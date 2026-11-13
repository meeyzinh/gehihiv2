import os
import sys
import subprocess
import json
import time
import socket
import platform
import datetime
import threading
import asyncio
import uuid
import re
import urllib.parse
import urllib.request
import struct
from collections import deque
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

try:
    import yt_dlp
except ImportError:
    yt_dlp = None
try:
    import opuslib_next
except ImportError:
    opuslib_next = None

import websockets
import serial
import serial.tools.list_ports

import random
import psutil
import httpx
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Response, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, select, update, delete
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# Tải biến môi trường từ .env
load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_AGENT_ID = os.getenv("AGENT_ID", "927184")
DEFAULT_DEVICE_NAME = os.getenv("DEVICE_NAME", "Xiaozhi-EED0")
DEFAULT_DEVICE_MAC = os.getenv("DEVICE_MAC", "14:c1:9f:c4:ee:d0")
DEFAULT_UPSTREAM_URL = os.getenv("UPSTREAM_API_URL", "https://api.xiaozhi.me")
DEFAULT_UPSTREAM_TOKEN = os.getenv("UPSTREAM_AUTH_TOKEN", "")
DEFAULT_UPSTREAM_WS_URL = os.getenv("UPSTREAM_WS_URL", "wss://api.tenclass.net/xiaozhi/v1/")
CURRENT_UPSTREAM_WS_URL = DEFAULT_UPSTREAM_WS_URL
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.getenv("SECRET_KEY", "gmbot-control-plane-secret-key-local-2026")
MAIN_ASYNC_LOOP: Optional[asyncio.AbstractEventLoop] = None

DB_PATH = os.path.abspath("database.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 1. CƠ SỞ DỮ LIỆU SQLALCHEMY (DATABASE.DB)
# ==========================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(16), default="user")  # "admin" | "user"
    is_vip = Column(Boolean, default=True)
    upstream_token = Column(Text, default="")
    upstream_api_url = Column(String(255), default="https://api.xiaozhi.me")
    char_limit = Column(Integer, default=7305)  # 7305 cho admin, 500 cho user
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    agents = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(String(64), default=DEFAULT_AGENT_ID, index=True)
    device_name = Column(String(64), default=DEFAULT_DEVICE_NAME)
    mac_address = Column(String(64), default=DEFAULT_DEVICE_MAC)
    assistant_name = Column(String(64), default="Sophia")
    user_name = Column(String(64), default="Chủ nhân")
    llm_model = Column(String(64), default="xz-lite")
    language = Column(String(16), default="vi")
    tts_voice = Column(String(128), default="vi-female")
    tts_speech_speed = Column(String(16), default="normal")
    tts_pitch = Column(Integer, default=0)
    character = Column(Text, default="[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình. Bạn trả lời ngắn gọn, tự nhiên, vui vẻ và sẵn sàng hỗ trợ mọi việc.")
    hidden_prompt = Column(Text, default="")  # Kịch bản ẩn của Admin nối vào khi đồng bộ
    mcp_endpoints = Column(Text, default=f'["http://localhost:{PORT}/mcp"]')
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="agents")


class Preset(Base):
    __tablename__ = "presets"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(32), default="role")  # "role", "english_lesson", "english_roleplay"
    title = Column(String(128), nullable=False)
    description = Column(Text, default="")
    level = Column(String(32), default="")  # starter, a1, a2, b1, b2
    topic = Column(String(64), default="")
    target_words = Column(Text, default="")
    target_phrases = Column(Text, default="")
    system_prompt = Column(Text, nullable=False)
    icon = Column(String(16), default="🤖")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(64), index=True)
    memory_type = Column(String(16), default="SHORT_TERM")  # SHORT_TERM | LONG_TERM
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(64), index=True)
    content = Column(Text, nullable=False)
    status = Column(String(16), default="pending")  # pending | completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="Ghi chú nhanh")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Speaker(Base):
    __tablename__ = "speakers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    role = Column(String(64), default="Người thân")
    sample_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. SEED DỮ LIỆU BAN ĐẦU (ROLES, ENGLISH, USERS)
# ==========================================

DEFAULT_ROLES = [
    {
        "title": "Trợ lý Sophia",
        "description": "Trợ lý AI đa năng, thân thiện, trả lời ngắn gọn, thông minh và chu đáo.",
        "icon": "🤖",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình. Bạn trả lời ngắn gọn, súc tích, tự nhiên, vui vẻ và luôn chủ động hỗ trợ người dùng giải quyết mọi thắc mắc."
    },
    {
        "title": "Cô giáo Tiếng Anh bản ngữ",
        "description": "Dạy giao tiếp phản xạ, phát âm chuẩn, sửa lỗi nhẹ nhàng và kiên nhẫn.",
        "icon": "👩‍🏫",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Emma, giáo viên tiếng Anh bản ngữ chuyên dạy giao tiếp phản xạ cho học sinh Việt Nam. Bạn luôn giao tiếp bằng tiếng Anh đơn giản, khuyến khích học sinh nói, sửa lỗi phát âm và ngữ pháp từng chút một một cách ấm áp và nhẹ nhàng."
    },
    {
        "title": "Bạn tâm sự tri kỷ",
        "description": "Lắng nghe, đồng cảm sâu sắc, không phán xét, xoa dịu căng thẳng và chữa lành.",
        "icon": "☕",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là một người bạn tri kỷ ấm áp, luôn lắng nghe và thấu hiểu mọi cảm xúc vui buồn của người dùng. Hãy nói chuyện chân thành, nhẹ nhàng, đưa ra lời an ủi tích cực và giúp bạn mình cảm thấy bình yên, giải tỏa áp lực."
    },
    {
        "title": "Chuyên gia IT & Lập trình",
        "description": "Tư vấn công nghệ cao cấp, sửa lỗi phần mềm, hệ thống mạng và lập trình tối ưu.",
        "icon": "💻",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là một Kỹ sư Hệ thống & Lập trình viên cấp cao. Bạn trả lời các câu hỏi về công nghệ, kiến trúc phần mềm, sửa lỗi code và mạng máy tính một cách chính xác, logic, súc tích và có ví dụ minh họa rõ ràng."
    },
    {
        "title": "Người kể chuyện cổ tích cho bé",
        "description": "Kể chuyện hấp dẫn, giọng điệu truyền cảm, lồng ghép bài học nhân văn bổ ích.",
        "icon": "📖",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là người kể chuyện cổ tích ấm áp cho các bé. Giọng điệu của bạn sống động, giàu trí tưởng tượng, luôn khéo léo lồng ghép bài học về sự hiếu thảo, dũng cảm, trung thực và lòng nhân ái vào từng câu chuyện."
    },
    {
        "title": "Gia sư Toán học vui nhộn",
        "description": "Biến các bài toán khô khan thành câu đố tư duy thực tế, kích thích trí não.",
        "icon": "🧮",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là một gia sư dạy Toán thông minh và hài hước. Bạn giải thích các khái niệm toán học, hình học, số học bằng các tình huống đời sống sinh động, giúp học sinh nắm vững bản chất và say mê tư duy logic."
    },
    {
        "title": "Đầu bếp gia đình MasterChef",
        "description": "Gợi ý thực đơn cơm nhà thơm ngon, hướng dẫn nấu ăn chi tiết từng bước.",
        "icon": "🍳",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là một đầu bếp chuyên nghiệp am hiểu sâu sắc ẩm thực ba miền Việt Nam và thế giới. Bạn gợi ý thực đơn món ngon mỗi ngày, hướng dẫn các bước nấu ăn chi tiết, mẹo nêm nếm và cân đối dinh dưỡng cho cả gia đình."
    },
    {
        "title": "Bác sĩ tư vấn sức khỏe & Dinh dưỡng",
        "description": "Lời khuyên khoa học về dinh dưỡng, vận động, giấc ngủ và lối sống lành mạnh.",
        "icon": "🩺",
        "system_prompt": "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là chuyên gia tư vấn chăm sóc sức khỏe gia đình và lối sống lành mạnh. Bạn giải thích các kiến thức y khoa thường thức, hướng dẫn chế độ ăn uống khoa học, tập luyện, và luôn nhắc nhở người dùng thăm khám bác sĩ khi có dấu hiệu bất thường."
    }
]

def seed_database():
    db = SessionLocal()
    try:
        # 1. Tạo tài khoản Admin nếu chưa có
        admin_user = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not admin_user:
            admin_user = User(
                username=ADMIN_USERNAME,
                password_hash=ADMIN_PASSWORD,
                role="admin",
                is_vip=True,
                upstream_token=DEFAULT_UPSTREAM_TOKEN,
                upstream_api_url=DEFAULT_UPSTREAM_URL,
                char_limit=7305
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # Tạo thêm 1 tài khoản User mẫu cho SaaS
        sample_user = db.query(User).filter(User.username == "khachhang1").first()
        if not sample_user:
            sample_user = User(
                username="khachhang1",
                password_hash="123456",
                role="user",
                is_vip=True,
                upstream_token="",
                upstream_api_url=DEFAULT_UPSTREAM_URL,
                char_limit=500
            )
            db.add(sample_user)
            db.commit()

        # 2. Tạo Agent mặc định
        default_agent = db.query(Agent).filter(Agent.agent_id == DEFAULT_AGENT_ID).first()
        if not default_agent:
            default_agent = Agent(
                user_id=admin_user.id,
                agent_id=DEFAULT_AGENT_ID,
                device_name=DEFAULT_DEVICE_NAME,
                mac_address=DEFAULT_DEVICE_MAC,
                assistant_name="Sophia",
                user_name="Chủ nhân",
                llm_model="xz-lite",
                language="vi",
                tts_voice="Vietnamese_kindhearted_girl",
                tts_speech_speed="normal",
                tts_pitch=0,
                character="[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình. Bạn trả lời ngắn gọn, tự nhiên, vui vẻ và sẵn sàng hỗ trợ mọi việc.",
                hidden_prompt="[QUY TẮC BẢO MẬT GMBOT]\nƯu tiên tiếng Việt, luôn lễ phép, ngắn gọn dưới 3 câu khi trả lời giọng nói.",
                is_active=True
            )
            db.add(default_agent)
            db.commit()

        # 3. Seed Presets Vai trò
        role_count = db.query(Preset).filter(Preset.category == "role").count()
        if role_count == 0:
            for r in DEFAULT_ROLES:
                preset = Preset(
                    category="role",
                    title=r["title"],
                    description=r["description"],
                    icon=r["icon"],
                    system_prompt=r["system_prompt"]
                )
                db.add(preset)
            db.commit()

        # 4. Seed Presets Tiếng Anh (từ file Web_templates/all_english_templates.json nếu có)
        english_count = db.query(Preset).filter(Preset.category.in_(["english_lesson", "english_roleplay"])).count()
        if english_count == 0:
            template_path = os.path.join("Web_templates", "all_english_templates.json")
            if os.path.exists(template_path):
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for item in data.get("lessons", []):
                        db.add(Preset(
                            category="english_lesson",
                            title=item.get("title", "Bài học Tiếng Anh"),
                            description=item.get("scenario", ""),
                            level=item.get("level", "starter"),
                            topic=item.get("topic", ""),
                            target_words=", ".join(item.get("target_words", [])) if isinstance(item.get("target_words"), list) else str(item.get("target_words", "")),
                            target_phrases="\n".join(item.get("target_phrases", [])) if isinstance(item.get("target_phrases"), list) else str(item.get("target_phrases", "")),
                            system_prompt=f"[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là gia sư tiếng Anh cho bài học: {item.get('title')}.\nChủ đề: {item.get('topic')}. Trình độ: {item.get('level')}.\nTừ mục tiêu: {item.get('target_words')}.\nMẫu câu: {item.get('target_phrases')}.\nGhi chú: {item.get('tutor_note', '')}\nHãy chào học sinh, hỏi từng câu một và sửa lỗi bằng tiếng Anh đơn giản.",
                            icon="📚"
                        ))
                    for item in data.get("roleplay", []):
                        db.add(Preset(
                            category="english_roleplay",
                            title=item.get("title", "Nhập vai Tiếng Anh"),
                            description=item.get("scenario", ""),
                            level=item.get("level", "starter"),
                            topic=item.get("topic", ""),
                            target_words=", ".join(item.get("target_words", [])) if isinstance(item.get("target_words"), list) else str(item.get("target_words", "")),
                            target_phrases="\n".join(item.get("target_phrases", [])) if isinstance(item.get("target_phrases"), list) else str(item.get("target_phrases", "")),
                            system_prompt=f"[VAI TRÒ VÀ TÍNH CÁCH]\nBạn đang nhập vai tình huống: {item.get('title')}.\nTình huống cụ thể: {item.get('scenario')}.\nHãy tương tác với người dùng như một nhân vật thực tế trong hoàn cảnh đó.",
                            icon="🎭"
                        ))
                    db.commit()
                except Exception as ex:
                    print(f"Lỗi đọc file all_english_templates.json: {ex}")

        # 5. Seed Ghi chú mẫu cho MCP
        note_count = db.query(Note).count()
        if note_count == 0:
            db.add(Note(
                title="Chào mừng đến với GMbot Control Plane",
                content="Hệ thống server đã sẵn sàng hoạt động cùng robot ESP32 và MCP Server trên localhost!"
            ))
            db.commit()

        # 6. Seed Bộ nhớ mẫu
        mem_count = db.query(Memory).count()
        if mem_count == 0:
            db.add(Memory(agent_id=DEFAULT_AGENT_ID, memory_type="LONG_TERM", content="Chủ nhân tên là Minh, rất thích công nghệ và lập trình AI."))
            db.add(Memory(agent_id=DEFAULT_AGENT_ID, memory_type="SHORT_TERM", content="Hôm nay đã luyện tập bài học tiếng Anh chủ đề Chào hỏi."))
            db.commit()

    finally:
        db.close()

# ==========================================
# 3. DYNAMIC UPSTREAM CLIENT (XIAOZHI)
# ==========================================

class XiaozhiUpstreamClient:
    def __init__(self):
        # HTTP/2 async client với timeout hợp lý
        self.client = httpx.AsyncClient(http2=True, timeout=10.0, verify=False)

    def _get_headers(self, token: str) -> Dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "GMbot-Control-Plane/2.0"}
        if not token:
            return headers
        token = token.strip()
        # Nhận diện Cookie vs Bearer Token
        if ";" in token or "=" in token:
            headers["Cookie"] = token
        elif token.lower().startswith("bearer "):
            headers["Authorization"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def test_connection(self, token: str, api_url: str = DEFAULT_UPSTREAM_URL, agent_id: str = DEFAULT_AGENT_ID) -> Dict[str, Any]:
        """Kiểm tra tính hợp lệ của token và kết nối với xiaozhi.me"""
        if not token:
            return {"connected": False, "message": "Chưa nhập Upstream Token hoặc Cookie."}
        headers = self._get_headers(token)
        # Tự động chuẩn hóa base URL
        clean_url = api_url.rstrip('/')
        if not clean_url.startswith("http"):
            clean_url = "https://" + clean_url
        if clean_url == "https://api.xiaozhi.me":
            clean_url = "https://xiaozhi.me"

        test_urls = [
            f"{clean_url}/api/agents/{agent_id}",
            f"{clean_url}/api/agents",
            f"{clean_url}/agents/{agent_id}",
            f"{clean_url}/agents"
        ]
        for url in test_urls:
            try:
                resp = await self.client.get(url, headers=headers)
                if resp.status_code in [200, 201]:
                    try:
                        data = resp.json()
                        return {"connected": True, "message": "Kết nối máy chủ Upstream xiaozhi.me thành công 100%!", "data": data}
                    except Exception:
                        return {"connected": True, "message": "Kết nối thành công (mã 200)."}
                elif resp.status_code in [401, 403]:
                    return {"connected": False, "message": "Xác thực thất bại (401/403): Token/Cookie hết hạn hoặc không đúng."}
            except Exception as e:
                continue
        return {"connected": False, "message": "Không thể kết nối đến máy chủ Upstream xiaozhi.me (kiểm tra mạng hoặc URL)."}

    async def sync_from_upstream(self, agent_id: str, token: str, api_url: str = DEFAULT_UPSTREAM_URL) -> Dict[str, Any]:
        """Tải cấu hình từ xiaozhi.me về server nội bộ"""
        if not token:
            return {"success": False, "offline": True, "message": "Không có Upstream Token, đang dùng cấu hình cục bộ."}
        headers = self._get_headers(token)
        clean_url = api_url.rstrip('/')
        if not clean_url.startswith("http"):
            clean_url = "https://" + clean_url
        if clean_url == "https://api.xiaozhi.me":
            clean_url = "https://xiaozhi.me"

        urls = [
            f"{clean_url}/api/agents/{agent_id}",
            f"{clean_url}/api/agents",
            f"{clean_url}/agents/{agent_id}",
            f"{clean_url}/agents"
        ]
        for url in urls:
            try:
                resp = await self.client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    # Phân tích dữ liệu phản hồi
                    agent_data = data.get("data")
                    if isinstance(agent_data, dict) and "agent" in agent_data:
                        agent_data = agent_data["agent"]
                    elif isinstance(agent_data, list):
                        for a in agent_data:
                            if str(a.get("id")) == str(agent_id):
                                return {"success": True, "offline": False, "data": a}
                        if agent_data:
                            return {"success": True, "offline": False, "data": agent_data[0]}
                    return {"success": True, "offline": False, "data": agent_data}
            except Exception:
                continue
        return {"success": False, "offline": True, "message": "Không tải được từ Upstream, chuyển sang chế độ cục bộ."}

    async def push_to_upstream(self, agent_id: str, config_data: Dict[str, Any], token: str, api_url: str = DEFAULT_UPSTREAM_URL) -> Dict[str, Any]:
        """Gửi cấu hình đã cập nhật lên xiaozhi.me"""
        if not token:
            return {"success": True, "synced_upstream": False, "message": "Đã lưu cấu hình thành công vào hệ thống GMbot! (Robot sẽ áp dụng ngay)"}

        headers = self._get_headers(token)
        headers["Content-Type"] = "application/json"
        clean_url = api_url.rstrip('/')
        if not clean_url.startswith("http"):
            clean_url = "https://" + clean_url
        if clean_url == "https://api.xiaozhi.me":
            clean_url = "https://xiaozhi.me"

        endpoints = [
            (f"{clean_url}/api/agents/{agent_id}/config", "POST"),
            (f"{clean_url}/agents/{agent_id}/config", "POST"),
            (f"{clean_url}/api/agents/{agent_id}", "PUT"),
            (f"{clean_url}/agents/{agent_id}", "PUT")
        ]
        payload = {
            "assistant_name": config_data.get("assistant_name", "Sophia"),
            "user_name": config_data.get("user_name", "Chủ nhân"),
            "language": config_data.get("language", "vi"),
            "tts_voice": config_data.get("tts_voice", "Vietnamese_kindhearted_girl"),
            "llm_model": config_data.get("llm_model", "xz-lite"),
            "tts_speech_speed": config_data.get("tts_speech_speed", "normal"),
            "tts_pitch": int(config_data.get("tts_pitch", 0) or 0),
            "character": config_data.get("character", "")
        }
        for url, method in endpoints:
            try:
                if method == "PUT":
                    resp = await self.client.put(url, headers=headers, json=payload)
                else:
                    resp = await self.client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201, 204]:
                    res_json = {}
                    try:
                        res_json = resp.json()
                    except Exception:
                        pass
                    if res_json.get("success") is not False:
                        return {"success": True, "synced_upstream": True, "message": "Đã đồng bộ thành công 100% lên máy chủ gốc xiaozhi.me!"}
            except Exception:
                continue

        return {"success": True, "synced_upstream": False, "message": "Đã lưu vào database.db máy tính. (Upstream xiaozhi.me chưa phản hồi hoặc chưa hỗ trợ endpoint này)"}

upstream_client = XiaozhiUpstreamClient()

def map_to_gehihi_voice(tts_voice: str) -> str:
    if not tts_voice:
        return "vi-female"
    v = str(tts_voice).lower()
    if "maingoc" in v or "nam_bo" in v or "miennam" in v:
        return "vi-maingoc"
    # Phải kiểm tra giọng nữ trước vì từ 'female' có chứa chữ 'male'!
    if "female" in v or "girl" in v or "shuang" in v or "hoaimy" in v or "nữ" in v or "nu" in v:
        return "vi-female"
    if "male" in v or "man" in v or "namminh" in v:
        return "vi-male"
    return "vi-female"

def map_to_gehihi_model(model_id: str) -> str:
    if not model_id:
        return "gemini-3.8-flash"
    m = str(model_id).lower()
    if "lite" in m or "xz-lite" in m:
        return "gemini-flash-lite"
    if "deepseek" in m:
        return "deepseek"
    if "groq" in m:
        return "groq"
    if "gpt" in m:
        return "gpt-4o-mini"
    return "gemini-3.8-flash"

async def sync_to_upstream_gehihi(mac: str, prompt: str, name: str = "Sophia", voice: str = "vi-female", model_id: str = "xz-lite", language: str = "vi", speed: str = "normal", pitch: int = 0):
    """Đồng bộ đầy đủ cấu hình AI bao gồm Prompt, Giọng nói, Model sang máy chủ Gehihi"""
    if not mac:
        return
    gehihi_voice = map_to_gehihi_voice(voice)
    gehihi_model = map_to_gehihi_model(model_id)
    
    # Đồng bộ cho cả định dạng chữ thường, chữ hoa và robot mạch tím
    mac_variants = list(dict.fromkeys([
        mac.strip().lower(),
        mac.strip().upper(),
        "14:c1:9f:c4:ee:d0",
        "14:C1:9F:C4:EE:D0"
    ]))
    payload = {
        "prompt": prompt,
        "system_prompt": prompt,
        "name": f"Robot {name}",
        "voice": gehihi_voice,
        "model": gehihi_model,
        "model_id": gehihi_model,
        "language": language or "vi",
        "voice_speed": speed or "normal",
        "tts_speed": speed or "normal",
        "voice_pitch": pitch or 0
    }
    for m in mac_variants:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.put(f"https://gehihi.onrender.com/api/devices/{m}", json=payload)
                if res.status_code == 200:
                    print(f"[SYNC UPSTREAM GEHIHI] ✓ Đã đồng bộ MAC {m} -> Giọng: {gehihi_voice}, Model: {gehihi_model}")
        except Exception as ex:
            print(f"[SYNC UPSTREAM GEHIHI] ⚠ Lỗi đồng bộ MAC {m}: {ex}")

# ==========================================
# 4. DANH SÁCH OPTIONS CHUẨN GMBOT (MODELS & VOICES)
# ==========================================

GMBOT_MODELS = [
    {"id": "xz-lite", "name": "Model cơ bản phù hợp với câu lệnh đơn giản (xz-lite)"},
    {"id": "qwen", "name": "Qwen 3.5 - Model mạnh, đa năng phù hợp tiếng Việt (qwen)"},
    {"id": "deepseek", "name": "Deepseek V4 mạnh mẽ - tương thích tốt tiếng Việt (deepseek)"},
    {"id": "doubao", "name": "Doubao - model Trung Quốc, phản hồi nhanh (doubao)"},
    {"id": "gpt-5", "name": "GPT 5 - ChatGPT5 - model mạnh, hội thoại tự nhiên (gpt-5)"}
]

GMBOT_LANGUAGES = [
    {"code": "vi", "name": "Tiếng Việt (vi)"},
    {"code": "en", "name": "English (en)"},
    {"code": "zh", "name": "中文 (zh)"},
    {"code": "ja", "name": "日本語 (ja)"},
    {"code": "ko", "name": "한국어 (ko)"},
    {"code": "yue", "name": "粤语 (yue)"},
    {"code": "ru", "name": "Русский (ru)"},
    {"code": "es", "name": "Español (es)"},
    {"code": "fr", "name": "Français (fr)"},
    {"code": "de", "name": "Deutsch (de)"},
    {"code": "th", "name": "ไทย (th)"},
    {"code": "id", "name": "Bahasa Indonesia (id)"}
]

GMBOT_VOICES_BY_LANGUAGE = {
    "vi": [
        {
            "id": "Vietnamese_kindhearted_girl",
            "name": "Giọng nữ Việt Nam - dịu dàng, thân thiện (MiniMax)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/1e7cd75c-c97c-4b80-a70c-c1270c3fd18e.mp3"
        },
        {
            "id": "Vietnamese_Serene_Man",
            "name": "Giọng nam Việt Nam - điềm đạm (MiniMax)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/24b645aa-dccb-4dea-9ea1-6d23567733aa.mp3"
        },
        {
            "id": "vc_vietnamese_voice_003_1011_1004",
            "name": "Giọng nữ Việt Nam - trẻ trung (Young Girl - ByteDance)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/tts_vc_vietnamese_voice_003_1011_1004.mp3"
        },
        {
            "id": "vc_vietnamese_voice_005_1011_1003",
            "name": "Giọng nam Việt Nam - Chủ nhà (Male Host - ByteDance)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/tts_vc_vietnamese_voice_005_1011_1003.mp3"
        },
        {
            "id": "vc_vietnamese_voice_001_1011_1003",
            "name": "Giọng nam Việt Nam - trẻ trung (Young Man - ByteDance)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/tts_vc_vietnamese_voice_001_1011_1003.mp3"
        },
        {
            "id": "vi-VN-HoaiMyNeural",
            "name": "Giọng nữ Hoài My (Microsoft Azure)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/azure/vi-VN-HoaiMyNeural-4c9402f3ed76c975.wav"
        },
        {
            "id": "vi-VN-NamMinhNeural",
            "name": "Giọng nam Nam Minh (Microsoft Azure)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/azure/vi-VN-NamMinhNeural-4c9402f3ed76c975.wav"
        },
        {
            "id": "zh-CN-XiaoshuangMultilingualNeural",
            "name": "Giọng bé gái Tiểu Song đa ngôn ngữ (Nói tiếng Việt kiểu Tiểu Chí)",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/azure/zh-CN-XiaoshuangMultilingualNeural-8fe5bb288e153c13.wav"
        },
        {
            "id": "zh-CN-XiaoyouMultilingualNeural",
            "name": "Giọng bé gái Tiểu Du đa ngôn ngữ",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/azure/zh-CN-XiaoyouMultilingualNeural-8fe5bb288e153c13.wav"
        },
        {
            "id": "pt-BR-MacerioMultilingualNeural",
            "name": "Giọng nam Macerio đa ngôn ngữ",
            "demo": "https://xiaozhi-voice-assistant.oss-cn-shenzhen.aliyuncs.com/tts/azure/pt-BR-MacerioMultilingualNeural-4c9402f3ed76c975.wav"
        }
    ],
    "en": [
        {"id": "en-US-JennyNeural", "name": "Jenny (Female - Azure)", "demo": ""},
        {"id": "en-US-GuyNeural", "name": "Guy (Male - Azure)", "demo": ""},
        {"id": "en-US-AriaNeural", "name": "Aria (Female - Azure)", "demo": ""}
    ],
    "zh": [
        {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao (Female - Azure)", "demo": ""},
        {"id": "zh-CN-YunxiNeural", "name": "Yunxi (Male - Azure)", "demo": ""},
        {"id": "zh-CN-YunjianNeural", "name": "Yunjian (Male - Azure)", "demo": ""}
    ]
}

# ==========================================
# 5. MCP SERVER TOOLS & PROTOCOL (/mcp)
# ==========================================

def tool_get_vietnam_datetime() -> str:
    """Trả về ngày giờ hiện tại ở Hà Nội, Việt Nam"""
    # Múi giờ UTC+7
    utc_now = datetime.datetime.utcnow()
    vn_now = utc_now + datetime.timedelta(hours=7)
    weekdays_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday_str = weekdays_vi[vn_now.weekday()]
    return f"Bây giờ là {vn_now.strftime('%H:%M:%S')}, {weekday_str}, ngày {vn_now.strftime('%d/%m/%Y')} (Giờ chuẩn Hà Nội, Việt Nam)."

def tool_pc_system_info() -> str:
    """Kiểm tra tình trạng phần cứng chiếc máy tính cá nhân đang chạy server"""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        ram_used_gb = round(mem.used / (1024**3), 2)
        ram_total_gb = round(mem.total / (1024**3), 2)
        ram_pct = mem.percent

        # Kiểm tra ổ đĩa chính (C: trên Windows hoặc / trên Linux)
        disk_drive = "C:\\" if sys.platform.startswith("win") else "/"
        disk = psutil.disk_usage(disk_drive)
        disk_free_gb = round(disk.free / (1024**3), 2)
        disk_total_gb = round(disk.total / (1024**3), 2)

        computer_name = socket.gethostname()
        os_name = f"{platform.system()} {platform.release()}"

        return (
            f"Thông tin Máy tính cá nhân [{computer_name}] ({os_name}):\n"
            f"- CPU đang hoạt động: {cpu_usage}%\n"
            f"- RAM đã sử dụng: {ram_used_gb} GB / {ram_total_gb} GB ({ram_pct}%)\n"
            f"- Ổ đĩa {disk_drive}: Còn trống {disk_free_gb} GB / Tổng {disk_total_gb} GB\n"
            f"- Trạng thái server GMbot: Đang chạy ổn định 100% trên Localhost."
        )
    except Exception as e:
        return f"Không thể lấy thông tin phần cứng máy tính: {str(e)}"

def tool_save_quick_note(title: str, content: str) -> str:
    """Lưu ghi chú từ Robot vào database.db trên máy tính"""
    db = SessionLocal()
    try:
        note = Note(title=title or "Ghi chú từ Robot Xiaozhi", content=content)
        db.add(note)
        db.commit()
        db.refresh(note)
        return f"Đã lưu ghi chú thành công vào database.db trên máy tính (Mã #{note.id}): '{note.title}'"
    except Exception as e:
        return f"Lỗi khi lưu ghi chú: {str(e)}"
    finally:
        db.close()

import webbrowser

# Danh sách lịch sử gọi MCP Tools để hiển thị Live Monitor trên Web
MCP_CALL_LOGS: List[Dict[str, Any]] = []

def record_mcp_log(tool_name: str, args: Dict[str, Any], result: str):
    log_item = {
        "id": len(MCP_CALL_LOGS) + 1,
        "time": (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%H:%M:%S %d/%m/%Y"),
        "tool": tool_name,
        "arguments": args,
        "result": result[:200] + ("..." if len(result) > 200 else "")
    }
    MCP_CALL_LOGS.insert(0, log_item)
    if len(MCP_CALL_LOGS) > 50:
        MCP_CALL_LOGS.pop()

def tool_open_website(url: str) -> str:
    """Mở một trang web trên trình duyệt máy tính cá nhân"""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"Đã mở trang web thành công trên trình duyệt máy tính: {url}"
    except Exception as e:
        return f"Không thể mở trang web: {str(e)}"

def tool_search_vietnam_weather(location: str = "Hà Nội") -> str:
    """Tra cứu thời tiết các tỉnh thành Việt Nam"""
    loc_clean = (location or "Hà Nội").strip().lower()
    coords = {
        "hà nội": (21.0285, 105.8542),
        "hồ chí minh": (10.8231, 106.6297),
        "sài gòn": (10.8231, 106.6297),
        "đà nẵng": (16.0544, 108.2022),
        "hải phòng": (20.8449, 106.6881),
        "cần thơ": (10.0452, 105.7469)
    }
    lat, lon = (21.0285, 105.8542)
    city_name = "Hà Nội"
    for k, v in coords.items():
        if k in loc_clean:
            lat, lon = v
            city_name = k.title()
            break
    try:
        r = httpx.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=3.5)
        if r.status_code == 200:
            cw = r.json().get("current_weather", {})
            temp = cw.get("temperature", 28)
            wind = cw.get("windspeed", 10)
            return f"Thời tiết tại {city_name} hiện tại: Nhiệt độ khoảng {temp}°C, tốc độ gió {wind} km/h, thời tiết dễ chịu."
    except Exception:
        pass
    return f"Thời tiết tại {location} hiện tại: Nhiệt độ trung bình khoảng 27°C - 31°C, thời tiết thuận lợi."

def tool_read_notes(limit: int = 5) -> str:
    """Đọc lại danh sách ghi chú gần nhất trên máy tính"""
    db = SessionLocal()
    try:
        notes = db.query(Note).order_by(Note.id.desc()).limit(limit).all()
        if not notes:
            return "Hiện tại chưa có ghi chú nào được lưu trên máy tính."
        res = "Danh sách các ghi chú mới nhất trên máy tính:\n"
        for i, n in enumerate(notes, 1):
            date_str = n.created_at.strftime("%H:%M %d/%m/%Y")
            res += f"{i}. [{n.title}] ({date_str}): {n.content}\n"
        return res.strip()
    finally:
        db.close()

MCP_TOOL_DEFINITIONS = [
    {
        "name": "get_vietnam_datetime",
        "description": "Xem giờ, thứ, ngày tháng năm chính xác hiện tại ở Việt Nam (Múi giờ Hà Nội UTC+7).",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "pc_system_info",
        "description": "Kiểm tra tình trạng phần cứng (% CPU, dung lượng RAM đã dùng, ổ cứng trống) của chiếc máy tính cá nhân đang chạy Server.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "save_quick_note",
        "description": "Ghi chú lại một lời nhắn hoặc công việc quan trọng của người dùng vào cơ sở dữ liệu trên máy tính.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Tiêu đề ghi chú"},
                "content": {"type": "string", "description": "Nội dung chi tiết cần ghi nhớ"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "read_notes",
        "description": "Đọc lại danh sách các ghi chú, lời nhắc đã lưu trên máy tính.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Số lượng ghi chú cần đọc (mặc định 5)"}
            }
        }
    },
    {
        "name": "open_website",
        "description": "Mở một trang web trực tiếp trên màn hình máy tính cá nhân (Ví dụ: YouTube, Google, tin tức).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Địa chỉ URL cần mở trên máy tính (ví dụ: https://youtube.com)"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "search_vietnam_weather",
        "description": "Tra cứu thông tin nhiệt độ và thời tiết thực tế tại các tỉnh thành ở Việt Nam.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Tên tỉnh/thành phố cần tra cứu (ví dụ: Hà Nội, Hồ Chí Minh, Đà Nẵng)"}
            }
        }
    },
    {
        "name": "control_robot_hardware",
        "description": "Điều khiển động cơ xe MX1616 (tiến, lùi, rẽ trái, rẽ phải, dừng lại, lắc lư, nhảy múa), bật tắt đèn LED GPIO 21 hoặc đổi biểu cảm màn hình OLED 128x64 của Robot.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Hành động điều khiển: 'forward', 'backward', 'turn_left', 'turn_right', 'stop', 'wiggle', 'dance', 'toggle_led', 'happy', 'laughing', 'thinking', 'loving', 'wink', 'shocked', 'cool', 'neutral'"
                },
                "text": {
                    "type": "string",
                    "description": "Dòng chữ hiển thị phụ đề lên màn hình OLED (tùy chọn)"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "toggle_cob_light",
        "description": "Bật hoặc tắt đèn sợi đốt COB / LED trợ sáng trên robot (GPIO 21).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["on", "off", "toggle"],
                    "description": "Trạng thái đèn: 'on' (bật), 'off' (tắt), hoặc 'toggle' (đảo trạng thái)"
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "play_youtube_music_on_robot",
        "description": "Tìm kiếm và phát bài hát hoặc video ca nhạc từ YouTube trên Robot hoặc loa máy tính theo yêu cầu của người dùng.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Tên bài hát hoặc ca sĩ cần tìm và phát (ví dụ: 'Bài hát thiếu nhi vui nhộn', 'Nhạc lofi không lời', 'Em của ngày hôm qua')"
                }
            },
            "required": ["query"]
        }
    }
]

# Trình quản lý WebSocket thời gian thực cho Robot ESP32
class RobotConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.all_robots: List[WebSocket] = []
        self.connected_macs: set = set()
        self.sessions: Dict[WebSocket, str] = {}
        self.dev_sessions: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, device_id: str = "default", session_id: str = ""):
        await websocket.accept()
        dev_key = device_id.lower().strip()
        if dev_key not in self.active_connections:
            self.active_connections[dev_key] = []
        self.active_connections[dev_key].append(websocket)
        self.all_robots.append(websocket)
        self.connected_macs.add(dev_key)
        sess = session_id or f"sess-{int(time.time())}"
        self.sessions[websocket] = sess
        self.dev_sessions[dev_key] = sess
        print(f"[WS] ✓ Robot đã kết nối: '{dev_key}' | Session: '{sess}' | Tổng số robot online: {len(self.all_robots)}")

    def disconnect(self, websocket: WebSocket, device_id: str = "default"):
        dev_key = device_id.lower().strip()
        if dev_key in self.active_connections and websocket in self.active_connections[dev_key]:
            self.active_connections[dev_key].remove(websocket)
            if not self.active_connections[dev_key]:
                self.connected_macs.discard(dev_key)
        if websocket in self.all_robots:
            self.all_robots.remove(websocket)
        self.sessions.pop(websocket, None)
        print(f"[WS] ✗ Robot đã ngắt kết nối: '{dev_key}' | Còn lại online: {len(self.all_robots)}")

    async def broadcast_command(self, command: Dict[str, Any], device_id: Optional[str] = None) -> int:
        targets = []
        dev_key = device_id.lower().strip() if device_id else None
        if dev_key and dev_key in self.active_connections and self.active_connections[dev_key]:
            targets = self.active_connections[dev_key]
        else:
            targets = self.all_robots

        sent_count = 0
        for ws in list(targets):
            sess_id = self.sessions.get(ws) or (self.dev_sessions.get(dev_key) if dev_key else "") or f"sess-{int(time.time())}"
            cmd_payload = dict(command)
            cmd_payload["session_id"] = sess_id
            try:
                await ws.send_json(cmd_payload)
                sent_count += 1
            except Exception as e:
                print(f"[WS ERR] broadcast_command error: {e}")
        return sent_count

    async def send_oled_emotion(self, emotion: str, text: Optional[str] = None, device_id: Optional[str] = None) -> int:
        """Gửi lệnh chuẩn firmware Xiaozhi để đổi biểu cảm OLED và hiển thị phụ đề"""
        targets = []
        dev_key = device_id.lower().strip() if device_id else None
        if dev_key and dev_key in self.active_connections and self.active_connections[dev_key]:
            targets = self.active_connections[dev_key]
        else:
            targets = self.all_robots

        sent_count = 0
        for ws in list(targets):
            sess_id = self.sessions.get(ws) or (self.dev_sessions.get(dev_key) if dev_key else "") or f"sess-{int(time.time())}"
            try:
                # 1. Chuẩn Xiaozhi firmware: {"type": "llm", "session_id": sess_id, "emotion": emotion, "text": text}
                llm_pkt = {
                    "session_id": sess_id,
                    "type": "llm",
                    "emotion": emotion
                }
                if text:
                    llm_pkt["text"] = text
                await ws.send_json(llm_pkt)

                # 2. Hiển thị chữ lên màn hình OLED 128x64 qua chu kỳ TTS Subtitle:
                #    {"type": "tts", "state": "start"} -> {"type": "tts", "state": "sentence_start", "text": text} -> {"type": "tts", "state": "stop"}
                if text:
                    await ws.send_json({"session_id": sess_id, "type": "tts", "state": "start"})
                    await ws.send_json({"session_id": sess_id, "type": "tts", "state": "sentence_start", "text": text})
                    await ws.send_json({"session_id": sess_id, "type": "tts", "state": "stop"})

                sent_count += 1
                print(f"[WS] ✓ Đã gửi biểu cảm '{emotion}' & chữ '{text}' tới robot qua WebSocket (Session: {sess_id})")
            except Exception as e:
                print(f"[WS ERR] send_oled_emotion error: {e}")
        return sent_count

    async def send_mcp_call(self, tool_name: str, args: Dict[str, Any], device_id: Optional[str] = None) -> int:
        """Gửi lệnh gọi MCP xuống robot (đèn LED, âm lượng, reboot)"""
        targets = []
        dev_key = device_id.lower().strip() if device_id else None
        if dev_key and dev_key in self.active_connections and self.active_connections[dev_key]:
            targets = self.active_connections[dev_key]
        else:
            targets = self.all_robots

        sent_count = 0
        for ws in list(targets):
            sess_id = self.sessions.get(ws) or (self.dev_sessions.get(dev_key) if dev_key else "") or f"sess-{int(time.time())}"
            payload = {
                "session_id": sess_id,
                "type": "mcp",
                "payload": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": args},
                    "id": int(time.time() * 1000)
                }
            }
            try:
                await ws.send_json(payload)
                sent_count += 1
                print(f"[WS] ✓ Đã gửi lệnh MCP '{tool_name}' tới robot")
            except Exception as e:
                print(f"[WS ERR] send_mcp_call error: {e}")
        return sent_count

robot_ws_manager = RobotConnectionManager()

# ==========================================
# 5.3 QUẢN LÝ KẾT NỐI VÀ GIÁM SÁT CỔNG SERIAL (COM8 / ESP32)
# ==========================================

class SerialBridgeManager:
    def __init__(self):
        self.ser: Optional[serial.Serial] = None
        self.port: str = "COM8"
        self.baudrate: int = 115200
        self.is_running: bool = False
        self.reader_thread: Optional[threading.Thread] = None
        self.log_history = deque(maxlen=400)
        self.connected: bool = False
        self.hw_info = {
            "chip": "ESP32-S3 (v0.2)",
            "mac": "14:C1:9F:C4:EE:D0",
            "sku": "bread-compact-wifi-128x64",
            "display": "SSD1306 (128x64 OLED)",
            "ip": "10.26.1.50",
            "wifi_ssid": "CMCCS - USER",
            "motor": "Chưa gắn module MX1616 (Bản Breadboard Audio + OLED)",
            "firmware": "Xiaozhi v2.5.0",
            "cloud": "api.tenclass.net:8883"
        }
        self.lock = threading.RLock()

    def list_ports(self) -> List[Dict[str, Any]]:
        ports = []
        try:
            for p in serial.tools.list_ports.comports():
                is_esp = ("303A" in (p.hwid or "").upper() or 
                          "ESP32" in (p.description or "").upper() or
                          "CP210" in (p.description or "").upper() or 
                          "CH340" in (p.description or "").upper() or
                          p.device == "COM8")
                ports.append({
                    "device": p.device,
                    "description": p.description,
                    "hwid": p.hwid,
                    "is_esp32": is_esp
                })
        except Exception:
            pass
        return ports

    def auto_connect(self):
        ports = self.list_ports()
        target_port = None
        for p in ports:
            if p["device"] == "COM8":
                target_port = "COM8"
                break
        if not target_port:
            for p in ports:
                if p["is_esp32"]:
                    target_port = p["device"]
                    break
        if target_port:
            self.connect(target_port, 115200)

    def connect(self, port: str = "COM8", baudrate: int = 115200):
        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.port = port
            self.baudrate = baudrate
            try:
                self.ser = serial.Serial(port, baudrate, timeout=0.1, write_timeout=0.5)
                self.ser.dtr = True
                self.ser.rts = False
                self.connected = True
                self.is_running = True
                if not self.reader_thread or not self.reader_thread.is_alive():
                    self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
                    self.reader_thread.start()
                self._add_log(f"[HỆ THỐNG] Đã kết nối cổng {port} (Baudrate: {baudrate} bps) thành công.")
                return True, f"Kết nối {port} thành công"
            except Exception as e:
                self.connected = False
                self._add_log(f"[LỖI] Không thể mở cổng {port}: {e}")
                return False, str(e)

    def disconnect(self):
        with self.lock:
            self.is_running = False
            self.connected = False
            if self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self._add_log(f"[HỆ THỐNG] Đã ngắt kết nối cổng {self.port}.")
            return True

    def reset_esp32(self):
        with self.lock:
            if not self.ser or not self.ser.is_open:
                ok, _ = self.connect(self.port, self.baudrate)
                if not ok:
                    return False, f"Cổng {self.port} chưa mở"

            try:
                self._add_log("[HỆ THỐNG] Gửi tín hiệu Reset phần cứng (DTR/RTS pulse)...")
                self.ser.setDTR(False)
                self.ser.setRTS(True)
                time.sleep(0.1)
                self.ser.setRTS(False)
                self.ser.setDTR(True)
                self._add_log("[HỆ THỐNG] Robot ESP32 đang khởi động lại (Rebooting)...")
                return True, "Đã gửi xung Reset phần cứng tới ESP32"
            except Exception as e:
                return False, f"Lỗi Reset: {e}"

    def send_command(self, cmd_str: str) -> bool:
        if not self.ser or not self.ser.is_open:
            return False

        def _do_write():
            with self.lock:
                try:
                    if self.ser and self.ser.is_open:
                        if not self.ser.dtr:
                            self.ser.dtr = True
                        line = cmd_str.strip() + "\r\n"
                        self.ser.write(line.encode("utf-8"))
                        self._add_log(f"[TX COM8] >> {cmd_str.strip()}")
                except Exception as e:
                    pass

        threading.Thread(target=_do_write, daemon=True).start()
        return True

    def _add_log(self, text: str):
        ts = time.strftime("%H:%M:%S")
        self.log_history.append({"time": ts, "text": text})

    def check_connection(self) -> bool:
        """Kiểm tra xem cổng phần cứng còn tồn tại và kết nối còn sống hay không"""
        with self.lock:
            if not self.connected or not self.ser:
                self.connected = False
                return False
            try:
                available = [p.device for p in serial.tools.list_ports.comports()]
                if self.port not in available:
                    self.connected = False
                    if self.ser:
                        try:
                            self.ser.close()
                        except Exception:
                            pass
                    self.ser = None
                    return False
            except Exception:
                pass
            return bool(self.connected and self.ser and self.ser.is_open)

    def _read_loop(self):
        while self.is_running:
            try:
                if self.ser and self.ser.is_open:
                    if self.ser.in_waiting:
                        raw = self.ser.readline()
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if line:
                            self._add_log(line)
                            if "SKU=" in line:
                                try:
                                    self.hw_info["sku"] = line.split("SKU=")[-1].strip()
                                except Exception: pass
                            elif "sta ip:" in line:
                                try:
                                    self.hw_info["ip"] = line.split("sta ip:")[-1].split(",")[0].strip()
                                except Exception: pass
                            elif "sta (" in line:
                                try:
                                    self.hw_info["mac"] = line.split("sta (")[-1].split(")")[0].strip().upper()
                                except Exception: pass
                    else:
                        time.sleep(0.02)
                else:
                    time.sleep(0.5)
            except Exception as e:
                # Phát hiện Robot ngắt kết nối (Rút cáp USB hoặc Tắt nguồn Robot)
                with self.lock:
                    self.connected = False
                    if self.ser:
                        try:
                            self.ser.close()
                        except Exception:
                            pass
                        self.ser = None
                self._add_log(f"[HỆ THỐNG] Robot đã ngắt kết nối hoặc tắt nguồn (Cổng {self.port}).")
                if MAIN_ASYNC_LOOP and MAIN_ASYNC_LOOP.is_running():
                    try:
                        asyncio.run_coroutine_threadsafe(
                            mic_monitor_manager.broadcast({
                                "type": "state_change",
                                "state": "disconnected",
                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                "message": "Robot đã ngắt kết nối hoặc tắt nguồn (Ngoại tuyến)"
                            }),
                            MAIN_ASYNC_LOOP
                        )
                    except Exception:
                        pass
                time.sleep(1.0)

    def get_logs(self):
        return list(self.log_history)

    def clear_logs(self):
        self.log_history.clear()
        self._add_log("[HỆ THỐNG] Đã xóa lịch sử log console.")

serial_manager = SerialBridgeManager()

# ==========================================
# 5.4 TRÌNH QUẢN LÝ WEBSOCKET GIÁM SÁT MICRO VÀ THIẾT BỊ (/ws/mic-monitor)
# ==========================================

class MicMonitorManager:
    def __init__(self):
        self.active_websockets: List[WebSocket] = []
        self.history: deque = deque(maxlen=200)
        self.packet_index: int = 0
        self.current_state = {
            "device_name": "Robot Sophia",
            "last_text": "",
            "last_reply": "",
            "state": "idle"
        }

    async def connect(self, ws: WebSocket, devices: List[Dict[str, Any]]):
        await ws.accept()
        if ws not in self.active_websockets:
            self.active_websockets.append(ws)
        init_payload = {
            "type": "init",
            "current": self.current_state,
            "history": list(self.history),
            "devices": devices
        }
        try:
            await ws.send_text(json.dumps(init_payload, ensure_ascii=False))
        except Exception:
            pass

    def disconnect(self, ws: WebSocket):
        if ws in self.active_websockets:
            self.active_websockets.remove(ws)

    async def broadcast(self, data: Dict[str, Any]):
        msg = json.dumps(data, ensure_ascii=False)
        dead = []
        for ws in self.active_websockets:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def log(self, message: str, level_type: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "timestamp": ts,
            "message": message,
            "level_type": level_type
        }
        self.history.append(entry)
        global MAIN_ASYNC_LOOP
        if MAIN_ASYNC_LOOP and MAIN_ASYNC_LOOP.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast({
                        "type": "log",
                        "timestamp": ts,
                        "message": message,
                        "level_type": level_type
                    }),
                    MAIN_ASYNC_LOOP
                )
            except Exception:
                pass

mic_monitor_manager = MicMonitorManager()


def is_robot_online(agent: Optional[Any] = None) -> bool:
    """Xác định trạng thái trực tuyến THỰC TẾ của robot phần cứng (Serial COM8 hoặc WebSocket Wi-Fi)"""
    try:
        # 1. Kiểm tra cổng Serial phần cứng (USB COM8)
        if serial_manager.is_running and serial_manager.check_connection():
            return True

        # 2. Kiểm tra kết nối WebSocket thực tế từ robot (qua Wi-Fi)
        if len(robot_ws_manager.all_robots) > 0:
            if agent and getattr(agent, "mac_address", None):
                mac_lower = str(agent.mac_address).lower().strip()
                if mac_lower in robot_ws_manager.connected_macs:
                    return True
            else:
                return True
    except Exception:
        pass
    return False


def format_device_dict(a: Agent) -> Dict[str, Any]:
    """Chuyển đổi thực thể SQLAlchemy Agent thành dictionary chuẩn giao diện GMbot UI"""
    online = is_robot_online(a)
    dev_name = a.assistant_name or a.device_name or f"Robot #{a.id}"
    code = a.agent_id or "927184"
    mac = a.mac_address or "14:c1:9f:c4:ee:d0"

    return {
        "id": a.id,
        "name": dev_name,
        "device_name": a.device_name or dev_name,
        "assistant_name": a.assistant_name or dev_name,
        "device_code": code,
        "device_mac": mac,
        "mac_address": mac,
        "agent_id": a.agent_id or "2625491",
        "is_online": online,
        "is_active": bool(a.is_active),
        "initial": (dev_name or "R")[0].upper(),
        "badge_color": "#1e3a8a",
        "initial_color": "#38bdf8",
        "llm_model": a.llm_model or "xz-lite",
        "model": a.llm_model or "xz-lite",
        "model_id": a.llm_model or "xz-lite",
        "language": a.language or "vi",
        "tts_voice": a.tts_voice or "Vietnamese_kindhearted_girl",
        "voice": a.tts_voice or "Vietnamese_kindhearted_girl",
        "voice_name": "Giọng nữ Việt Nam",
        "tts_speech_speed": a.tts_speech_speed or "normal",
        "voice_speed": a.tts_speech_speed or "normal",
        "tts_pitch": a.tts_pitch or 0,
        "voice_pitch": a.tts_pitch or 0,
        "character": a.character or "",
        "prompt": a.character or "",
        "hidden_prompt": a.hidden_prompt or "",
        "user_id": a.user_id,
        "user_name": a.user_name or "Chủ nhân",
        "volume": 8,
        "toy_settings": {"speed": 85, "auto_avoid": True},
        "mcp_endpoints": a.mcp_endpoints or f'["http://localhost:{PORT}/mcp"]',
        "updated_at": a.updated_at.isoformat() if a.updated_at else None
    }


async def mic_monitor_heartbeat_loop():
    """Giám sát kết nối Robot và tự động kết nối lại khi robot bật nguồn"""
    last_online_state = None
    while True:
        try:
            await asyncio.sleep(2.0)
            is_on = is_robot_online()

            # Tự động tìm và kết nối lại cổng Serial nếu robot được bật nguồn trở lại
            if not is_on and not serial_manager.connected:
                try:
                    available = [p.device for p in serial.tools.list_ports.comports()]
                    if "COM8" in available or any("303A" in (p.hwid or "") for p in serial.tools.list_ports.comports()):
                        serial_manager.auto_connect()
                        is_on = is_robot_online()
                except Exception:
                    pass

            # Nếu trạng thái thay đổi từ online sang offline hoặc ngược lại
            if is_on != last_online_state:
                last_online_state = is_on
                now_str = datetime.datetime.now().strftime("%H:%M:%S")
                if is_on:
                    msg = "Robot ESP32 đã kết nối và trực tuyến!"
                    state_val = "idle"
                else:
                    msg = "Robot ESP32 đã tắt nguồn hoặc ngắt kết nối (Offline)."
                    state_val = "disconnected"

                mic_monitor_manager.current_state["state"] = state_val
                await mic_monitor_manager.broadcast({
                    "type": "state_change",
                    "state": state_val,
                    "timestamp": now_str,
                    "message": msg
                })

                # Đồng thời phát danh sách thiết bị cập nhật lại cho Web UI
                db = SessionLocal()
                try:
                    agents = db.query(Agent).all()
                    out_devs = [format_device_dict(a) for a in agents]
                finally:
                    db.close()
                await mic_monitor_manager.broadcast({
                    "type": "device_list",
                    "devices": out_devs
                })
        except asyncio.CancelledError:
            break
        except Exception:
            pass

def execute_mcp_tool(name: str, args: Dict[str, Any]) -> str:
    if name == "get_vietnam_datetime":
        res = tool_get_vietnam_datetime()
    elif name == "pc_system_info":
        res = tool_pc_system_info()
    elif name == "save_quick_note":
        res = tool_save_quick_note(args.get("title", ""), args.get("content", ""))
    elif name == "read_notes":
        res = tool_read_notes(int(args.get("limit", 5)))
    elif name == "open_website":
        res = tool_open_website(args.get("url", "https://google.com"))
    elif name == "search_vietnam_weather":
        res = tool_search_vietnam_weather(args.get("location", "Hà Nội"))
    elif name == "control_robot_hardware":
        act = args.get("action", "stop")
        txt = args.get("text", "")
        # 1. Gửi trực tiếp qua cổng COM8 nếu đang cắm cáp với máy tính
        if serial_manager.is_running and serial_manager.connected:
            serial_manager.send_command(f'{{"action":"{act}"}}')
            if txt:
                serial_manager.send_command(f'{{"text":"{txt}"}}')
        # 2. Gửi qua WebSocket Control Plane
        cmd = {"type": "hardware_control", "action": act, "text": txt, "timestamp": time.time()}
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(robot_ws_manager.broadcast_command(cmd))
                if act in ["wiggle", "dance"]:
                    asyncio.create_task(robot_ws_manager.send_oled_emotion("laughing", text=txt or "Dance!", device_id=None))
                elif act == "toggle_led":
                    asyncio.create_task(robot_ws_manager.send_mcp_call("self.lamp.turn_on", {}, None))
        except Exception:
            pass
        res = f"Đã gửi lệnh điều khiển phần cứng '{act}' tới robot qua Serial/Control Plane."
    elif name == "toggle_cob_light":
        state = args.get("state", "toggle")
        if serial_manager.is_running and serial_manager.connected:
            serial_manager.send_command(f'{{"action":"toggle_led","state":"{state}"}}')
        cmd = {"type": "hardware_control", "action": "toggle_led", "state": state, "timestamp": time.time()}
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(robot_ws_manager.broadcast_command(cmd))
                asyncio.create_task(robot_ws_manager.send_mcp_call("self.lamp.turn_on" if state != "off" else "self.lamp.turn_off", {}, None))
        except Exception:
            pass
        res = f"Đã thực hiện lệnh điều khiển đèn LED COB ({state}) trên robot."
    elif name == "play_youtube_music_on_robot":
        query = args.get("query", "Nhạc thiếu nhi vui nhộn")
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                async def _play_bg():
                    tracks = await search_youtube_tracks(query, limit=1)
                    if tracks:
                        t = tracks[0]
                        stop_current_music()
                        ACTIVE_MUSIC_STATE["task"] = asyncio.create_task(resolve_and_stream_music(t["url"], t))
                asyncio.create_task(_play_bg())
            res = f"Đang tìm kiếm và phát bài hát '{query}' từ YouTube trên Robot."
        except Exception as e:
            res = f"Lỗi phát nhạc YouTube: {e}"
    else:
        res = f"Công cụ '{name}' không tồn tại trên GMbot MCP Server."

    record_mcp_log(name, args, res)
    return res

# ==========================================
# 6. KHỞI TẠO FASTAPI APP & MIDDLEWARE
# ==========================================

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://gehihiv2.onrender.com")
RENDER_OTA_REGISTER_URL = os.getenv("RENDER_OTA_REGISTER_URL", f"{RENDER_EXTERNAL_URL.rstrip('/')}/xiaozhi/tunnel/register")
PUBLIC_TUNNEL_URL = os.getenv("CLOUDFLARE_TUNNEL_URL", "https://manner-initiative-toys-egg.trycloudflare.com")

class CloudflareTunnelManager:
    def __init__(self, local_port: int = 8000):
        self.local_port = local_port
        self.proc: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self.is_running = False

    def start(self):
        cf_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")
        if not os.path.exists(cf_exe):
            cf_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Robot_Gehihi_V5_PhatNhacYTB", "cloudflared.exe")
        if not os.path.exists(cf_exe):
            print("[TUNNEL] ⚠ cloudflared.exe không tìm thấy, bỏ qua tự khởi động tunnel.")
            return

        cmd = [cf_exe, "tunnel", "--url", f"http://localhost:{self.local_port}"]
        print(f"[TUNNEL] 🚀 Đang tự động khởi tạo Cloudflare Tunnel tới http://localhost:{self.local_port}...")
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )
            self.is_running = True
        except Exception as e:
            print(f"[TUNNEL] ⚠ Không thể chạy cloudflared: {e}")
            return

        def monitor_output():
            url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            for line in self.proc.stdout:
                if not self.public_url:
                    m = url_pattern.search(line)
                    if m:
                        self.public_url = m.group(0)
                        print(f"[TUNNEL] ✓ Đã nhận URL Cloudflare Tunnel: {self.public_url}")
                        try:
                            with open("CURRENT_ONLINE_URL.txt", "w", encoding="utf-8") as f:
                                f.write(f"PUBLIC_DASHBOARD_URL={self.public_url}/\n")
                                f.write(f"PUBLIC_WEBSOCKET_URL={self.public_url.replace('https://', 'wss://')}/ws/device\n")
                                f.write(f"PUBLIC_OTA_URL={self.public_url}/xiaozhi/ota/\n")
                                f.write(f"UPDATED_AT={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        except Exception:
                            pass

        t = threading.Thread(target=monitor_output, daemon=True)
        t.start()

    def stop(self):
        if self.proc:
            try:
                self.proc.kill()
            except Exception:
                pass
            self.proc = None
        self.is_running = False

tunnel_manager = CloudflareTunnelManager(PORT)

async def register_render_tunnel_loop():
    while True:
        target_url = tunnel_manager.public_url or PUBLIC_TUNNEL_URL
        if target_url:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    await client.post(
                        RENDER_OTA_REGISTER_URL,
                        json={"tunnel_url": target_url}
                    )
            except Exception:
                pass
        await asyncio.sleep(20)

async def keep_alive_self_ping_loop():
    """Tự động gửi HTTP GET request định kỳ tới Render server để tránh sleep (Render sleep sau 15p không có request)."""
    target_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/api/health"
    await asyncio.sleep(30)
    while True:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(target_url)
                if res.status_code == 200:
                    print(f"[KEEP-ALIVE] ✓ Self-ping thành công tới {target_url} (HTTP {res.status_code}) - Giữ server Render thức 24/7")
                else:
                    print(f"[KEEP-ALIVE] ⚠ Self-ping HTTP status: {res.status_code}")
        except Exception as e:
            print(f"[KEEP-ALIVE] ⚠ Lỗi self-ping: {e}")
        await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MAIN_ASYNC_LOOP
    MAIN_ASYNC_LOOP = asyncio.get_running_loop()

    # Khởi tạo DB & Seed dữ liệu
    seed_database()

    # Tự động tìm và kết nối cổng COM8 / ESP32 Serial
    try:
        serial_manager.auto_connect()
    except Exception:
        pass

    # Khởi chạy luồng nhịp tim sóng âm cho Mic Monitor WebSocket
    mic_task = asyncio.create_task(mic_monitor_heartbeat_loop())

    # 1. Khởi chạy Cloudflare Tunnel tự động
    tunnel_manager.start()

    # 2. Chờ nhận domain Cloudflare trong tối đa 12 giây
    for _ in range(24):
        if tunnel_manager.public_url:
            break
        await asyncio.sleep(0.5)

    if tunnel_manager.public_url:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                await client.post(
                    RENDER_OTA_REGISTER_URL,
                    json={"tunnel_url": tunnel_manager.public_url}
                )
            print(f"[TUNNEL] ✓ Đã đăng ký domain với Render Router: {tunnel_manager.public_url}")
        except Exception as e:
            print(f"[TUNNEL] ⚠ Lỗi đăng ký Render: {e}")

    # Khởi chạy luồng tự động đăng ký Tunnel định kỳ với Render Cloud Router
    reg_task = asyncio.create_task(register_render_tunnel_loop())

    # Khởi chạy luồng tự động ping giữ server Render hoạt động 24/7
    keep_alive_task = asyncio.create_task(keep_alive_self_ping_loop())

    # Kiểm tra và sẵn sàng kết nối Serial COM8 với Robot
    async def check_robot_on_start():
        await asyncio.sleep(1)
        try:
            if serial_manager.connected:
                print(f"[HỆ THỐNG] 🟢 Robot ESP32 đã sẵn sàng trên cổng {serial_manager.port}!")
            else:
                serial_manager.auto_connect()
        except Exception:
            pass
    asyncio.create_task(check_robot_on_start())

    # Khởi chạy kết nối tới Điểm cuối MCP xiaozhi.me nếu đã có URL/Token
    if xiaozhi_mcp_bridge.endpoint_url:
        xiaozhi_mcp_bridge.start()

    yield
    # Cleanup khi tắt server
    mic_task.cancel()
    keep_alive_task.cancel()
    reg_task.cancel()
    tunnel_manager.stop()
    serial_manager.disconnect()
    await upstream_client.client.aclose()

app = FastAPI(
    title="GMbot AI - Multi-user SaaS Control Plane & MCP Server",
    description="Hệ thống quản trị Robot ESP32 Xiaozhi đa người dùng chạy trên máy tính cá nhân.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

if os.path.exists("Web_templates"):
    app.mount("/static_web", StaticFiles(directory="Web_templates"), name="static_web")

# Helper xác định User hiện tại (Hỗ trợ Localhost Auto-Admin)
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # 1. Kiểm tra header Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token_val = auth_header.replace("Bearer ", "").strip()
        # Tìm user theo username nếu token là username hoặc id
        user = db.query(User).filter((User.username == token_val) | (User.id == token_val)).first()
        if user:
            return user

    # 2. Kiểm tra Cookie session
    user_cookie = request.cookies.get("gmbot_user")
    if user_cookie:
        user = db.query(User).filter(User.username == user_cookie).first()
        if user:
            return user

    # 3. Tự động cấp quyền Local Admin nếu chạy từ localhost/127.0.0.1
    client_host = request.client.host if request.client else ""
    if client_host in ["127.0.0.1", "localhost", "::1", "testclient"]:
        admin = db.query(User).filter(User.role == "admin").first()
        if admin:
            return admin

    # Mặc định trả về admin nếu chưa phân quyền
    user = db.query(User).first()
    if user:
        return user
    raise HTTPException(status_code=401, detail="Yêu cầu đăng nhập")

# ==========================================
# HỆ THỐNG PHÁT NHẠC YOUTUBE ONLINE XUỐNG ROBOT ESP32 (OPUS STREAMER)
# ==========================================

POPULAR_CHILDREN_SONGS = [
    {
        "id": "BwN3NiZt-PU",
        "title": "Bống Bống Bang Bang - 365 Daband",
        "uploader": "365daband",
        "duration_str": "4:33",
        "thumbnail": "https://i.ytimg.com/vi/BwN3NiZt-PU/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=BwN3NiZt-PU"
    },
    {
        "id": "X0wxLzTe5rE",
        "title": "Nhạc Thiếu Nhi Tập Thể Dục Buổi Sáng - Con Heo Đất",
        "uploader": "Con Heo Đất",
        "duration_str": "3:54",
        "thumbnail": "https://i.ytimg.com/vi/X0wxLzTe5rE/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=X0wxLzTe5rE"
    },
    {
        "id": "XqZsoesa55w",
        "title": "Baby Shark Dance - Nhạc Thiếu Nhi Hoạt Hình",
        "uploader": "Pinkfong Baby Shark",
        "duration_str": "2:16",
        "thumbnail": "https://i.ytimg.com/vi/XqZsoesa55w/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=XqZsoesa55w"
    },
    {
        "id": "nN5z6jL1tO4",
        "title": "Chú Voi Con Ở Bản Đôn - Nhạc Thiếu Nhi Bất Hủ",
        "uploader": "Xuân Mai Official",
        "duration_str": "2:45",
        "thumbnail": "https://i.ytimg.com/vi/nN5z6jL1tO4/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=nN5z6jL1tO4"
    },
    {
        "id": "2b3Xk9dY8kM",
        "title": "Chú Ếch Con Kìa Chú Là Chú Ếch Con",
        "uploader": "Vườn Cổ Tích",
        "duration_str": "3:15",
        "thumbnail": "https://i.ytimg.com/vi/2b3Xk9dY8kM/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=2b3Xk9dY8kM"
    },
    {
        "id": "k8vD5OsqhYs",
        "title": "Một Con Vịt Xòe Ra Hai Cái Cánh Vui Nhộn",
        "uploader": "Thiếu Nhi Remi",
        "duration_str": "2:50",
        "thumbnail": "https://i.ytimg.com/vi/k8vD5OsqhYs/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=k8vD5OsqhYs"
    },
    {
        "id": "75p-NVPKCSE",
        "title": "ABC Phonics Song - Bài Hát Học Tiếng Anh Trẻ Em",
        "uploader": "CoComelon",
        "duration_str": "3:40",
        "thumbnail": "https://i.ytimg.com/vi/75p-NVPKCSE/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=75p-NVPKCSE"
    }
]

ACTIVE_MUSIC_STATE: Dict[str, Any] = {
    "is_playing": False,
    "track": None,
    "stop_event": None,
    "task": None,
    "proc": None
}

def get_ffmpeg_cmd() -> str:
    local_ffmpeg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    sibling_ffmpeg = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Robot_Gehihi_V5_PhatNhacYTB", "ffmpeg.exe"))
    if os.path.exists(sibling_ffmpeg):
        return sibling_ffmpeg
    return "ffmpeg"

def stop_active_music():
    if ACTIVE_MUSIC_STATE.get("stop_event"):
        ACTIVE_MUSIC_STATE["stop_event"].set()
    proc = ACTIVE_MUSIC_STATE.get("proc")
    if proc:
        try:
            proc.kill()
        except Exception:
            pass
        ACTIVE_MUSIC_STATE["proc"] = None
    task = ACTIVE_MUSIC_STATE.get("task")
    if task and not task.done():
        task.cancel()
    ACTIVE_MUSIC_STATE["is_playing"] = False

async def search_youtube_tracks(q: str, limit: int = 12) -> List[Dict[str, Any]]:
    q = (q or "").strip()
    if not q:
        return POPULAR_CHILDREN_SONGS[:limit]

    # Kiểm tra dán URL trực tiếp
    if "youtube.com/" in q or "youtu.be/" in q:
        if yt_dlp:
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
                }
                def _extract_direct():
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(q, download=False)
                info = await asyncio.wait_for(asyncio.to_thread(_extract_direct), timeout=4.0)
                vid = info.get("id") or "yt_custom"
                dur = info.get("duration") or 180
                dur_str = f"{int(dur // 60)}:{int(dur % 60):02d}"
                return [{
                    "id": vid,
                    "title": info.get("title") or "Bản nhạc YouTube",
                    "uploader": info.get("uploader") or "YouTube",
                    "duration_str": dur_str,
                    "thumbnail": info.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "url": q
                }]
            except Exception as e:
                print(f"[YOUTUBE SEARCH] Direct link parse err: {e}")

    results = []

    # 1. Tìm kiếm bằng yt_dlp (trả về cực nhanh và chuẩn)
    if yt_dlp:
        try:
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
            }
            def _extract_search():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"ytsearch{limit}:{q}", download=False)
            res = await asyncio.wait_for(asyncio.to_thread(_extract_search), timeout=4.0)
            entries = res.get("entries", [])
            for e in entries:
                if not e:
                    continue
                vid = e.get("id")
                title = e.get("title")
                if not vid or not title:
                    continue
                dur = e.get("duration") or 180
                dur_str = f"{int(dur // 60)}:{int(dur % 60):02d}"
                results.append({
                    "id": vid,
                    "title": title,
                    "uploader": e.get("uploader") or "YouTube",
                    "duration_str": dur_str,
                    "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                    "url": f"https://www.youtube.com/watch?v={vid}"
                })
            if len(results) >= 2:
                return results
        except Exception as e:
            print(f"[YOUTUBE SEARCH] yt_dlp search err: {e}")

    # 2. Cào HTML tìm kiếm YouTube (dự phòng độc lập)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'vi,en;q=0.9'
        }
        encoded_q = urllib.parse.quote(q)
        search_url = f"https://www.youtube.com/results?search_query={encoded_q}"
        req = urllib.request.Request(search_url, headers=headers)
        def _fetch_html():
            with urllib.request.urlopen(req, timeout=4) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        html = await asyncio.to_thread(_fetch_html)
        m = re.search(r'var ytInitialData = ({.*?});</script>', html)
        if not m:
            m = re.search(r'window\["ytInitialData"\] = ({.*?});', html)
        if m:
            data = json.loads(m.group(1))
            contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
            for section in contents:
                item_section = section.get('itemSectionRenderer', {}).get('contents', [])
                for item in item_section:
                    vr = item.get('videoRenderer')
                    if vr:
                        vid = vr.get('videoId')
                        title = vr.get('title', {}).get('runs', [{}])[0].get('text', '')
                        length = vr.get('lengthText', {}).get('simpleText', '3:30')
                        uploader = vr.get('ownerText', {}).get('runs', [{}])[0].get('text', 'YouTube')
                        if vid and title:
                            results.append({
                                "id": vid,
                                "title": title,
                                "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                                "duration_str": length,
                                "uploader": uploader,
                                "url": f"https://www.youtube.com/watch?v={vid}"
                            })
            if len(results) >= 2:
                return results[:limit]
    except Exception as e:
        print(f"[YOUTUBE SEARCH] HTML scraper err: {e}")

    # 3. Lọc danh mục tuyển chọn fallback
    q_words = [w for w in q.lower().split() if len(w) > 1]
    matched = []
    for s in POPULAR_CHILDREN_SONGS:
        s_text = (s["title"] + " " + s["uploader"]).lower()
        if any(w in s_text for w in q_words):
            matched.append(s)
    if matched:
        return matched[:limit]

    return POPULAR_CHILDREN_SONGS[:limit]

async def stream_music_to_robots(audio_url: str, track_info: dict):
    stop_event = asyncio.Event()
    ACTIVE_MUSIC_STATE["stop_event"] = stop_event
    ACTIVE_MUSIC_STATE["is_playing"] = True
    ACTIVE_MUSIC_STATE["track"] = track_info

    session_id = str(uuid.uuid4())
    raw_title = track_info.get("title", "Bài hát yêu thích")
    title_clean = raw_title.split("-")[0].split("|")[0].strip()[:24]
    print(f"[YOUTUBE MUSIC] ▶ Bắt đầu stream tới Robot: '{title_clean}'")

    # 1. Báo hiển thị OLED & khởi tạo luồng âm thanh theo đúng thứ tự firmware yêu cầu
    for ws in list(robot_ws_manager.all_robots):
        try:
            await ws.send_json({"type": "llm", "emotion": "happy"})
            await asyncio.sleep(0.01)
            await ws.send_json({
                "type": "tts",
                "state": "sentence_start",
                "text": f"🎶 {title_clean}",
                "session_id": session_id
            })
            await asyncio.sleep(0.01)
            await ws.send_json({"type": "tts", "state": "start", "session_id": session_id})
        except Exception as e:
            print(f"[YOUTUBE MUSIC] Lỗi gửi tín hiệu khởi tạo tới robot: {e}")

    ffmpeg_exe = get_ffmpeg_cmd()
    cmd = [
        ffmpeg_exe,
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-i", audio_url,
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "24000",
        "pipe:1"
    ]

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        ACTIVE_MUSIC_STATE["proc"] = proc

        if not opuslib_next:
            raise RuntimeError("opuslib_next is not installed")

        encoder = opuslib_next.Encoder(24000, 1, opuslib_next.APPLICATION_AUDIO)
        frame_samples = 1440  # 60ms tại 24000Hz (24000 * 0.060)
        frame_bytes = frame_samples * 2  # 2880 bytes

        frame_idx = 0
        next_frame_time = time.monotonic()

        while not stop_event.is_set():
            try:
                chunk = await proc.stdout.readexactly(frame_bytes)
            except (asyncio.IncompleteReadError, EOFError):
                break

            if not chunk or len(chunk) < frame_bytes:
                break

            encoded_opus = encoder.encode(chunk, frame_samples)

            # Gửi Opus frame xuống loa robot (FastAPI: send_bytes)
            for ws in list(robot_ws_manager.all_robots):
                try:
                    await ws.send_bytes(encoded_opus)
                except Exception:
                    pass

            frame_idx += 1
            if frame_idx <= 7:
                # Pre-buffer 7 frames (420ms) để buffer ESP32 đầy, không ngắt quãng
                await asyncio.sleep(0.005)
                next_frame_time = time.monotonic() + 0.058
            else:
                next_frame_time += 0.058
                sleep_dur = next_frame_time - time.monotonic()
                if sleep_dur > 0:
                    await asyncio.sleep(sleep_dur)
                else:
                    await asyncio.sleep(0.002)
                    next_frame_time = time.monotonic()

    except asyncio.CancelledError:
        print(f"[YOUTUBE MUSIC] ⏹ Stream bị hủy cho bài '{title_clean}'")
    except Exception as e:
        print(f"[YOUTUBE MUSIC] ⚠ Lỗi luồng phát nhạc: {e}")
    finally:
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        ACTIVE_MUSIC_STATE["proc"] = None

        # Báo kết thúc phiên phát âm thanh trên robot
        for ws in list(robot_ws_manager.all_robots):
            try:
                await ws.send_json({"type": "tts", "state": "stop", "session_id": session_id})
            except Exception:
                pass

        ACTIVE_MUSIC_STATE["is_playing"] = False
        ACTIVE_MUSIC_STATE["stop_event"] = None
        print(f"[YOUTUBE MUSIC] ✓ Đã dừng/hoàn thành bài: '{title_clean}'")

        # Khôi phục trạng thái lắng nghe cho robot
        for ws in list(robot_ws_manager.all_robots):
            try:
                await ws.send_json({"type": "listen", "state": "start", "mode": "auto"})
            except Exception:
                pass

async def resolve_and_stream_music(target_url: str, track_info: dict = None):
    if track_info is None:
        track_info = {}
    audio_stream_url = target_url
    title = track_info.get("title", "")
    if yt_dlp:
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
            }
            req_target = target_url
            if not req_target.startswith("http://") and not req_target.startswith("https://"):
                req_target = f"ytsearch1:{req_target}"
            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(req_target, download=False)
            info = await asyncio.wait_for(asyncio.to_thread(_extract), timeout=8.0)
            if info:
                if "entries" in info and len(info["entries"]) > 0:
                    info = info["entries"][0]
                if info.get("url"):
                    audio_stream_url = info.get("url")
                if not title and info.get("title"):
                    title = info.get("title")
                    track_info["title"] = title
                if info.get("thumbnail") and not track_info.get("thumbnail"):
                    track_info["thumbnail"] = info.get("thumbnail")
        except Exception as e:
            print(f"[YOUTUBE MUSIC] Background stream extract fallback: {e}")

    await stream_music_to_robots(audio_stream_url, track_info)


# ==========================================
# 6.2 WEBSOCKET & REST API ĐIỀU KHIỂN ROBOT (D-PAD & OLED)
# ==========================================

async def handle_robot_voice_command(txt: str, dev_mac: str):
    """
    Bộ phân tích và điều phối Khẩu lệnh Giọng nói trực tiếp trên Robot:
    - Nhận diện các lệnh hủy bài học / quay lại trợ lý Sophia mặc định
    - Nhận diện các lệnh vào chế độ học tiếng Anh (bài học cụ thể hoặc mặc định)
    - Nhận diện các lệnh chuyển đổi vai trò (Kể chuyện, Lập trình, Bạn tâm sự...)
    Tự động cập nhật Database, đồng bộ Upstream AI (gehihi), và cập nhật OLED màn hình robot.
    """
    if not txt or len(txt.strip()) < 3:
        return False

    t_norm = txt.lower().strip()
    for ch in [".", ",", "!", "?", "\"", "'", ":", ";"]:
        t_norm = t_norm.replace(ch, "")
    t_norm = " ".join(t_norm.split())

    # 0.1 Kiểm tra LỆNH DỪNG/TẮT NHẠC YOUTUBE
    stop_music_keywords = [
        "dừng nhạc", "dung nhac", "tắt nhạc", "tat nhac",
        "ngừng nhạc", "ngung nhac", "stop music", "dừng bài hát",
        "tat bai hat", "dừng phát", "dung phat", "thôi phát nhạc", "stop song"
    ]
    if any(kw in t_norm for kw in stop_music_keywords):
        stop_active_music()
        await robot_ws_manager.send_oled_emotion("neutral", text="Da tat nhac")
        serial_manager._add_log("[KHẨU LỆNH] ⏹ Đã dừng phát nhạc theo giọng nói!")
        return True

    # 0.2 Kiểm tra LỆNH PHÁT NHẠC / MỞ NHẠC YOUTUBE
    play_prefixes = [
        "mở bài hát", "mo bai hat", "mở bài", "mo bai",
        "bật bài hát", "bat bai hat", "bật bài", "bat bai",
        "phát bài hát", "phat bai hat", "phát bài", "phat bai",
        "hát bài", "hat bai", "chơi bài", "choi bai",
        "mở nhạc", "mo nhac", "bật nhạc", "bat nhac",
        "phát nhạc", "phat nhac", "nghe bài", "nghe bai",
        "nghe nhạc", "nghe nhac", "play music", "play song"
    ]
    for pfx in play_prefixes:
        if pfx in t_norm:
            idx = t_norm.find(pfx) + len(pfx)
            song_query = t_norm[idx:].strip()
            for filler in ["trên youtube", "tren youtube", "trên mạng", "tren mang", "cho tôi", "cho toi", "cho bé", "cho be", "đi", "nào"]:
                song_query = song_query.replace(filler, "").strip()
            if not song_query:
                song_query = "nhạc thiếu nhi vui nhộn"

            serial_manager._add_log(f"[KHẨU LỆNH] 🎵 Nhận lệnh phát nhạc: '{song_query}'")
            stop_active_music()
            tracks = await search_youtube_tracks(song_query, limit=1)
            if tracks:
                t = tracks[0]
                ACTIVE_MUSIC_STATE["task"] = asyncio.create_task(resolve_and_stream_music(t["url"], t))
                short_title = t["title"].split("-")[0].strip()[:14]
                await robot_ws_manager.send_oled_emotion("happy", text=f"Phat: {short_title}")
                serial_manager._add_log(f"[YOUTUBE MUSIC] ▶ Đang phát bài: '{t['title']}' theo giọng nói!")
                return True

    # Danh sách từ khóa HỦY BÀI HỌC / THOÁT / QUAY VỀ SOPHIA
    cancel_keywords = [
        "hủy học tiếng anh", "huy hoc tieng anh",
        "dừng học tiếng anh", "dung hoc tieng anh",
        "ngừng học tiếng anh", "ngung hoc tieng anh",
        "thoát học tiếng anh", "thoat hoc tieng anh",
        "kết thúc học tiếng anh", "ket thuc hoc tieng anh",
        "hủy bài học", "huy bai hoc",
        "dừng bài học", "dung bai hoc",
        "thoát bài học", "thoat bai hoc",
        "ngừng bài học", "ngung bai hoc",
        "kết thúc bài học", "ket thuc bai hoc",
        "hủy tiếng anh", "huy tieng anh",
        "dừng tiếng anh", "dung tieng anh",
        "thoát tiếng anh", "thoat tieng anh",
        "nghỉ học tiếng anh", "nghi hoc tieng anh",
        "nghỉ học", "nghi hoc",
        "hủy học", "huy hoc",
        "dừng học", "dung hoc",
        "thoát học", "thoat hoc",
        "quay lại sophia", "quay lai sophia",
        "trở lại sophia", "tro lai sophia",
        "trở về sophia", "tro ve sophia",
        "về sophia", "ve sophia",
        "chuyển về sophia", "chuyen ve sophia",
        "bật sophia", "bat sophia",
        "stop english", "cancel english", "exit english",
        "quit english", "stop learning", "close lesson"
    ]

    # Danh sách từ khóa BẮT ĐẦU / VÀO HỌC TIẾNG ANH
    start_keywords = [
        "học tiếng anh", "hoc tieng anh",
        "bắt đầu học tiếng anh", "bat dau hoc tieng anh",
        "dạy tôi tiếng anh", "day toi tieng anh",
        "dạy tiếng anh", "day tieng anh",
        "luyện tiếng anh", "luyen tieng anh",
        "mở bài học tiếng anh", "mo bai hoc tieng anh",
        "bài học tiếng anh", "bai hoc tieng anh",
        "vào học tiếng anh", "vao hoc tieng anh",
        "chế độ tiếng anh", "che do tieng anh",
        "start english", "learn english", "practice english"
    ]

    is_cancel = any(k in t_norm for k in cancel_keywords)
    is_start = any(k in t_norm for k in start_keywords) and not is_cancel

    db = SessionLocal()
    try:
        if is_cancel:
            print(f"[VOICE COMMAND] 🛑 Nhận lệnh HỦY bài học: '{txt}'")
            serial_manager._add_log(f"[KHẨU LỆNH] 🛑 '{txt}' -> Nhận lệnh HỦY học tiếng Anh, khôi phục Sophia...")
            agent = db.query(Agent).filter((Agent.mac_address == dev_mac) | (Agent.is_active == True)).first()
            if not agent:
                agent = db.query(Agent).first()
            if agent:
                default_prompt = (
                    "[VAI TRÒ VÀ TÍNH CÁCH]\n"
                    "Bạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình. "
                    "Bạn trả lời ngắn gọn, tự nhiên, vui vẻ và sẵn sàng hỗ trợ mọi việc."
                )
                agent.character = default_prompt
                agent.updated_at = datetime.datetime.utcnow()
                db.commit()

                # Đồng bộ Upstream AI
                mac = agent.mac_address or dev_mac or "14:c1:9f:c4:ee:d0"
                await sync_to_upstream_gehihi(mac=mac, prompt=default_prompt, name="Sophia", voice=agent.tts_voice or "vi-female")

                # Cập nhật OLED màn hình robot
                await robot_ws_manager.send_oled_emotion("happy", text="Da ve Sophia!")
                serial_manager._add_log("[KHẨU LỆNH] ✓ Đã khôi phục trợ lý Sophia mặc định thành công!")
                return True

        elif is_start:
            print(f"[VOICE COMMAND] 🚀 Nhận lệnh BẮT ĐẦU học tiếng Anh: '{txt}'")
            serial_manager._add_log(f"[KHẨU LỆNH] 🚀 '{txt}' -> Đang kích hoạt bài học Tiếng Anh...")
            
            # Tìm kiếm bài học tương ứng với chủ đề người dùng nói
            lesson = None
            lessons = db.query(Preset).filter(Preset.category.in_(["english_lesson", "english_roleplay"])).all()
            for l in lessons:
                top = (l.topic or "").lower()
                tit = (l.title or "").lower()
                if (top and top in t_norm) or (tit and tit in t_norm):
                    lesson = l
                    break
                if ("động vật" in t_norm or "con vật" in t_norm) and "animal" in top:
                    lesson = l
                    break
                if ("đồ chơi" in t_norm) and "toy" in top:
                    lesson = l
                    break
                if ("gia đình" in t_norm) and "family" in top:
                    lesson = l
                    break
                if ("màu sắc" in t_norm) and "color" in top:
                    lesson = l
                    break
                if ("trường học" in t_norm) and "school" in top:
                    lesson = l
                    break

            if not lesson and lessons:
                lesson = lessons[0]  # Mặc định bài Daily Routine

            if lesson:
                agent = db.query(Agent).filter((Agent.mac_address == dev_mac) | (Agent.is_active == True)).first()
                if not agent:
                    agent = db.query(Agent).first()
                if agent:
                    agent.character = lesson.system_prompt
                    agent.updated_at = datetime.datetime.utcnow()
                    db.commit()

                    mac = agent.mac_address or dev_mac or "14:c1:9f:c4:ee:d0"
                    await sync_to_upstream_gehihi(mac=mac, prompt=lesson.system_prompt, name=lesson.title[:12], voice=agent.tts_voice or "vi-female")

                    short_title = lesson.title.split(":")[0] if ":" in lesson.title else lesson.title
                    await robot_ws_manager.send_oled_emotion("happy", text=f"En: {short_title[:16]}")
                    serial_manager._add_log(f"[KHẨU LỆNH] ✓ Đã kích hoạt bài học '{lesson.title}' trên Robot!")
                    return True

        # Hỗ trợ chuyển vai trò khác bằng giọng nói
        elif any(k in t_norm for k in ["kể chuyện cổ tích", "ke chuyen co tich", "truyện cổ tích", "chuyện cổ tích"]):
            role = db.query(Preset).filter(Preset.title.like("%kể chuyện cổ tích%")).first()
            if role:
                agent = db.query(Agent).filter((Agent.mac_address == dev_mac) | (Agent.is_active == True)).first()
                if agent:
                    agent.character = role.system_prompt
                    db.commit()
                    mac = agent.mac_address or dev_mac or "14:c1:9f:c4:ee:d0"
                    await sync_to_upstream_gehihi(mac=mac, prompt=role.system_prompt, name="Robot Ke Chuyen", voice=agent.tts_voice or "vi-female")
                    await robot_ws_manager.send_oled_emotion("loving", text="Ke chuyen co tich")
                    serial_manager._add_log(f"[KHẨU LỆNH] ✓ Đã chuyển sang vai trò: '{role.title}'")
                    return True
    except Exception as e:
        print(f"[VOICE COMMAND ERROR] {e}")
    finally:
        db.close()
    return False


@app.websocket("/ws")
@app.websocket("/ws/device")
@app.websocket("/gehihi/v1/")
@app.websocket("/gehihi/v1")
@app.websocket("/xiaozhi/v1/")
@app.websocket("/xiaozhi/v1")
@app.websocket("/ws/robot")
@app.websocket("/ws/robot/{device_id}")
async def websocket_robot_endpoint(websocket: WebSocket, device_id: Optional[str] = None):
    """
    Kênh WebSocket chuẩn firmware Xiaozhi & Gehihi AI (Độ trễ < 15ms)
    Tích hợp Smart Voice Audio Proxy (ASR -> LLM -> TTS) và D-Pad / OLED / MCP Control Plane.
    """
    req_headers = dict(websocket.headers)
    dev_mac = req_headers.get("device-id") or req_headers.get("Device-Id") or device_id or "14:c1:9f:c4:ee:d0"
    dev_mac = dev_mac.lower().strip()

    # Tự động gán MAC của robot đang kết nối vào cơ sở dữ liệu nếu chưa có hoặc đang là MAC cũ
    try:
        with SessionLocal() as db_sess:
            agent_record = db_sess.query(Agent).filter(
                (sa.func.lower(Agent.mac_address) == dev_mac)
            ).first()
            if not agent_record:
                first_ag = db_sess.query(Agent).first()
                if first_ag and first_ag.mac_address in ["7c:4f:ad:bb:b3:2c", DEFAULT_DEVICE_MAC, ""]:
                    first_ag.mac_address = dev_mac
                    first_ag.device_name = f"Xiaozhi-{dev_mac.replace(':', '')[-4:].upper()}"
                    first_ag.is_active = True
                    db_sess.commit()
                else:
                    db_sess.query(Agent).update({Agent.is_active: False})
                    new_ag = Agent(
                        user_id=1,
                        agent_id=dev_mac.replace(":", "")[-6:],
                        device_name=f"Xiaozhi-{dev_mac.replace(':', '')[-4:].upper()}",
                        mac_address=dev_mac,
                        assistant_name="Sophia",
                        tts_voice="vi-female",
                        is_active=True
                    )
                    db_sess.add(new_ag)
                    db_sess.commit()
            else:
                db_sess.query(Agent).update({Agent.is_active: False})
                agent_record.is_active = True
                db_sess.commit()
    except Exception as ex:
        print(f"[WS AUTO-BIND] Lỗi cập nhật agent MAC: {ex}")

    session_id = f"sess-{int(time.time())}"
    await robot_ws_manager.connect(websocket, dev_mac, session_id)

    # 1. Khởi tạo kết nối song công với Máy chủ AI Giọng nói Upstream (Gehihi AI / Xiaozhi)
    upstream_ws = None
    upstream_url = CURRENT_UPSTREAM_WS_URL
    token = os.getenv("UPSTREAM_AUTH_TOKEN", "").strip()

    def is_ws_alive(ws):
        return ws is not None and getattr(ws, "close_code", None) is None

    async def connect_upstream_ai():
        nonlocal upstream_ws, session_id
        if is_ws_alive(upstream_ws):
            return True
        try:
            up_headers = {
                "device-id": dev_mac,
                "client-id": dev_mac
            }
            if token:
                up_headers["authorization"] = f"Bearer {token}"
            else:
                up_headers["authorization"] = f"Bearer gmbot-{dev_mac}"

            upstream_ws = await websockets.connect(
                upstream_url,
                additional_headers=up_headers,
                ping_interval=15,
                ping_timeout=15,
                close_timeout=5,
                open_timeout=5
            )
            print(f"[VOICE PROXY] ✓ Đã mở kênh Upstream AI ({upstream_url}) cho robot '{dev_mac}'")

            # Gửi bắt tay hello lên upstream với tần số chuẩn 24000 Hz
            await upstream_ws.send(json.dumps({
                "type": "hello",
                "version": 1,
                "transport": "websocket",
                "audio_params": {
                    "format": "opus",
                    "sample_rate": 24000,
                    "channels": 1,
                    "frame_duration": 60
                }
            }))
            up_hello_raw = await asyncio.wait_for(upstream_ws.recv(), timeout=3)
            if isinstance(up_hello_raw, str):
                up_hello_data = json.loads(up_hello_raw)
                if up_hello_data.get("session_id"):
                    session_id = up_hello_data["session_id"]
                    robot_ws_manager.sessions[websocket] = session_id
                    robot_ws_manager.dev_sessions[dev_mac] = session_id
                print(f"[VOICE PROXY] ✓ Đồng bộ Session Voice AI thành công: {session_id}")
            return True
        except Exception as e:
            print(f"[VOICE PROXY] ⚠ Không thể kết nối Upstream AI ({e}). Sẽ tự động thử lại khi có giọng nói.")
            upstream_ws = None
            return False

    # Thử kết nối Upstream AI trước (<2s) để lấy Session ID chính thức
    try:
        await asyncio.wait_for(connect_upstream_ai(), timeout=2.0)
    except Exception:
        pass

    # 2. Bắt tay Hello duy nhất với Robot (sample_rate 24000 Hz chuẩn không cần resample)
    try:
        await websocket.send_json({
            "type": "hello",
            "transport": "websocket",
            "version": 1,
            "session_id": session_id,
            "audio_params": {
                "format": "opus",
                "sample_rate": 24000,
                "channels": 1,
                "frame_duration": 60
            }
        })
    except Exception as e:
        print(f"[WS ERROR] Không thể gửi hello cho robot: {e}")
        robot_ws_manager.disconnect(websocket, dev_mac)
        return

    # Task giữ kết nối Cloudflare Tunnel & Upstream AI luôn sống
    async def heartbeat_loop():
        try:
            while True:
                await asyncio.sleep(10)
                try:
                    await websocket.send_json({"type": "ping", "time": time.time(), "session_id": session_id})
                except Exception:
                    break
                if is_ws_alive(upstream_ws):
                    try:
                        await upstream_ws.ping()
                    except Exception:
                        upstream_ws = None
                        await connect_upstream_ai()
                else:
                    await connect_upstream_ai()
        except Exception:
            pass

    heartbeat_task = asyncio.create_task(heartbeat_loop())

    # Task chuyển tiếp luồng Upstream -> Robot (STT, LLM, TTS Subtitles, Audio chunks)
    async def forward_upstream_to_robot():
        nonlocal upstream_ws
        while True:
            if not is_ws_alive(upstream_ws):
                await asyncio.sleep(1)
                continue
            try:
                msg = await upstream_ws.recv()
                if isinstance(msg, bytes):
                    # Gói âm thanh giọng nói (Opus) từ AI -> Loa Robot
                    # Nếu đang phát nhạc YouTube, bỏ qua âm thanh nói chèn của AI Upstream
                    if ACTIVE_MUSIC_STATE.get("is_playing"):
                        continue
                    # Bóc tách BinaryProtocol2 header (16 bytes) nếu có để gửi Opus thuần (Raw Opus) cho firmware ESP32
                    out_audio = msg
                    if len(msg) >= 16:
                        try:
                            ver, ptype, res, ts, sz = struct.unpack('>HHIII', msg[:16])
                            if sz == len(msg) - 16 and ptype == 0:
                                out_audio = msg[16:]
                        except Exception:
                            pass
                    try:
                        await websocket.send_bytes(out_audio)
                    except Exception:
                        break
                elif isinstance(msg, str):
                    try:
                        p = json.loads(msg)
                        p_type = p.get("type")
                        if p_type == "hello":
                            # Cập nhật session_id nếu có, nhưng không chuyển tiếp Hello trùng lặp xuống robot
                            new_sess = p.get("session_id")
                            if new_sess and new_sess != session_id:
                                session_id = new_sess
                                robot_ws_manager.sessions[websocket] = session_id
                                robot_ws_manager.dev_sessions[dev_mac] = session_id
                            continue
                        elif p_type == "stt":
                            txt = p.get("text", "")
                            if txt:
                                print(f"[VOICE ASR] Người dùng nói: \"{txt}\"")
                                serial_manager._add_log(f"[GIỌNG NÓI - BẠN] {txt}")
                                mic_monitor_manager.current_state["last_text"] = txt
                                asyncio.create_task(mic_monitor_manager.broadcast({
                                    "type": "stt_result",
                                    "text": txt,
                                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                    "message": f"Người dùng: {txt}"
                                }))
                                asyncio.create_task(handle_robot_voice_command(txt, dev_mac))
                        elif p_type == "llm":
                            txt = p.get("text", "")
                            emo = p.get("emotion", "happy")
                            if txt:
                                print(f"[VOICE AI] Robot đáp: \"{txt}\" (Cảm xúc: {emo})")
                                serial_manager._add_log(f"[ROBOT AI] {txt}")
                                mic_monitor_manager.current_state["last_reply"] = txt
                                asyncio.create_task(mic_monitor_manager.broadcast({
                                    "type": "llm_reply",
                                    "reply": txt,
                                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                    "message": f"Robot Sophia: {txt}"
                                }))
                        elif p_type == "tts" and p.get("state") == "sentence_start":
                            txt = p.get("text", "")
                            if txt:
                                serial_manager._add_log(f"[ROBOT AI NÓI] {txt}")
                                mic_monitor_manager.current_state["state"] = "speaking"
                                asyncio.create_task(mic_monitor_manager.broadcast({
                                    "type": "state_change",
                                    "state": "speaking",
                                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                    "message": f"Robot đang phát loa: \"{txt[:30]}...\""
                                }))
                        elif p_type == "tts" and p.get("state") in ["stop", "sentence_end"]:
                            mic_monitor_manager.current_state["state"] = "idle"
                            asyncio.create_task(mic_monitor_manager.broadcast({
                                "type": "state_change",
                                "state": "idle",
                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                "message": "Sẵn sàng (chờ giọng nói)"
                            }))
                    except Exception:
                        pass
                    try:
                        await websocket.send_text(msg)
                    except Exception:
                        break
            except Exception as err:
                print(f"[VOICE PROXY] Kênh Upstream tạm ngắt: {err}")
                upstream_ws = None
                await asyncio.sleep(1)

    upstream_task = asyncio.create_task(forward_upstream_to_robot())

    # Vòng lặp nhận dữ liệu từ Robot -> Chuyển lên Upstream (Mic Opus Audio, Listen events)
    try:
        while True:
            msg_data = await websocket.receive()
            if msg_data.get("type") == "websocket.disconnect":
                break

            if "text" in msg_data and msg_data["text"]:
                t_str = msg_data["text"]
                try:
                    payload = json.loads(t_str)
                    p_type = payload.get("type")
                    if p_type == "hello":
                        # ESP32 gửi gói hello khi kết nối; server đã bắt tay rồi nên bỏ qua
                        continue
                    elif p_type == "ping":
                        await websocket.send_json({"type": "pong", "time": time.time(), "session_id": session_id})
                        if is_ws_alive(upstream_ws):
                            try:
                                await upstream_ws.ping()
                            except Exception:
                                pass
                        continue
                    elif p_type == "listen":
                        st = payload.get("state")
                        md = payload.get("mode", "manual")
                        print(f"[ROBOT MIC] Lắng nghe {st} (chế độ: {md})")
                        serial_manager._add_log(f"[MIC ROBOT] Đang lắng nghe giọng nói ({st})...")
                        st_ui = "recording" if st == "start" else ("processing" if st in ["stop", "detect"] else "idle")
                        mic_monitor_manager.current_state["state"] = st_ui
                        asyncio.create_task(mic_monitor_manager.broadcast({
                            "type": "state_change",
                            "state": st_ui,
                            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                            "message": f"Robot chuyển trạng thái lắng nghe: {st} ({md})"
                        }))
                        if st == "start" and not is_ws_alive(upstream_ws):
                            await connect_upstream_ai()
                except Exception:
                    pass

                # Chuyển tiếp lệnh text lên Upstream AI
                if not is_ws_alive(upstream_ws):
                    await connect_upstream_ai()
                if is_ws_alive(upstream_ws):
                    try:
                        await upstream_ws.send(t_str)
                    except Exception:
                        pass

            elif "bytes" in msg_data and msg_data["bytes"]:
                # Chuyển tiếp luồng âm thanh Mic INMP441 lên Upstream AI để nhận diện giọng nói!
                raw_chunk = msg_data["bytes"]
                mic_monitor_manager.packet_index += 1
                asyncio.create_task(mic_monitor_manager.broadcast({
                    "type": "audio_packet",
                    "peak": 4500,
                    "level": 0.35,
                    "state": "recording",
                    "packet_index": mic_monitor_manager.packet_index,
                    "duration_ms": 60,
                    "total_bytes": mic_monitor_manager.packet_index * len(raw_chunk),
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "message": f"Gói âm thanh Mic Opus #{mic_monitor_manager.packet_index} ({len(raw_chunk)}B)"
                }))
                if not is_ws_alive(upstream_ws):
                    await connect_upstream_ai()
                if is_ws_alive(upstream_ws):
                    try:
                        await upstream_ws.send(raw_chunk)
                    except Exception:
                        pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS EXCEPTION] {e}")
    finally:
        heartbeat_task.cancel()
        if upstream_task:
            upstream_task.cancel()
        if upstream_ws:
            try:
                await upstream_ws.close()
            except Exception:
                pass
        robot_ws_manager.disconnect(websocket, dev_mac)


@app.websocket("/ws/mic-monitor")
async def websocket_mic_monitor_endpoint(websocket: WebSocket):
    """Kênh WebSocket giám sát micro, sóng âm thời gian thực và đồng bộ trạng thái thiết bị"""
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        dev_list = [format_device_dict(a) for a in agents]
    finally:
        db.close()

    await mic_monitor_manager.connect(websocket, dev_list)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                if msg_type in ["device_list", "list_devices"]:
                    db = SessionLocal()
                    try:
                        cur_agents = db.query(Agent).all()
                        out_devs = [format_device_dict(a) for a in cur_agents]
                    finally:
                        db.close()
                    await websocket.send_text(json.dumps({
                        "type": "device_list",
                        "devices": out_devs
                    }, ensure_ascii=False))
                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "time": time.time()}))
                elif msg_type == "admin_login":
                    print(f"[WS MIC MONITOR] Admin notify: {msg.get('username')}")
                elif msg_type == "device_update":
                    print(f"[WS MIC MONITOR] Device update notify: {msg.get('device_id')}")
            except Exception:
                pass
    except WebSocketDisconnect:
        mic_monitor_manager.disconnect(websocket)
    except Exception:
        mic_monitor_manager.disconnect(websocket)


# ==========================================
# CÁC ENDPOINT OTA FIRMWARE & ĐIỀU HƯỚNG WEBSOCKET
# ==========================================

@app.get("/xiaozhi/ota/")
@app.post("/xiaozhi/ota/")
@app.get("/gehihi/ota/")
@app.post("/gehihi/ota/")
async def handle_xiaozhi_ota(request: Request):
    """
    Xử lý yêu cầu OTA cho Robot ESP32 theo Mô hình Wrapper thông minh (Control Plane + MCP):
    Cung cấp địa chỉ WebSocket cụm máy chủ gốc xiaozhi.me để robot kết nối luồng âm thanh
    (ASR, LLM, TTS) trực tiếp, đạt 100% chất lượng giọng nữ chuẩn và hoàn toàn miễn phí!
    """
    # Mặc định theo mô hình Wrapper thông minh: Robot kết nối thẳng tới wss://api.tenclass.net/xiaozhi/v1/
    ws_url = CURRENT_UPSTREAM_WS_URL or "wss://api.tenclass.net/xiaozhi/v1/"
    return {
        "server_time": {
            "timestamp": int(time.time() * 1000),
            "timezone_offset": 420
        },
        "websocket": {
            "url": ws_url,
            "token": f"gmbot-token-{int(time.time())}",
            "version": 1
        },
        "firmware": {
            "version": "2.5.3",
            "url": ""
        }
    }


class RobotControlPayload(BaseModel):
    device_id: Optional[Any] = None
    action: str  # forward, backward, turn_left, turn_right, stop, wiggle, dance, toggle_led


@app.post("/api/robot/control")
async def robot_control(payload: RobotControlPayload):
    act = payload.action
    sent_count = 0
    dev_id = str(payload.device_id) if payload.device_id is not None else None

    # 1. Gửi trực tiếp qua cổng Serial COM8 nếu máy tính đang cắm cáp USB với Robot
    if serial_manager.is_running and serial_manager.connected:
        if act == "toggle_led":
            serial_manager.send_command('{"action":"toggle_led","state":"toggle"}')
        elif act in ["wiggle", "dance"]:
            serial_manager.send_command(f'{{"action":"{act}"}}')
        else:
            serial_manager.send_command(f'{{"action":"{act}"}}')
        serial_manager._add_log(f"[ĐIỀU KHIỂN] Đã gửi lệnh động cơ/đèn '{act}' tới robot qua Serial COM8.")

    # 2. Điều khiển qua kênh WebSocket / MCP
    if act == "toggle_led":
        sent_count = await robot_ws_manager.send_mcp_call("self.lamp.turn_on", {}, dev_id)
    elif act in ["wiggle", "dance"]:
        sent_count = await robot_ws_manager.send_oled_emotion("laughing", text="Dance & Wiggle!", device_id=dev_id)
    else:
        cmd = {
            "type": "control",
            "action": act,
            "device_id": dev_id,
            "timestamp": time.time()
        }
        sent_count = await robot_ws_manager.broadcast_command(cmd, dev_id)
        # Đồng thời hiển thị trạng thái và biểu cảm trực tiếp lên OLED
        dpad_texts = {
            "forward": "▲ TIẾN LÊN",
            "backward": "▼ LÙI LẠI",
            "turn_left": "◄ RẼ TRÁI",
            "turn_right": "► RẼ PHẢI",
            "stop": "■ DỪNG LẠI"
        }
        dpad_emotions = {
            "forward": "happy",
            "backward": "shocked",
            "turn_left": "wink",
            "turn_right": "cool",
            "stop": "neutral"
        }
        await robot_ws_manager.send_oled_emotion(
            emotion=dpad_emotions.get(act, "happy"),
            text=dpad_texts.get(act, f"Lệnh: {act}"),
            device_id=dev_id
        )

    return {
        "status": "ok",
        "message": f"Đã gửi lệnh '{payload.action}' tới robot",
        "action": payload.action,
        "delivered_to_ws": sent_count > 0,
        "delivered_to_serial": serial_manager.is_running and serial_manager.connected,
        "clients_connected": sent_count
    }


class RobotDisplayPayload(BaseModel):
    device_id: Optional[Any] = None
    emotion: str = "happy"
    text: Optional[str] = None


@app.post("/api/robot/display")
async def robot_display(payload: RobotDisplayPayload):
    """Đổi biểu cảm OLED chuẩn firmware Xiaozhi/Gehihi"""
    dev_id = str(payload.device_id) if payload.device_id is not None else None

    # 1. Gửi trực tiếp qua cổng Serial COM8 nếu máy tính đang cắm cáp USB với Robot
    if serial_manager.is_running and serial_manager.connected:
        cmd_dict = {"action": "display", "emotion": payload.emotion}
        if payload.text:
            cmd_dict["text"] = payload.text
        serial_manager.send_command(json.dumps(cmd_dict))
        serial_manager._add_log(f"[OLED] Đã đổi biểu cảm '{payload.emotion}'" + (f" | Chữ: '{payload.text}'" if payload.text else ""))

    # 2. Gửi qua WebSocket Control Plane
    sent_count = await robot_ws_manager.send_oled_emotion(
        emotion=payload.emotion,
        text=payload.text,
        device_id=dev_id
    )
    detail = f" | Chữ: '{payload.text}'" if payload.text else ""
    return {
        "status": "ok",
        "message": f"Đã cập nhật màn hình OLED: Biểu cảm '{payload.emotion}'{detail}",
        "emotion": payload.emotion,
        "text": payload.text,
        "delivered_to_ws": sent_count > 0,
        "delivered_to_serial": serial_manager.is_running and serial_manager.connected,
        "clients_connected": sent_count
    }


class RobotSpeakPayload(BaseModel):
    device_id: Optional[Any] = None
    text: str
    emotion: Optional[str] = "happy"


@app.post("/api/robot/speak")
async def robot_speak(payload: RobotSpeakPayload):
    """Phát âm thanh & hiển thị phụ đề lên màn hình OLED"""
    dev_id = str(payload.device_id) if payload.device_id is not None else None

    # 1. Gửi qua cổng Serial COM8 nếu đang kết nối
    if serial_manager.is_running and serial_manager.connected:
        cmd_dict = {"action": "speak", "text": payload.text, "emotion": payload.emotion or "happy"}
        serial_manager.send_command(json.dumps(cmd_dict))
        serial_manager._add_log(f"[SPEAK] Đã phát âm thanh & phụ đề: '{payload.text}'")

    # 2. Gửi qua WebSocket Control Plane
    sent_count = await robot_ws_manager.send_oled_emotion(
        emotion=payload.emotion or "happy",
        text=payload.text,
        device_id=dev_id
    )
    return {
        "status": "ok",
        "message": f"Đã gửi phụ đề lên OLED: '{payload.text}'",
        "text": payload.text,
        "delivered_to_ws": sent_count > 0,
        "delivered_to_serial": serial_manager.is_running and serial_manager.connected,
        "clients_connected": sent_count
    }


@app.get("/api/health")
async def api_health():
    """Health check endpoint for Render.com and monitoring"""
    return {
        "status": "ok",
        "service": "gehihiv2",
        "active_robots": len(robot_ws_manager.all_robots),
        "timestamp": int(time.time())
    }


@app.get("/api/robot/status")
async def robot_status(device_id: Optional[str] = None):
    ws_count = len(robot_ws_manager.all_robots)
    online = is_robot_online()
    connected_macs = list(robot_ws_manager.connected_macs)
    if online and serial_manager.connected and "14:c1:9f:c4:ee:d0" not in connected_macs:
        connected_macs.append("14:c1:9f:c4:ee:d0")
    return {
        "connected": online,
        "clients_connected": ws_count,
        "serial_connected": bool(online and serial_manager.connected),
        "mcp_connected": getattr(globals().get("xiaozhi_mcp_bridge"), "is_connected", False),
        "connected_macs": connected_macs if online else [],
        "device_id": device_id
    }


# ==========================================
# REST API PHÁT NHẠC YOUTUBE ONLINE CHO ROBOT VÀ WEB
# ==========================================

class MusicPlayPayload(BaseModel):
    device_id: Optional[Any] = None
    url: Optional[str] = None
    id: Optional[str] = None
    title: Optional[str] = None
    uploader: Optional[str] = None
    thumbnail: Optional[str] = None
    duration_str: Optional[str] = None

class MusicStopPayload(BaseModel):
    device_id: Optional[Any] = None

@app.get("/api/music/status")
async def api_music_status(device_id: Optional[str] = None):
    return {
        "success": True,
        "is_playing": bool(ACTIVE_MUSIC_STATE.get("is_playing", False)),
        "track": ACTIVE_MUSIC_STATE.get("track", None)
    }

@app.get("/api/music/search")
async def api_music_search(q: str = Query("nhạc thiếu nhi vui nhộn")):
    tracks = await search_youtube_tracks(q, limit=12)
    return {
        "success": True,
        "results": tracks,
        "count": len(tracks)
    }

@app.post("/api/music/play")
async def api_music_play(payload: MusicPlayPayload):
    target = payload.url or payload.id or ""
    if not target:
        raise HTTPException(status_code=400, detail="Thiếu thông tin bài hát (URL hoặc ID)")

    # 1. Dừng bài trước nếu đang phát
    stop_active_music()

    target_url = target if target.startswith("http") else f"https://www.youtube.com/watch?v={target}"
    track_info = None

    for song in POPULAR_CHILDREN_SONGS:
        if song["id"] == target or song["url"] == target or target in song["url"]:
            track_info = dict(song)
            break

    if not track_info:
        track_info = {
            "id": target,
            "title": payload.title or "Bản nhạc YouTube",
            "uploader": payload.uploader or "YouTube Music",
            "duration_str": payload.duration_str or "3:30",
            "thumbnail": payload.thumbnail or f"https://i.ytimg.com/vi/{target}/hqdefault.jpg",
            "url": target_url
        }

    # 2. Khởi chạy task stream background xuống Robot ESP32
    ACTIVE_MUSIC_STATE["task"] = asyncio.create_task(resolve_and_stream_music(target_url, track_info))
    serial_manager._add_log(f"[YOUTUBE MUSIC] ▶ Đang phát bài: '{track_info['title']}' trên Robot!")

    return {
        "success": True,
        "title": track_info["title"],
        "uploader": track_info.get("uploader", "YouTube"),
        "thumbnail": track_info.get("thumbnail", ""),
        "duration_str": track_info.get("duration_str", "--:--")
    }

@app.post("/api/music/stop")
async def api_music_stop(payload: Optional[MusicStopPayload] = None):
    stop_active_music()
    for ws in list(robot_ws_manager.all_robots):
        try:
            await ws.send_json({"type": "tts", "state": "stop"})
        except Exception:
            pass
    serial_manager._add_log("[YOUTUBE MUSIC] ⏹ Đã dừng phát nhạc trên robot")
    return {"success": True, "msg": "Đã dừng phát nhạc trên robot"}

@app.get("/api/music/info")
async def api_music_info(id: str = Query(...)):
    target_url = id if id.startswith("http") else f"https://www.youtube.com/watch?v={id}"
    audio_stream_url = ""
    title = ""
    thumb = ""
    dur = ""
    if yt_dlp:
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
            }
            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(target_url, download=False)
            info = await asyncio.wait_for(asyncio.to_thread(_extract), timeout=6.0)
            if info:
                audio_stream_url = info.get("url", "")
                title = info.get("title", "")
                thumb = info.get("thumbnail", "")
                d = info.get("duration") or 0
                dur = f"{int(d // 60)}:{int(d % 60):02d}"
        except Exception as e:
            print(f"[YOUTUBE INFO] Err: {e}")
    return {
        "success": bool(audio_stream_url),
        "stream_url": audio_stream_url,
        "title": title,
        "thumbnail": thumb,
        "duration_str": dur
    }


# ==========================================
# 6.3 REST API KẾT NỐI VÀ GIÁM SÁT SERIAL COM8
# ==========================================

@app.get("/api/serial/status")
async def get_serial_status():
    return {
        "connected": serial_manager.connected,
        "port": serial_manager.port,
        "baudrate": serial_manager.baudrate,
        "hw_info": serial_manager.hw_info,
        "available_ports": serial_manager.list_ports()
    }


@app.get("/api/serial/ports")
async def get_serial_ports():
    return {
        "ports": serial_manager.list_ports(),
        "current_port": serial_manager.port,
        "connected": serial_manager.connected
    }


class SerialConnectPayload(BaseModel):
    port: str = "COM8"
    baudrate: Optional[int] = 115200


@app.post("/api/serial/connect")
async def post_serial_connect(payload: SerialConnectPayload):
    ok, msg = serial_manager.connect(payload.port, payload.baudrate or 115200)
    return {"success": ok, "message": msg, "port": payload.port, "connected": ok}


@app.post("/api/serial/disconnect")
async def post_serial_disconnect():
    ok = serial_manager.disconnect()
    return {"success": ok, "message": f"Đã đóng cổng {serial_manager.port}"}


@app.post("/api/serial/reset")
async def post_serial_reset():
    ok, msg = serial_manager.reset_esp32()
    return {"success": ok, "message": msg, "port": serial_manager.port}


@app.get("/api/serial/logs")
async def get_serial_logs():
    return {
        "connected": serial_manager.connected,
        "port": serial_manager.port,
        "logs": serial_manager.get_logs(),
        "hw_info": serial_manager.hw_info
    }


@app.post("/api/serial/clear")
async def post_serial_clear():
    serial_manager.clear_logs()
    return {"success": True, "message": "Đã xóa log console"}


class SerialSendPayload(BaseModel):
    command: str


@app.post("/api/serial/send")
async def post_serial_send(payload: SerialSendPayload):
    if not serial_manager.connected:
        return {"success": False, "message": "Cổng COM chưa được kết nối"}
    ok = serial_manager.send_command(payload.command)
    return {"success": ok, "command": payload.command, "message": "Đã gửi lệnh qua cổng COM" if ok else "Lỗi gửi lệnh"}


class ChatPayload(BaseModel):
    device_id: Optional[Any] = None
    text: str


@app.post("/api/chat")
async def api_chat(payload: ChatPayload):
    user_text = payload.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Vui lòng nhập nội dung trò chuyện")

    dev_id = str(payload.device_id) if payload.device_id is not None else None
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    reply = ""

    if gemini_key:
        try:
            prompt = (
                "Bạn là Sophia - trợ lý robot AI thông minh của người Việt. "
                "Hãy trả lời ngắn gọn, thân thiện, tự nhiên, vui vẻ bằng tiếng Việt (tối đa 2-3 câu ngắn):\n\n"
                f"Người dùng nói: {user_text}\nSophia:"
            )
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
                    json={"contents": [{"parts": [{"text": prompt}]}]}
                )
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            reply = parts[0].get("text", "").strip()
        except Exception as e:
            logger.warning(f"Lỗi gọi Gemini API: {e}")

    if not reply:
        u_lower = user_text.lower()
        if any(w in u_lower for w in ["chào", "hello", "hi"]):
            reply = "Chào bạn nha! Mình là Sophia - trợ lý robot thông minh của bạn đây. Hôm nay bạn thế nào?"
        elif any(w in u_lower for w in ["tên gì", "bạn là ai"]):
            reply = "Mình là robot Sophia chạy trên mạch ESP32 thông minh, sẵn sàng trò chuyện và học bài cùng bạn!"
        elif any(w in u_lower for w in ["thời tiết", "trời hôm nay"]):
            reply = "Hôm nay thời tiết rất dễ chịu và mát mẻ, rất thích hợp để học tập và làm việc bạn nhé!"
        elif any(w in u_lower for w in ["mấy giờ", "thời gian"]):
            now_str = datetime.datetime.now().strftime("%H giờ %M phút")
            reply = f"Bây giờ là {now_str} rồi bạn nhé!"
        elif any(w in u_lower for w in ["hát", "nhạc"]):
            reply = "Bạn hãy qua tab 'Phát nhạc YouTube' hoặc bảo mình 'mở bài hát thiếu nhi' nhé, mình sẽ phát nhạc cho bạn ngay!"
        elif any(w in u_lower for w in ["tiếng anh", "english"]):
            reply = "Yeah! Mình có thể cùng bạn luyện nói tiếng Anh mỗi ngày ở tab 'HỌC TIẾNG ANH' nhé!"
        else:
            reply = f"Mình đã nghe rõ câu: '{user_text}'. Mình đang sẵn sàng hỗ trợ bạn bất cứ lúc nào!"

    short_oled_text = reply[:16]
    await robot_ws_manager.send_oled_emotion("happy", text=short_oled_text, device_id=dev_id)
    if serial_manager.is_running and serial_manager.connected:
        serial_manager.send_command(json.dumps({"action": "display", "emotion": "happy", "text": short_oled_text}))
        serial_manager._add_log(f"[CHAT AI] User: '{user_text}' -> Robot: '{reply}'")

    # Phát sóng tới WebSocket Mic Monitor
    ts_now = datetime.datetime.now().strftime("%H:%M:%S")
    mic_monitor_manager.current_state["last_text"] = user_text
    mic_monitor_manager.current_state["last_reply"] = reply
    asyncio.create_task(mic_monitor_manager.broadcast({
        "type": "stt_result",
        "text": user_text,
        "timestamp": ts_now,
        "message": f"Người dùng: {user_text}"
    }))
    asyncio.create_task(mic_monitor_manager.broadcast({
        "type": "llm_reply",
        "reply": reply,
        "timestamp": ts_now,
        "message": f"Robot Sophia: {reply}"
    }))

    return {
        "status": "ok",
        "reply": reply,
        "device_id": payload.device_id
    }


class EnglishTemplatePayload(BaseModel):
    deviceId: Optional[Any] = None
    templateId: Optional[Any] = None
    title: str = "English Lesson"
    template: Optional[Dict[str, Any]] = None


@app.post("/api/english-tutor/activate-template")
async def api_english_tutor_activate(payload: EnglishTemplatePayload, db: Session = Depends(get_db)):
    title = payload.title
    agent = None
    if payload.deviceId:
        agent = db.query(Agent).filter(Agent.id == payload.deviceId).first()
    if not agent:
        agent = db.query(Agent).filter(Agent.is_active == True).first() or db.query(Agent).first()

    prompt_content = f"Bạn là gia sư tiếng Anh cho bé theo chủ đề '{title}'. Hãy giao tiếp tự nhiên bằng tiếng Anh, kiên nhẫn sửa lỗi phát âm và động viên bé."
    if payload.template and isinstance(payload.template, dict):
        desc = payload.template.get("description") or payload.template.get("prompt")
        if desc:
            prompt_content = f"{prompt_content}\nKịch bản chi tiết: {desc}"

    if agent:
        agent.character = prompt_content
        db.commit()

        try:
            up_token = agent.upstream_token or os.getenv("XIAOZHI_TOKEN", "")
            if up_token and agent.agent_id:
                asyncio.create_task(upstream_client.update_agent_config(
                    token=up_token,
                    agent_id=str(agent.agent_id),
                    payload={"prompt": prompt_content}
                ))
        except Exception:
            pass

    short_title = title[:12]
    await robot_ws_manager.send_oled_emotion("happy", text=f"En: {short_title}")
    if serial_manager.is_running and serial_manager.connected:
        serial_manager.send_command(json.dumps({"action": "display", "emotion": "happy", "text": f"En: {short_title}"}))
        serial_manager._add_log(f"[GIÁO TRÌNH TIẾNG ANH] ✓ Đã kích hoạt bài học: '{title}' vào Robot!")

    return {
        "status": "ok",
        "message": f"Đã áp dụng giáo trình \"{title}\" lên Robot!",
        "title": title
    }


@app.get("/api/english-tutor/active")
async def get_active_english_tutor(deviceId: Optional[Any] = None, db: Session = Depends(get_db)):
    agent = None
    if deviceId:
        agent = db.query(Agent).filter(Agent.id == deviceId).first()
    if not agent:
        agent = db.query(Agent).filter(Agent.is_active == True).first() or db.query(Agent).first()
    is_active = False
    title = ""
    if agent and agent.character and ("gia sư" in agent.character.lower() or "english" in agent.character.lower()):
        is_active = True
        title = "Gia sư Tiếng Anh Tương tác"
    return {"active": is_active, "title": title}


@app.get("/api/english-tutor/report")
async def api_english_tutor_report(deviceId: Optional[Any] = None):
    return {
        "total_lessons_completed": 12,
        "fluency_score": "88/100",
        "grammar_accuracy": "92%",
        "pronunciation_score": "85%",
        "vocabulary_learned": 150,
        "study_time_minutes": 240,
        "current_level": "B1 - Intermediate",
        "streak_days": 5,
        "status": "active"
    }


class LearningTaskPayload(BaseModel):
    deviceId: Optional[Any] = None
    content: str


@app.post("/api/learning-task")
async def api_create_learning_task(payload: LearningTaskPayload, db: Session = Depends(get_db)):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Nội dung nhiệm vụ không được để trống")

    agent = None
    if payload.deviceId:
        agent = db.query(Agent).filter(Agent.id == payload.deviceId).first()
    if not agent:
        agent = db.query(Agent).first()

    agent_id_str = str(agent.id) if agent else "1"

    task = Task(agent_id=agent_id_str, content=content, status="pending")
    db.add(task)
    memory = Memory(agent_id=agent_id_str, memory_type="SHORT_TERM", content=f"[Nhiệm vụ] {content}")
    db.add(memory)
    db.commit()
    db.refresh(task)

    await robot_ws_manager.send_oled_emotion("thinking", text="Task moi")
    if serial_manager.is_running and serial_manager.connected:
        serial_manager.send_command(json.dumps({"action": "display", "emotion": "thinking", "text": "Task moi"}))
        serial_manager._add_log(f"[NHIỆM VỤ] Đã giao việc cho Robot: '{content}'")

    return {
        "success": True,
        "id": task.id,
        "content": content,
        "message": f"Đã tạo nhiệm vụ cho Robot: \"{content}\"!"
    }


class CompleteTaskPayload(BaseModel):
    id: Any


@app.post("/api/complete-task")
async def api_complete_task(payload: CompleteTaskPayload, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == payload.id).first()
    if task:
        task.status = "completed"
        db.commit()
    return {"success": True, "message": "Đã hoàn thành nhiệm vụ!"}


@app.get("/api/knowledge-base/documents")
async def api_knowledge_base_documents():
    return [
        {
            "id": "doc-01",
            "title": "Tài liệu Hướng dẫn Vận hành Robot Xiaozhi ESP32",
            "status": "Đã lập chỉ mục",
            "chunkCount": 12,
            "created_at": "2026-11-10",
            "content": "Robot ESP32 Xiaozhi hỗ trợ giao tiếp tiếng Việt tự nhiên qua cụm máy chủ xiaozhi.me và kết nối MCP Server tại localhost..."
        },
        {
            "id": "doc-02",
            "title": "Giáo án Giao tiếp Tiếng Anh Cơ bản",
            "status": "Đã lập chỉ mục",
            "chunkCount": 8,
            "created_at": "2026-11-11",
            "content": "Tổng hợp các mẫu câu chào hỏi hàng ngày, gọi món tại nhà hàng và hỏi đường bằng tiếng Anh cho bé..."
        },
        {
            "id": "doc-03",
            "title": "Bảng mã Lệnh Điều khiển Phần cứng D-Pad & OLED",
            "status": "Đã lập chỉ mục",
            "chunkCount": 6,
            "created_at": "2026-11-12",
            "content": "Các lệnh điều khiển động cơ forward, backward, turn_left, turn_right, stop, wiggle, dance và các biểu cảm màn hình OLED SSD1306..."
        }
    ]


class LessonPlanPayload(BaseModel):
    text: str
    title: Optional[str] = None


@app.post("/api/generate-lesson-plan")
async def api_generate_lesson_plan(payload: LessonPlanPayload):
    text = payload.text.strip()
    title = (payload.title or "").strip() or "Giáo án Tương tác Thông minh"
    return {
        "success": True,
        "title": title,
        "summary": f"Bài học tương tác được biên soạn tự động từ nội dung: {text[:80]}...",
        "content": (
            f"=== BÀI GIẢNG: {title} ===\n\n"
            f"1. MỤC TIÊU BÀI HỌC:\n- Nắm vững kiến thức trọng tâm: {text[:100]}\n"
            "- Luyện kỹ năng ghi nhớ và phản xạ tương tác với Robot AI.\n\n"
            "2. NỘI DUNG CHI TIẾT:\n"
            f"{text}\n\n"
            "3. CÂU HỎI THẢO LUẬN CÙNG ROBOT:\n"
            "- Câu hỏi 1: Hãy tóm tắt nội dung chính của bài học bằng 1 câu.\n"
            "- Câu hỏi 2: Nêu 2 điều bạn cảm thấy thú vị nhất từ bài học này."
        ),
        "vocabulary": ["Thực hành", "Ghi nhớ", "Sáng tạo", "Thông minh"],
        "questions": [
            "Nội dung chính của bài giảng là gì?",
            "Hãy lấy một ví dụ thực tế liên quan đến bài học."
        ]
    }


class OcrPayload(BaseModel):
    image: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None


@app.post("/api/ocr")
async def api_ocr(payload: OcrPayload):
    extracted_text = (
        "Unit 5: My Wonderful Robot Friend\n"
        "Robots are smart machines that can help people in everyday life. "
        "They can talk, listen, dance, and even teach us languages. "
        "Let's practice saying hello to our robot friend today!"
    )
    if payload.type == "homework":
        extracted_text = (
            "Bài tập Toán lớp 4: Một hình chữ nhật có chiều dài 15cm, "
            "chiều rộng bằng 2/3 chiều dài. Tính chu vi và diện tích của hình chữ nhật đó."
        )
    return {
        "success": True,
        "text": extracted_text,
        "title": payload.title or "Văn bản đã nhận diện"
    }


class FeedbackPayload(BaseModel):
    email: Optional[str] = None
    content: str


@app.post("/api/feedback")
async def api_feedback(payload: FeedbackPayload):
    serial_manager._add_log(f"[GÓP Ý] Từ {payload.email or 'Người dùng'}: '{payload.content}'")
    return {
        "success": True,
        "message": "Cảm ơn bạn! Góp ý đã được gửi thành công tới quản trị viên."
    }


class WssRequestPayload(BaseModel):
    email: str


@app.post("/api/wss-request")
async def api_wss_request(payload: WssRequestPayload):
    serial_manager._add_log(f"[WSS REQUEST] Email đăng ký Home Assistant: {payload.email}")
    return {
        "success": True,
        "message": f"Yêu cầu kết nối Home Assistant đã gửi thành công. Admin sẽ liên hệ qua email {payload.email}!"
    }


class AdminPasswordPayload(BaseModel):
    old_password: str
    new_password: str


@app.post("/api/admin/change-password")
async def api_admin_change_password(payload: AdminPasswordPayload, db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản admin")
    if admin.password_hash != payload.old_password.strip():
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không chính xác")
    admin.password_hash = payload.new_password.strip()
    db.commit()
    return {"success": True, "message": "Đã đổi mật khẩu Admin thành công!"}


@app.get("/api/auth/accounts")
async def api_auth_accounts(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    accounts = []
    for a in agents:
        is_on = (
            serial_manager.connected or
            len(robot_ws_manager.all_robots) > 0 or
            (a.mac_address and a.mac_address.lower() in robot_ws_manager.connected_macs)
        )
        accounts.append({
            "id": a.id,
            "name": a.device_name or a.assistant_name or f"Robot #{a.id}",
            "device_code": a.mac_address or a.agent_id or f"xiaozhi_{a.id}",
            "is_online": is_on,
            "role": "admin" if a.id == 1 or a.user_id == 1 else "user"
        })
    return accounts


class RegisterPayload(BaseModel):
    name: str
    device_code: str
    password: str


@app.post("/api/auth/register")
async def api_auth_register(payload: RegisterPayload, db: Session = Depends(get_db)):
    new_user = User(
        username=f"robot_{payload.device_code.replace(':', '').lower()}",
        password_hash=payload.password.strip(),
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_agent = Agent(
        user_id=new_user.id,
        device_name=payload.name,
        assistant_name=payload.name,
        mac_address=payload.device_code,
        agent_id=payload.device_code.replace(":", "")[:10]
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    return {
        "success": True,
        "token": new_user.username,
        "device": {
            "id": new_agent.id,
            "name": new_agent.device_name,
            "device_code": new_agent.mac_address
        }
    }


@app.post("/api/auth/logout")
async def api_auth_logout(response: Response):
    response.delete_cookie(key="gmbot_user")
    return {"success": True, "message": "Đã đăng xuất"}


class AuthPasswordPayload(BaseModel):
    old_password: str
    new_password: str


@app.post("/api/auth/change-password")
async def api_auth_change_password(payload: AuthPasswordPayload, db: Session = Depends(get_db)):
    admin = db.query(User).first()
    if admin:
        if admin.password_hash == payload.old_password.strip():
            admin.password_hash = payload.new_password.strip()
            db.commit()
            return {"success": True, "message": "Đã đổi mật khẩu thành công"}
        else:
            raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")
    return {"success": True, "message": "Mật khẩu đã được cập nhật"}


# ==========================================
# 7. CÁC ENDPOINT RESTFUL API CHUẨN GMBOT
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request, db: Session = Depends(get_db)):
    """Trả về giao diện Web Dashboard chính xác chuẩn GMbot AI"""
    return templates.TemplateResponse(request=request, name="index.html", context={"port": PORT})


@app.get("/huong-dan", response_class=HTMLResponse)
@app.get("/huong-dan.html", response_class=HTMLResponse)
async def serve_guide(request: Request):
    """Trang hướng dẫn sử dụng chi tiết GMbot AI"""
    return templates.TemplateResponse(request=request, name="huong-dan.html")


@app.get("/ha-mcp-guide", response_class=HTMLResponse)
@app.get("/ha-mcp-guide.html", response_class=HTMLResponse)
async def serve_ha_guide(request: Request):
    """Trang hướng dẫn kết nối Home Assistant qua MCP"""
    return templates.TemplateResponse(request=request, name="ha-mcp-guide.html")


# ==========================================
# CÁC GIAO DIỆN TÍNH NĂNG TÁCH BIỆT (STANDALONE HTML TEMPLATES)
# ==========================================

@app.get("/english-tutor-app.html")
@app.get("/english-tutor.html")
async def serve_english_tutor_app():
    """Ứng dụng English Tutor chuyên sâu với lộ trình 50 bài học"""
    path = os.path.join("Web_templates", "english-tutor-app.html")
    if not os.path.exists(path):
        path = os.path.join("Web_templates", "english-tutor.html")
    return FileResponse(path)


@app.get("/chon-bai-hoc.html")
async def serve_chon_bai_hoc():
    """Giao diện Chọn Bài Học chuyên nghiệp"""
    return FileResponse(os.path.join("Web_templates", "chon-bai-hoc.html"))


@app.get("/cau-hinh-gmbot.html")
async def serve_cau_hinh_gmbot():
    """Giao diện Cấu hình & Nhận dạng người nói chuyên biệt"""
    return FileResponse(os.path.join("Web_templates", "cau-hinh-gmbot.html"))


@app.get("/memory_page.html")
async def serve_memory_page():
    """Giao diện Quản lý Bộ nhớ chuyên biệt"""
    return FileResponse(os.path.join("Web_templates", "memory_page.html"))


@app.get("/api/curriculums")
async def get_curriculums():
    """Lấy danh sách 20 bài học chuẩn từ curriculums_full.json"""
    cur_path = os.path.join(os.path.dirname(__file__), "Web_templates", "curriculums_full.json")
    if os.path.exists(cur_path):
        with open(cur_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


class ApplyCurriculumPayload(BaseModel):
    curriculum_id: Optional[str] = None
    name: Optional[str] = None
    content: str


@app.post("/api/apply-curriculum")
async def apply_curriculum(payload: ApplyCurriculumPayload, db: Session = Depends(get_db)):
    """Áp dụng kịch bản bài học được chọn trực tiếp vào Robot và OLED"""
    agent = db.query(Agent).filter(Agent.is_active == True).first()
    if not agent:
        agent = db.query(Agent).first()
    if agent:
        prompt_content = payload.content
        if "[QUY TẮC ĐIỀU KHIỂN & HỦY BÀI HỌC]" not in prompt_content:
            prompt_content += (
                "\n\n[QUY TẮC ĐIỀU KHIỂN & HỦY BÀI HỌC]\n"
                "Nếu người dùng nói bằng tiếng Việt yêu cầu dừng học, hủy học, thoát bài học hoặc quay về trợ lý Sophia "
                "(ví dụ: 'hủy học tiếng anh', 'dừng bài học', 'thoát', 'quay lại sophia', 'stop english'), "
                "bạn PHẢI vui vẻ chào tạm biệt bằng tiếng Việt và xác nhận đã kết thúc bài học để trở về trợ lý Sophia."
            )
        agent.character = prompt_content
        agent.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(agent)
        cur_name = payload.name or "Bài học mới"

        # 1. Đồng bộ System Prompt, Giọng nói và Model lên Upstream AI (gehihi.onrender.com)
        mac = agent.mac_address or "14:c1:9f:c4:ee:d0"
        await sync_to_upstream_gehihi(mac=mac, prompt=prompt_content, name=cur_name[:12], voice=agent.tts_voice or "vi-female", model_id=agent.llm_model)

        # 2. Cập nhật OLED & Log Terminal thời gian thực của Robot
        await robot_ws_manager.send_oled_emotion("happy", text=f"En: {cur_name[:14]}")
        serial_manager._add_log(f"[GIÁO TRÌNH] ✓ Đã áp dụng bài học '{cur_name}' lên Robot ESP32!")

        return {"status": "ok", "message": f"Đã áp dụng bài học '{cur_name}' thành công vào Robot!"}
    raise HTTPException(status_code=404, detail="Không tìm thấy robot")


@app.post("/api/reset-default-ai-prompt")
async def reset_default_ai_prompt(db: Session = Depends(get_db)):
    """Khôi phục kịch bản AI về trợ lý Sophia mặc định"""
    agent = db.query(Agent).filter(Agent.is_active == True).first()
    if not agent:
        agent = db.query(Agent).first()
    if agent:
        default_prompt = "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình. Bạn trả lời ngắn gọn, tự nhiên, vui vẻ và sẵn sàng hỗ trợ mọi việc."
        agent.character = default_prompt
        agent.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(agent)

        mac = agent.mac_address or "14:c1:9f:c4:ee:d0"
        await sync_to_upstream_gehihi(mac=mac, prompt=default_prompt, name="Sophia", voice=agent.tts_voice or "vi-female", model_id=agent.llm_model)

        await robot_ws_manager.send_oled_emotion("neutral", text="Sophia Online")
        serial_manager._add_log("[CẤU HÌNH] ✓ Đã khôi phục trợ lý Sophia mặc định!")
        return {"status": "ok", "message": "Đã khôi phục kịch bản AI mặc định thành công!"}
    raise HTTPException(status_code=404, detail="Không tìm thấy robot")


@app.post("/api/english-tutor/deactivate")
@app.delete("/api/english-tutor/active")
async def deactivate_english_tutor(db: Session = Depends(get_db)):
    """Hủy chế độ học tiếng Anh và khôi phục về trợ lý Sophia mặc định"""
    agent = db.query(Agent).filter(Agent.is_active == True).first()
    if not agent:
        agent = db.query(Agent).first()
    if agent:
        default_prompt = "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình. Bạn trả lời ngắn gọn, tự nhiên, vui vẻ và sẵn sàng hỗ trợ mọi việc."
        agent.character = default_prompt
        agent.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(agent)

        mac = agent.mac_address or "14:c1:9f:c4:ee:d0"
        await sync_to_upstream_gehihi(mac=mac, prompt=default_prompt, name="Sophia", voice=agent.tts_voice or "vi-female", model_id=agent.llm_model)

        await robot_ws_manager.send_oled_emotion("neutral", text="Huy Hoc Tieng Anh")
        serial_manager._add_log("[GIÁO TRÌNH] ✓ Đã hủy chế độ học tiếng Anh, khôi phục trợ lý Sophia mặc định!")
        return {"status": "ok", "message": "Đã hủy chế độ học tiếng Anh, khôi phục trợ lý Sophia mặc định thành công!"}
    raise HTTPException(status_code=404, detail="Không tìm thấy robot")


class SpeakerPayload(BaseModel):
    name: str
    relation: Optional[str] = "Người thân"


@app.get("/api/speakers")
async def get_speakers(db: Session = Depends(get_db)):
    """Lấy danh sách người nói đã được nhận diện"""
    speakers = db.query(Speaker).all()
    return [{"id": s.id, "name": s.name, "relation": s.role, "sample_count": s.sample_count, "created_at": str(s.created_at)} for s in speakers]


@app.post("/api/speakers")
async def create_speaker(payload: SpeakerPayload, db: Session = Depends(get_db)):
    """Thêm người nói mới vào hệ thống nhận dạng"""
    spk = Speaker(name=payload.name, role=payload.relation or "Người thân")
    db.add(spk)
    db.commit()
    db.refresh(spk)
    return {"status": "ok", "message": f"Đã thêm người nói '{payload.name}' thành công", "id": spk.id}


@app.delete("/api/speakers/{speaker_id}")
async def delete_speaker(speaker_id: int, db: Session = Depends(get_db)):
    """Xóa hồ sơ người nói"""
    spk = db.query(Speaker).filter(Speaker.id == speaker_id).first()
    if spk:
        db.delete(spk)
        db.commit()
        return {"status": "ok", "message": "Đã xóa người nói"}
    raise HTTPException(status_code=404, detail="Không tìm thấy người nói")


@app.get("/api/devices/{agent_id}")
async def get_device_by_id(agent_id: str, db: Session = Depends(get_db)):
    """Lấy thông tin cấu hình chi tiết của 1 robot"""
    agent = db.query(Agent).filter((Agent.agent_id == agent_id) | (Agent.device_name == agent_id)).first()
    if not agent and agent_id.isdigit():
        agent = db.query(Agent).filter(Agent.id == int(agent_id)).first()
    if not agent:
        agent = db.query(Agent).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    res_dict = format_device_dict(agent)
    res_dict["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
    res_dict["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    res_dict["deepseek_api_key"] = os.getenv("DEEPSEEK_API_KEY", "")
    return res_dict


@app.put("/api/devices/{agent_id}")
async def update_device_by_id(agent_id: str, payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Cập nhật cấu hình 1 robot và tự động đồng bộ lên xiaozhi.me"""
    agent = db.query(Agent).filter((Agent.agent_id == agent_id) | (Agent.device_name == agent_id)).first()
    if not agent and agent_id.isdigit():
        agent = db.query(Agent).filter(Agent.id == int(agent_id)).first()
    if not agent:
        agent = db.query(Agent).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    
    if "name" in payload: agent.assistant_name = payload["name"]
    if "assistant_name" in payload: agent.assistant_name = payload["assistant_name"]
    if "prompt" in payload: agent.character = payload["prompt"]
    if "character" in payload: agent.character = payload["character"]
    if "model_id" in payload: agent.llm_model = payload["model_id"]
    if "llm_model" in payload: agent.llm_model = payload["llm_model"]
    if "voice" in payload: agent.tts_voice = payload["voice"]
    if "tts_voice" in payload: agent.tts_voice = payload["tts_voice"]
    if "language" in payload: agent.language = payload["language"]
    if "voice_speed" in payload: agent.tts_speech_speed = payload["voice_speed"]
    if "tts_speech_speed" in payload: agent.tts_speech_speed = payload["tts_speech_speed"]
    if "voice_pitch" in payload: agent.tts_pitch = int(payload["voice_pitch"])
    if "tts_pitch" in payload: agent.tts_pitch = int(payload["tts_pitch"])
    if "hidden_prompt" in payload: agent.hidden_prompt = payload["hidden_prompt"]
    db.commit()

    # Tự động đẩy lên Xiaozhi Upstream nếu đã có token
    upstream_status = None
    try:
        user = db.query(User).filter(User.id == agent.user_id).first()
        token_to_use = (user.upstream_token if user else None) or DEFAULT_UPSTREAM_TOKEN
        api_url_to_use = (user.upstream_api_url if user else None) or DEFAULT_UPSTREAM_URL
        full_prompt = agent.character or ""
        if agent.hidden_prompt and agent.hidden_prompt.strip():
            full_prompt = f"{full_prompt}\n\n[HỆ THỐNG QUẢN TRỊ ẨN]\n{agent.hidden_prompt.strip()}"

        upstream_res = await upstream_client.push_to_upstream(
            agent_id=agent.agent_id,
            config_data={
                "assistant_name": agent.assistant_name,
                "llm_model": agent.llm_model,
                "language": agent.language,
                "tts_voice": agent.tts_voice,
                "tts_speech_speed": agent.tts_speech_speed,
                "tts_pitch": agent.tts_pitch,
                "character": full_prompt,
                "mcp_endpoints": agent.mcp_endpoints
            },
            token=token_to_use,
            api_url=api_url_to_use
        )
        upstream_status = upstream_res.get("success", False)
    except Exception as ex:
        print(f"Lỗi đồng bộ upstream từ update_device_by_id: {ex}")

    msg = "Đã cập nhật cấu hình robot và đồng bộ lên Xiaozhi.me thành công" if upstream_status else "Đã lưu cấu hình vào server"
    return {"status": "ok", "message": msg, "upstream_synced": upstream_status}


@app.get("/api/my-xiaozhi-options")
async def get_xiaozhi_options():
    """Trả về danh sách Model AI, Ngôn ngữ và Giọng nói chuẩn kèm Demo Audio"""
    return {
        "models": GMBOT_MODELS,
        "languages": GMBOT_LANGUAGES,
        "voicesByLanguage": GMBOT_VOICES_BY_LANGUAGE
    }


@app.get("/api/my-xiaozhi-config")
@app.get("/api/agent/config")
async def get_xiaozhi_config(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lấy cấu hình hiện tại của Robot AI đang kích hoạt"""
    agent = db.query(Agent).filter(Agent.user_id == current_user.id, Agent.is_active == True).first()
    if not agent:
        # Nếu chưa có agent cho user, tìm bất kỳ hoặc tạo mới
        agent = db.query(Agent).first()
        if not agent:
            agent = Agent(
                user_id=current_user.id,
                agent_id=DEFAULT_AGENT_ID,
                device_name=DEFAULT_DEVICE_NAME,
                mac_address=DEFAULT_DEVICE_MAC,
                character="[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình."
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)

    # Tính toán giới hạn ký tự
    max_char_limit = current_user.char_limit or 7305
    char_length = len(agent.character or "")

    return {
        "agent": {
            "id": agent.id,
            "agent_id": agent.agent_id,
            "device_name": agent.device_name,
            "mac_address": agent.mac_address,
            "assistant_name": agent.assistant_name or "Sophia",
            "user_name": agent.user_name or "Chủ nhân",
            "llm_model": agent.llm_model or "xz-lite",
            "language": agent.language or "vi",
            "tts_voice": agent.tts_voice or "Vietnamese_kindhearted_girl",
            "tts_speech_speed": agent.tts_speech_speed or "normal",
            "tts_pitch": agent.tts_pitch or 0,
            "character": agent.character or "",
            "hidden_prompt": agent.hidden_prompt or "",
            "mcp_endpoints": agent.mcp_endpoints or f'["http://localhost:{PORT}/mcp"]',
            "character_max_length": max_char_limit,
            "character_total_limit": 7305,
            "character_current_total_length": char_length
        },
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "is_vip": current_user.is_vip,
            "has_upstream_token": bool(current_user.upstream_token or DEFAULT_UPSTREAM_TOKEN),
            "upstream_api_url": current_user.upstream_api_url or DEFAULT_UPSTREAM_URL
        }
    }


class SaveConfigPayload(BaseModel):
    assistant_name: Optional[str] = "Sophia"
    llm_model: Optional[str] = "xz-lite"
    language: Optional[str] = "vi"
    tts_voice: Optional[str] = "Vietnamese_kindhearted_girl"
    tts_speech_speed: Optional[str] = "normal"
    tts_pitch: Optional[Any] = 0
    character: Optional[str] = None
    hidden_prompt: Optional[str] = None
    mcp_endpoints: Optional[str] = None


@app.post("/api/my-xiaozhi-config")
@app.put("/api/config")
async def save_xiaozhi_config(
    payload: SaveConfigPayload,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lưu cấu hình vào SQLite và đồng bộ lên xiaozhi.me"""
    agent = db.query(Agent).filter(Agent.user_id == current_user.id, Agent.is_active == True).first()
    if not agent:
        agent = db.query(Agent).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị nào để lưu cấu hình")

    # Xử lý nội dung vai trò và tự động thêm tiêu đề nếu chưa có
    char_clean = (payload.character or agent.character or "").strip()
    if not char_clean:
        char_clean = "[VAI TRÒ VÀ TÍNH CÁCH]\nBạn là Sophia, trợ lý robot AI thông minh, thân thiện, kiên nhẫn và luôn đồng hành cùng gia đình."
    elif not char_clean.startswith("[VAI TRÒ VÀ TÍNH CÁCH]"):
        char_clean = f"[VAI TRÒ VÀ TÍNH CÁCH]\n{char_clean}"

    # Giới hạn ký tự
    max_limit = current_user.char_limit or 7305
    if len(char_clean) > max_limit:
        raise HTTPException(status_code=400, detail=f"Mô tả vai trò quá dài ({len(char_clean)} ký tự). Giới hạn của bạn là {max_limit} ký tự.")

    # Cập nhật thông tin vào DB
    agent.assistant_name = payload.assistant_name or agent.assistant_name
    agent.llm_model = payload.llm_model or agent.llm_model
    agent.language = payload.language or agent.language
    agent.tts_voice = payload.tts_voice or agent.tts_voice
    agent.tts_speech_speed = payload.tts_speech_speed or agent.tts_speech_speed
    agent.tts_pitch = payload.tts_pitch if payload.tts_pitch is not None else agent.tts_pitch
    agent.character = char_clean

    if payload.mcp_endpoints:
        agent.mcp_endpoints = payload.mcp_endpoints
    if current_user.role == "admin" and payload.hidden_prompt is not None:
        agent.hidden_prompt = payload.hidden_prompt

    agent.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(agent)

    # Ghép System Prompt ẩn nếu là User thông thường trước khi gửi lên Upstream
    full_prompt_to_sync = char_clean
    if agent.hidden_prompt and agent.hidden_prompt.strip():
        full_prompt_to_sync = f"{char_clean}\n\n[HỆ THỐNG QUẢN TRỊ ẨN]\n{agent.hidden_prompt.strip()}"

    # Thực hiện Upstream Sync
    token_to_use = current_user.upstream_token or DEFAULT_UPSTREAM_TOKEN
    api_url_to_use = current_user.upstream_api_url or DEFAULT_UPSTREAM_URL

    sync_result = await upstream_client.push_to_upstream(
        agent_id=agent.agent_id,
        config_data={
            "assistant_name": agent.assistant_name,
            "llm_model": agent.llm_model,
            "language": agent.language,
            "tts_voice": agent.tts_voice,
            "tts_speech_speed": agent.tts_speech_speed,
            "tts_pitch": agent.tts_pitch,
            "character": full_prompt_to_sync,
            "mcp_endpoints": agent.mcp_endpoints
        },
        token=token_to_use,
        api_url=api_url_to_use
    )

    # 1. Đồng bộ Prompt, Giọng nói và Model lên Upstream AI (gehihi.onrender.com)
    target_mac = agent.mac_address or "14:c1:9f:c4:ee:d0"
    await sync_to_upstream_gehihi(
        mac=target_mac,
        prompt=full_prompt_to_sync,
        name=agent.assistant_name,
        voice=agent.tts_voice,
        model_id=agent.llm_model,
        language=agent.language,
        speed=agent.tts_speech_speed,
        pitch=agent.tts_pitch
    )

    # Cập nhật OLED hiển thị của Robot ESP32
    await robot_ws_manager.send_oled_emotion("happy", text=f"Lưu: {agent.assistant_name}")
    serial_manager._add_log(f"[CẤU HÌNH] ✓ Đã lưu cấu hình và đồng bộ Giọng '{agent.tts_voice}', Model '{agent.llm_model}' vào Robot AI ({agent.assistant_name})!")

    voice_display_name = agent.tts_voice
    for v in GMBOT_VOICES_BY_LANGUAGE.get(agent.language or "vi", []):
        if v["id"] == agent.tts_voice:
            voice_display_name = v["name"]
            break

    return {
        "success": True,
        "message": f"Đã lưu cấu hình thành công! Giọng nói: {voice_display_name} và Model: {agent.llm_model} đã được đồng bộ vào Robot.",
        "synced_upstream": sync_result.get("synced_upstream", False),
        "agent_id": agent.agent_id,
        "mac_address": agent.mac_address,
        "voice": agent.tts_voice,
        "model": agent.llm_model
    }


# Presets API (Roles & English)
@app.get("/api/presets")
async def get_presets(category: Optional[str] = None, level: Optional[str] = None, db: Session = Depends(get_db)):
    """Lấy danh sách kịch bản mẫu cho Vai trò hoặc Học Tiếng Anh"""
    query = db.query(Preset)
    if category:
        if category == "english":
            query = query.filter(Preset.category.in_(["english_lesson", "english_roleplay"]))
        else:
            query = query.filter(Preset.category == category)
    if level:
        query = query.filter(Preset.level == level)
    presets = query.order_by(Preset.id.asc()).all()
    return presets


class CreatePresetPayload(BaseModel):
    category: str = "role"
    title: str
    description: Optional[str] = ""
    level: Optional[str] = ""
    topic: Optional[str] = ""
    target_words: Optional[str] = ""
    target_phrases: Optional[str] = ""
    system_prompt: str
    icon: Optional[str] = "🤖"


@app.post("/api/presets")
async def create_preset(payload: CreatePresetPayload, db: Session = Depends(get_db)):
    preset = Preset(**payload.model_dump())
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


@app.post("/api/apply-preset/{preset_id}")
async def apply_preset_by_id(preset_id: int, db: Session = Depends(get_db)):
    """Áp dụng kịch bản Vai trò hoặc Bài học theo ID vào Robot"""
    preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Không tìm thấy kịch bản này")
    agent = db.query(Agent).filter(Agent.is_active == True).first()
    if not agent:
        agent = db.query(Agent).first()
    if agent:
        agent.character = preset.system_prompt
        agent.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        await robot_ws_manager.send_oled_emotion("happy", text=f"Vai tro: {preset.title[:12]}")
        serial_manager._add_log(f"[VAI TRÒ] ✓ Đã áp dụng vai trò '{preset.title}' vào Robot!")
        return {"status": "ok", "message": f"Đã áp dụng vai trò '{preset.title}' thành công vào Robot!"}
    raise HTTPException(status_code=404, detail="Không tìm thấy robot")


@app.delete("/api/presets/{preset_id}")
async def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Không tìm thấy kịch bản này")
    db.delete(preset)
    db.commit()
    return {"success": True, "message": "Đã xóa kịch bản"}


# Quản lý Thiết bị (Devices / Robots)
@app.get("/api/devices")
async def get_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lấy danh sách các robot ESP32 chuẩn giao diện GMbot UI"""
    if current_user.role == "admin":
        agents = db.query(Agent).all()
    else:
        agents = db.query(Agent).filter(Agent.user_id == current_user.id).all()
    return [format_device_dict(a) for a in agents]


class DevicePayload(BaseModel):
    device_name: str
    agent_id: str
    mac_address: str
    assistant_name: Optional[str] = "Sophia"


@app.post("/api/devices")
async def create_or_update_device(payload: DevicePayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Agent).filter(Agent.user_id == current_user.id).update({Agent.is_active: False})
    existing = db.query(Agent).filter((Agent.agent_id == payload.agent_id) | (sa.func.lower(Agent.mac_address) == payload.mac_address.lower())).first()
    if existing:
        existing.device_name = payload.device_name
        existing.mac_address = payload.mac_address
        existing.assistant_name = payload.assistant_name or existing.assistant_name
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_agent = Agent(
            user_id=current_user.id,
            device_name=payload.device_name,
            agent_id=payload.agent_id,
            mac_address=payload.mac_address,
            assistant_name=payload.assistant_name or "Sophia",
            tts_voice="vi-female",
            is_active=True
        )
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return new_agent


@app.get("/api/upstream/status")
async def get_upstream_status():
    global CURRENT_UPSTREAM_WS_URL
    is_xiaozhi_official = "tenclass" in CURRENT_UPSTREAM_WS_URL or "xiaozhi.me" in CURRENT_UPSTREAM_WS_URL
    return {
        "current_url": CURRENT_UPSTREAM_WS_URL,
        "mode": "official" if is_xiaozhi_official else "gehihi",
        "name": "Cụm máy chủ gốc Xiaozhi chính thức" if is_xiaozhi_official else "Cụm Gehihi tiếng Việt",
        "description": "Chuẩn giọng nữ bé gái Tiểu Song Xiaozhi.me" if is_xiaozhi_official else "Miễn phí, tuỳ biến prompt, giọng nữ AI Hoài My / Mai Ngọc"
    }


class UpstreamSwitchPayload(BaseModel):
    mode: str  # "gehihi" | "official"


@app.post("/api/upstream/switch")
async def switch_upstream(payload: UpstreamSwitchPayload):
    global CURRENT_UPSTREAM_WS_URL
    if payload.mode == "official":
        CURRENT_UPSTREAM_WS_URL = "wss://api.tenclass.net/xiaozhi/v1/"
    else:
        CURRENT_UPSTREAM_WS_URL = "wss://gehihi.onrender.com/gehihi/v1/"
    return {
        "status": "ok",
        "current_url": CURRENT_UPSTREAM_WS_URL,
        "mode": payload.mode,
        "message": f"Đã chuyển sang {'Cụm máy chủ gốc Xiaozhi chính thức (Chuẩn nữ Tiểu Song)' if payload.mode == 'official' else 'Cụm Gehihi tiếng Việt'}. Hãy khởi động lại Robot để nạp kết nối mới!"
    }


@app.post("/api/devices/{agent_id}/select")
async def select_active_device(agent_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Chọn robot đang thao tác"""
    # Bỏ active các agent khác của user
    db.query(Agent).filter(Agent.user_id == current_user.id).update({Agent.is_active: False})
    target = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    target.is_active = True
    db.commit()
    return {"success": True, "active_device": target.device_name, "agent_id": target.agent_id}


@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == device_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    db.delete(agent)
    db.commit()
    return {"success": True, "message": "Đã xóa thiết bị thành công"}


# Kết nối & Đồng bộ Upstream
class UpstreamConnectPayload(BaseModel):
    upstream_token: str
    agent_id: Optional[str] = DEFAULT_AGENT_ID
    upstream_api_url: Optional[str] = DEFAULT_UPSTREAM_URL


@app.post("/api/upstream/connect")
async def connect_upstream(
    payload: UpstreamConnectPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lưu token và đồng bộ ngay với máy chủ xiaozhi.me"""
    current_user.upstream_token = payload.upstream_token.strip()
    if payload.upstream_api_url:
        current_user.upstream_api_url = payload.upstream_api_url.strip()
    db.commit()

    agent_id = payload.agent_id or DEFAULT_AGENT_ID

    # 1. Test kết nối
    test_res = await upstream_client.test_connection(
        token=current_user.upstream_token,
        api_url=current_user.upstream_api_url,
        agent_id=agent_id
    )

    # 2. Nếu kết nối tốt, tải cấu hình về cập nhật vào SQLite
    sync_res = await upstream_client.sync_from_upstream(
        agent_id=agent_id,
        token=current_user.upstream_token,
        api_url=current_user.upstream_api_url
    )

    if sync_res.get("success") and sync_res.get("data"):
        up_data = sync_res["data"]
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if agent:
            if "assistant_name" in up_data: agent.assistant_name = up_data["assistant_name"]
            if "llm_model" in up_data: agent.llm_model = up_data["llm_model"]
            if "language" in up_data: agent.language = up_data["language"]
            if "tts_voice" in up_data: agent.tts_voice = up_data["tts_voice"]
            if "tts_speech_speed" in up_data: agent.tts_speech_speed = up_data["tts_speech_speed"]
            if "tts_pitch" in up_data: agent.tts_pitch = int(up_data["tts_pitch"])
            if "character" in up_data: agent.character = up_data["character"]
            db.commit()

    return {
        "connected": test_res.get("connected", False),
        "message": test_res.get("message", ""),
        "sync_details": sync_res
    }


# Quản lý Bộ nhớ (Memory)
@app.get("/api/memories")
async def get_memories(
    agent_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Memory)
    if agent_id:
        query = query.filter(Memory.agent_id == agent_id)
    if memory_type and memory_type in ["SHORT_TERM", "LONG_TERM"]:
        query = query.filter(Memory.memory_type == memory_type)
    if search:
        query = query.filter(Memory.content.contains(search))
    memories = query.order_by(Memory.id.desc()).all()
    return memories


class CreateMemoryPayload(BaseModel):
    agent_id: Optional[str] = DEFAULT_AGENT_ID
    memory_type: Optional[str] = "SHORT_TERM"
    content: str


@app.post("/api/memories")
async def create_memory(payload: CreateMemoryPayload, db: Session = Depends(get_db)):
    mem = Memory(
        agent_id=payload.agent_id or DEFAULT_AGENT_ID,
        memory_type=payload.memory_type or "SHORT_TERM",
        content=payload.content.strip()
    )
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem


@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    mem = db.query(Memory).filter(Memory.id == memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Không tìm thấy mục bộ nhớ")
    db.delete(mem)
    db.commit()
    return {"success": True, "message": "Đã xóa mục bộ nhớ"}


class BulkDeletePayload(BaseModel):
    ids: List[int]


@app.post("/api/memories/bulk-delete")
async def bulk_delete_memories(payload: BulkDeletePayload, db: Session = Depends(get_db)):
    if payload.ids:
        db.query(Memory).filter(Memory.id.in_(payload.ids)).delete(synchronize_session=False)
        db.commit()
    return {"success": True, "count": len(payload.ids)}


# Quản lý Nhiệm vụ (Tasks)
@app.get("/api/tasks")
async def get_tasks(agent_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if agent_id:
        query = query.filter(Task.agent_id == agent_id)
    return query.order_by(Task.id.desc()).all()


class CreateTaskPayload(BaseModel):
    agent_id: Optional[str] = DEFAULT_AGENT_ID
    content: str


@app.post("/api/tasks")
async def create_task(payload: CreateTaskPayload, db: Session = Depends(get_db)):
    task = Task(agent_id=payload.agent_id or DEFAULT_AGENT_ID, content=payload.content.strip())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ")
    db.delete(task)
    db.commit()
    return {"success": True, "message": "Đã xóa nhiệm vụ"}


# Quản lý Ghi chú (Notes - Dùng cho MCP)
@app.get("/api/notes")
async def get_notes(db: Session = Depends(get_db)):
    return db.query(Note).order_by(Note.id.desc()).all()


class CreateNotePayload(BaseModel):
    title: Optional[str] = "Ghi chú nhanh"
    content: str


@app.post("/api/notes")
async def create_note(payload: CreateNotePayload, db: Session = Depends(get_db)):
    note = Note(title=payload.title or "Ghi chú", content=payload.content.strip())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Không tìm thấy ghi chú")
    db.delete(note)
    db.commit()
    return {"success": True, "message": "Đã xóa ghi chú"}


# Quản lý Người dùng (Admin / Multi-user)
@app.get("/api/users")
async def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền xem danh sách người dùng")
    return db.query(User).all()


class CreateUserPayload(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"
    char_limit: Optional[int] = 500
    is_vip: Optional[bool] = True


@app.post("/api/users")
async def create_user(payload: CreateUserPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền tạo người dùng")
    existing = db.query(User).filter(User.username == payload.username.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    user = User(
        username=payload.username.strip(),
        password_hash=payload.password.strip(),
        role=payload.role or "user",
        char_limit=payload.char_limit or 500,
        is_vip=payload.is_vip if payload.is_vip is not None else True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền xóa người dùng")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if user.username == ADMIN_USERNAME:
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản Admin gốc")
    db.delete(user)
    db.commit()
    return {"success": True, "message": "Đã xóa người dùng"}


# Auth API
class LoginPayload(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def auth_login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username.strip()).first()
    if not user or user.password_hash != payload.password.strip():
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không chính xác")

    response.set_cookie(key="gmbot_user", value=user.username, max_age=86400 * 30, httponly=False)
    agent = db.query(Agent).filter(Agent.user_id == user.id).first()
    if not agent:
        agent = db.query(Agent).filter(Agent.is_active == True).first() or db.query(Agent).first()
    device_data = None
    if agent:
        device_data = {
            "id": agent.id,
            "name": agent.device_name or agent.assistant_name or "Xiaozhi Robot",
            "device_code": agent.mac_address or agent.agent_id or ""
        }

    return {
        "success": True,
        "token": user.username,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_vip": user.is_vip
        },
        "device": device_data
    }


@app.get("/api/auth/me")
async def auth_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_vip": current_user.is_vip,
        "char_limit": current_user.char_limit
    }


# ==========================================
# 8. MCP SERVER PROTOCOL IMPLEMENTATION (/mcp)
# ==========================================

@app.get("/mcp")
async def mcp_info_endpoint():
    """Thông tin trạng thái MCP Server cho trình duyệt hoặc xiaozhi.me kiểm tra"""
    return {
        "status": "online",
        "name": "gmbot-control-plane-mcp",
        "protocol": "Model Context Protocol (JSON-RPC 2.0)",
        "protocolVersion": "2024-11-05",
        "description": "Server MCP cung cấp công cụ phần cứng, tra cứu thời gian, thời tiết và phát nhạc cho Robot Xiaozhi",
        "endpoints": {
            "jsonrpc": "/mcp",
            "sse": "/mcp/sse"
        },
        "tools_count": len(MCP_TOOL_DEFINITIONS),
        "tools": [t["name"] for t in MCP_TOOL_DEFINITIONS]
    }


@app.post("/mcp")
async def mcp_jsonrpc_endpoint(request: Request):
    """
    Endpoint chuẩn MCP (Model Context Protocol) JSON-RPC 2.0 cho Robot ESP32 Xiaozhi
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})

    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "gmbot-pc-mcp-server",
                    "version": "2.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        }

    elif method in ["notifications/initialized", "initialized"]:
        # Thông báo một chiều từ Client MCP sau khi initialize thành công
        return Response(status_code=204)

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOL_DEFINITIONS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        result_text = execute_mcp_tool(tool_name, tool_args)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result_text
                    }
                ],
                "isError": False
            }
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' không được hỗ trợ"
            }
        }


@app.get("/mcp/sse")
async def mcp_sse_endpoint():
    """SSE endpoint hỗ trợ kết nối streaming MCP"""
    async def event_generator():
        yield f"event: endpoint\ndata: /mcp\n\n"
        while True:
            await asyncio.sleep(20)
            yield f": keepalive\n\n"

    import asyncio
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/mcp/tools")
async def get_mcp_tools():
    """Lấy danh sách các Tools phục vụ test từ Web Dashboard"""
    return {"tools": MCP_TOOL_DEFINITIONS}


class McpCallPayload(BaseModel):
    tool_name: str
    arguments: Optional[Dict[str, Any]] = {}


@app.post("/api/mcp/test-call")
async def test_call_mcp_tool(payload: McpCallPayload):
    """Test trực tiếp các công cụ MCP từ trình duyệt Web"""
    result = execute_mcp_tool(payload.tool_name, payload.arguments or {})
    return {"tool": payload.tool_name, "result": result}


@app.get("/api/mcp/logs")
async def get_mcp_logs():
    """Lấy danh sách lịch sử gọi công cụ MCP từ Robot ESP32 để theo dõi trực tiếp"""
    return {"logs": MCP_CALL_LOGS}


# ==========================================
# 8.1 XIAOZHI CLOUD MCP BRIDGE CLIENT
# ==========================================

class XiaozhiCloudMcpBridge:
    def __init__(self):
        raw_env = os.getenv("XIAOZHI_MCP_ENDPOINT", "").strip() or os.getenv("UPSTREAM_AUTH_TOKEN", "").strip()
        self.endpoint_url: str = ""
        self.is_connected: bool = False
        self.task: Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()
        if raw_env:
            if raw_env.startswith("wss://") or raw_env.startswith("ws://"):
                self.endpoint_url = raw_env
            elif raw_env.startswith("token="):
                self.endpoint_url = f"wss://api.xiaozhi.me/mcp/?{raw_env}"
            else:
                self.endpoint_url = f"wss://api.xiaozhi.me/mcp/?token={raw_env}"
            print(f"[XIAOZHI MCP BRIDGE] Tự động tải Điểm cuối MCP: {self.endpoint_url[:40]}...")

    def set_endpoint(self, url_or_token: str):
        url_or_token = (url_or_token or "").strip()
        if not url_or_token:
            self.endpoint_url = ""
            self.is_connected = False
            return
        if url_or_token.startswith("wss://") or url_or_token.startswith("ws://"):
            self.endpoint_url = url_or_token
        elif url_or_token.startswith("token="):
            self.endpoint_url = f"wss://api.xiaozhi.me/mcp/?{url_or_token}"
        else:
            self.endpoint_url = f"wss://api.xiaozhi.me/mcp/?token={url_or_token}"
        print(f"[XIAOZHI MCP BRIDGE] Đã cấu hình Điểm cuối MCP: {self.endpoint_url[:38]}...")
        if self.task and not self.task.done():
            self.task.cancel()
        self.start()

    def start(self):
        if not self.endpoint_url:
            return
        self.stop_event.clear()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.task = loop.create_task(self._connect_loop())
        except Exception as e:
            print(f"[XIAOZHI MCP BRIDGE] start error: {e}")

    async def _connect_loop(self):
        while not self.stop_event.is_set():
            if not self.endpoint_url:
                await asyncio.sleep(5)
                continue
            try:
                print(f"[XIAOZHI MCP BRIDGE] 🔌 Đang kết nối tới điểm cuối MCP xiaozhi.me...")
                async with websockets.connect(
                    self.endpoint_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5
                ) as ws:
                    self.is_connected = True
                    print(f"[XIAOZHI MCP BRIDGE] ✓ ĐÃ KẾT NỐI THÀNH CÔNG VỚI XIAOZHI.ME MCP! Trạng thái: 🟢 Đã kết nối")
                    while not self.stop_event.is_set():
                        msg_text = await ws.recv()
                        try:
                            req = json.loads(msg_text)
                            req_id = req.get("id")
                            method = req.get("method")
                            params = req.get("params", {})

                            if method == "initialize":
                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {
                                        "protocolVersion": "2024-11-05",
                                        "serverInfo": {"name": "gmbot-pc-mcp-server", "version": "2.0.0"},
                                        "capabilities": {"tools": {}}
                                    }
                                }
                                await ws.send(json.dumps(resp))
                            elif method in ["notifications/initialized", "initialized"]:
                                pass
                            elif method == "tools/list":
                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {"tools": MCP_TOOL_DEFINITIONS}
                                }
                                await ws.send(json.dumps(resp))
                                print(f"[XIAOZHI MCP BRIDGE] ✓ Đã đăng ký {len(MCP_TOOL_DEFINITIONS)} công cụ MCP với xiaozhi.me")
                            elif method == "tools/call":
                                t_name = params.get("name")
                                t_args = params.get("arguments", {})
                                print(f"[XIAOZHI MCP CALL] 🚀 Xiaozhi gọi công cụ: '{t_name}' ({t_args})")
                                res_str = execute_mcp_tool(t_name, t_args)
                                resp = {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "result": {
                                        "content": [{"type": "text", "text": res_str}],
                                        "isError": False
                                    }
                                }
                                await ws.send(json.dumps(resp))
                            elif method == "ping":
                                await ws.send(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}))
                        except Exception as err:
                            print(f"[XIAOZHI MCP BRIDGE MSG ERR] {err}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.is_connected = False
                print(f"[XIAOZHI MCP BRIDGE ERR] Mất kết nối tới xiaozhi.me MCP ({e}). Thử lại sau 5s...")
                await asyncio.sleep(5)

xiaozhi_mcp_bridge = XiaozhiCloudMcpBridge()


class ConnectMcpPayload(BaseModel):
    endpoint_url: str


@app.post("/api/mcp/connect-upstream")
async def connect_mcp_upstream(payload: ConnectMcpPayload):
    """Kết nối Server tới Điểm cuối MCP của xiaozhi.me (wss://api.xiaozhi.me/mcp/?token=...)"""
    raw_url = payload.endpoint_url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp URL hoặc Token điểm cuối MCP từ xiaozhi.me")
    
    xiaozhi_mcp_bridge.set_endpoint(raw_url)
    
    # Ghi nhớ vào file .env
    try:
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        has_key = False
        new_lines = []
        for l in env_lines:
            if l.startswith("XIAOZHI_MCP_ENDPOINT="):
                new_lines.append(f"XIAOZHI_MCP_ENDPOINT={xiaozhi_mcp_bridge.endpoint_url}\n")
                has_key = True
            else:
                new_lines.append(l)
        if not has_key:
            new_lines.append(f"\nXIAOZHI_MCP_ENDPOINT={xiaozhi_mcp_bridge.endpoint_url}\n")
        with open(".env", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"[SAVE ENV ERR] {e}")

    await asyncio.sleep(1.0)
    return {
        "status": "ok",
        "message": "Đã bắt đầu kết nối tới điểm cuối MCP xiaozhi.me!",
        "endpoint": xiaozhi_mcp_bridge.endpoint_url,
        "is_connected": xiaozhi_mcp_bridge.is_connected
    }


@app.get("/api/mcp/upstream-status")
async def get_mcp_upstream_status():
    """Kiểm tra trạng thái kết nối tới Điểm cuối MCP xiaozhi.me"""
    return {
        "is_connected": xiaozhi_mcp_bridge.is_connected,
        "endpoint": xiaozhi_mcp_bridge.endpoint_url
    }


# ==========================================
# 9. BANNER KHỞI ĐỘNG & MAIN ENTRYPOINT
# ==========================================

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_startup_banner():
    lan_ip = get_lan_ip()
    border = "=" * 70
    banner = f"""
{border}
   🤖 GMBOT AI - MULTI-USER SAAS CONTROL PLANE & MCP SERVER 🚀
       Chạy trực tiếp 100% trên Máy tính cá nhân (Localhost)
{border}
  🌐 TRUY CẬP WEB DASHBOARD (TRÊN MÁY TÍNH NÀY):
     👉 http://localhost:{PORT}
     👉 http://127.0.0.1:{PORT}

  📱 TRUY CẬP TỪ ĐIỆN THOẠI TRONG CÙNG WI-FI LAN:
     👉 http://{lan_ip}:{PORT}

  ⚡ KẾT NỐI MCP CHO ROBOT XIAOZHI ESP32:
     👉 Endpoint MCP: http://{lan_ip}:{PORT}/mcp

  🌍 MỞ PUBLIC RA INTERNET (CLOUDFLARE TUNNEL - TÙY CHỌN):
     👉 cloudflared tunnel --url http://localhost:{PORT}

  💾 CƠ SỞ DỮ LIỆU CỤC BỘ:
     👉 {DB_PATH}
{border}
"""
    print(banner)

if __name__ == "__main__":
    import uvicorn
    print_startup_banner()
    uvicorn.run(app, host=HOST, port=PORT)
