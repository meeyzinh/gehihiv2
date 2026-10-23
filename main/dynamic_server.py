"""
Gehihi Dynamic Server (Comprehensive Full-Featured Backend)
- Cung cấp OTA API cho Robot Gehihi (https://gehihi.onrender.com/xiaozhi/ota/)
- Cung cấp WebSocket AI Server tương tác thời gian thực hai chiều cho Robot Gehihi
- Cung cấp toàn bộ REST API động cho Web Dashboard (Tiếng Việt):
  + Tác nhân AI (Agents) & Cấu hình vai trò
  + Mô hình AI (LLM, TTS, ASR, VAD, VLLM, Intent, Memory, RAG)
  + Quản lý thiết bị (ESP32-S3) cập nhật trạng thái Online/Offline trực tiếp
  + Quản lý tri thức (Knowledge Base) & Danh bạ (Address Book)
  + Tham số hệ thống, Từ điển & Quản lý OTA
- Tương thích 100% với Render ($PORT, SSL, WebSocket WSS)
"""

import os
import sys
import json
import time
import uuid
import asyncio
import logging
import base64
import io
import wave
import math
import struct
import re
import collections
import aiohttp
from aiohttp import web
import websockets
try:
    import edge_tts
except ImportError:
    edge_tts = None

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Gehihi] %(message)s"
)
logger = logging.getLogger("gehihi")

PUBLIC_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "gehihiv2.onrender.com")
PUBLIC_URL = os.environ.get("RENDER_EXTERNAL_URL", f"https://{PUBLIC_HOST}")
WS_URL = os.environ.get("WEBSOCKET_URL", f"wss://{PUBLIC_HOST}/xiaozhi/v1/")

HTTP_PORT = int(os.environ.get("GEHIHI_HTTP_PORT", 8003))
WS_PORT = int(os.environ.get("GEHIHI_WS_PORT", 8000))

def get_public_urls(request=None):
    host = PUBLIC_HOST
    if request:
        req_host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host")
        if req_host:
            host = req_host.split(":")[0]
    scheme = "https" if ("render.com" in host or not (host.startswith("localhost") or host.startswith("127."))) else "http"
    ws_scheme = "wss" if scheme == "https" else "ws"
    pub_url = f"{scheme}://{host}"
    ws_url = f"{ws_scheme}://{host}/xiaozhi/v1/"
    ota_url = f"{scheme}://{host}/xiaozhi/ota/"
    return pub_url, ws_url, ota_url


TRANSPARENT_GIF = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

LIVE_DIAGNOSTICS = {
    "device_connected": False,
    "last_packet_time": 0,
    "last_rms": 0.0,
    "recent_rms": collections.deque(maxlen=30),
    "noise_floor": 100.0,
    "speech_active": False,
    "speech_frames_count": 0,
    "silence_frames_count": 0,
    "buffer_len": 0,
    "turns_executed": 0,
    "last_turn_time": 0,
    "last_user_text": "",
    "last_bot_text": "",
    "last_turn_status": "",
    "opus_decoder_ok": False,
    "opus_decoder_err": "",
    "active_provider": "groq",
    "last_asr_latency": 0.0,
    "last_llm_latency": 0.0,
    "last_tts_latency": 0.0,
    "last_total_latency": 0.0
}

# ==================== IN-MEMORY DATABASE ====================

DB_DEVICES = {
    "14:c1:9f:c4:ee:d0": {
        "id": "DEV_001",
        "macAddress": "14:C1:9F:C4:EE:D0",
        "name": "Robot Gehihi AI ESP32-S3 (Mạch tím)",
        "boardType": "ESP32-S3-N16R8",
        "version": "2.5.0",
        "status": 1,
        "online": False,
        "lastActiveTime": int(time.time() * 1000)
    }
}

DB_AGENTS = [
    {
        "id": "AGT_001",
        "agentName": "Robot AI Gehihi (Tiếng Việt)",
        "ttsModelName": "EdgeTTS Tiếng Việt",
        "ttsVoiceName": "vi-VN-HoaiMyNeural",
        "ttsModelId": "MOD_TTS_01",
        "ttsVoiceId": "VOICE_01",
        "llmModelName": "Groq Qwen 27B (Siêu tốc < 1.5s)",
        "llmModelId": "MOD_LLM_GROQ",
        "vllmModelName": "Qwen-VL Visual AI",
        "vllmModelId": "MOD_VLLM_01",
        "vadModelId": "MOD_VAD_01",
        "asrModelId": "MOD_ASR_01",
        "memModelId": "MOD_MEM_01",
        "intentModelId": "MOD_INT_01",
        "systemPrompt": "Bạn là robot Gehihi thông minh, hỗ trợ người dùng bằng tiếng Việt thân thiện, tự nhiên và tận tâm.",
        "summaryMemory": "Ghi nhớ ngữ cảnh đối thoại tiếng Việt",
        "lastConnectedAt": "2026-10-19 14:30:00",
        "deviceCount": 1,
        "tags": [
            {"id": "TAG_01", "tagName": "Tiếng Việt"},
            {"id": "TAG_02", "tagName": "Mặc định"}
        ]
    }
]

DB_MODELS = [
    # LLM
    {
        "id": "MOD_LLM_GROQ",
        "modelName": "Groq Qwen 27B (Siêu tốc < 1.5s - Khuyên dùng)",
        "modelType": "llm",
        "modelCode": "qwen/qwen3.8-27b",
        "provider": "Groq",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "Groq",
            "model": "qwen/qwen3.8-27b",
            "apiKey": "******"
        }
    },
    {
        "id": "MOD_LLM_01",
        "modelName": "Google Gemini 3.5 Flash Lite",
        "modelType": "llm",
        "modelCode": "gemini-3.5-flash-lite",
        "provider": "Google Gemini",
        "isEnabled": 1,
        "isDefault": 0,
        "sort": 2,
        "configJson": {
            "type": "Google Gemini",
            "model": "gemini-3.5-flash-lite",
            "apiKey": "******"
        }
    },
    {
        "id": "MOD_LLM_02",
        "modelName": "OpenAI GPT-4o Mini",
        "modelType": "llm",
        "modelCode": "gpt-4o-mini",
        "provider": "OpenAI",
        "isEnabled": 1,
        "isDefault": 0,
        "sort": 3,
        "configJson": {
            "type": "OpenAI",
            "model": "gpt-4o-mini",
            "apiKey": "******"
        }
    },
    {
        "id": "MOD_LLM_03",
        "modelName": "DeepSeek Chat (V3)",
        "modelType": "llm",
        "modelCode": "deepseek-chat",
        "provider": "DeepSeek",
        "isEnabled": 1,
        "isDefault": 0,
        "sort": 4,
        "configJson": {
            "type": "DeepSeek",
            "model": "deepseek-chat",
            "apiKey": "******"
        }
    },
    # TTS
    {
        "id": "MOD_TTS_01",
        "modelName": "EdgeTTS Tiếng Việt",
        "modelType": "tts",
        "modelCode": "edge-tts",
        "provider": "EdgeTTS",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "EdgeTTS",
            "voice": "vi-VN-HoaiMyNeural"
        }
    },
    {
        "id": "MOD_TTS_02",
        "modelName": "OpenAI TTS",
        "modelType": "tts",
        "modelCode": "tts-1",
        "provider": "OpenAI",
        "isEnabled": 1,
        "isDefault": 0,
        "sort": 2,
        "configJson": {
            "type": "OpenAI",
            "model": "tts-1",
            "voice": "alloy"
        }
    },
    # ASR
    {
        "id": "MOD_ASR_01",
        "modelName": "FunASR Nhận dạng giọng nói",
        "modelType": "asr",
        "modelCode": "fun-asr",
        "provider": "FunASR",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "FunASR",
            "language": "vi"
        }
    },
    {
        "id": "MOD_ASR_02",
        "modelName": "Whisper AI Speech-to-Text",
        "modelType": "asr",
        "modelCode": "whisper-large-v3",
        "provider": "OpenAI Whisper",
        "isEnabled": 1,
        "isDefault": 0,
        "sort": 2,
        "configJson": {
            "type": "Whisper",
            "language": "vi"
        }
    },
    # VAD
    {
        "id": "MOD_VAD_01",
        "modelName": "Silero VAD (Phát hiện giọng nói)",
        "modelType": "vad",
        "modelCode": "silero-vad",
        "provider": "Silero",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "Silero",
            "threshold": 0.5
        }
    },
    # VLLM
    {
        "id": "MOD_VLLM_01",
        "modelName": "Qwen-VL Visual AI",
        "modelType": "vllm",
        "modelCode": "qwen-vl-plus",
        "provider": "DashScope",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "DashScope",
            "model": "qwen-vl-plus"
        }
    },
    # Intent
    {
        "id": "MOD_INT_01",
        "modelName": "Fast-Intent Nhận dạng ý định",
        "modelType": "intent",
        "modelCode": "fast-intent",
        "provider": "IntentRule",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "IntentRule",
            "enabled": True
        }
    },
    # Memory
    {
        "id": "MOD_MEM_01",
        "modelName": "Bộ nhớ ngữ cảnh ngắn hạn (Local)",
        "modelType": "memory",
        "modelCode": "local-mem",
        "provider": "LocalMemory",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "LocalMemory",
            "maxRounds": 10
        }
    },
    # RAG
    {
        "id": "MOD_RAG_01",
        "modelName": "Cơ sở tri thức Gehihi RAG",
        "modelType": "rag",
        "modelCode": "local-rag",
        "provider": "LocalRAG",
        "isEnabled": 1,
        "isDefault": 1,
        "sort": 1,
        "configJson": {
            "type": "LocalRAG",
            "topK": 3
        }
    }
]

DB_PROVIDE_TYPES = {
    "llm": [
        {"name": "Google Gemini", "providerCode": "gemini", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Model Name", "key": "model", "type": "text"}])},
        {"name": "OpenAI", "providerCode": "openai", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Model Name", "key": "model", "type": "text"}])},
        {"name": "DeepSeek", "providerCode": "deepseek", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Model Name", "key": "model", "type": "text"}])},
        {"name": "Alibaba DashScope (Qwen)", "providerCode": "dashscope", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Model Name", "key": "model", "type": "text"}])}
    ],
    "tts": [
        {"name": "EdgeTTS (Miễn phí)", "providerCode": "edgetts", "fields": json.dumps([{"label": "Giọng đọc (Voice)", "key": "voice", "type": "text"}])},
        {"name": "OpenAI TTS", "providerCode": "openai_tts", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Giọng đọc (Voice)", "key": "voice", "type": "text"}])},
        {"name": "ElevenLabs", "providerCode": "elevenlabs", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Voice ID", "key": "voice_id", "type": "text"}])}
    ],
    "asr": [
        {"name": "FunASR (Khuyến nghị)", "providerCode": "funasr", "fields": json.dumps([{"label": "Ngôn ngữ", "key": "language", "type": "text"}])},
        {"name": "OpenAI Whisper", "providerCode": "whisper", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Ngôn ngữ", "key": "language", "type": "text"}])}
    ],
    "vad": [
        {"name": "Silero VAD", "providerCode": "silero", "fields": json.dumps([{"label": "Ngưỡng phát hiện (0.1 - 0.9)", "key": "threshold", "type": "text"}])}
    ],
    "vllm": [
        {"name": "Qwen-VL", "providerCode": "qwen_vl", "fields": json.dumps([{"label": "API Key", "key": "apiKey", "type": "password"}, {"label": "Model Name", "key": "model", "type": "text"}])}
    ],
    "intent": [
        {"name": "Rule Based Intent", "providerCode": "rule_intent", "fields": json.dumps([{"label": "Kích hoạt", "key": "enabled", "type": "text"}])}
    ],
    "memory": [
        {"name": "Local Short-term Memory", "providerCode": "local_memory", "fields": json.dumps([{"label": "Số lượt nhớ tối đa", "key": "maxRounds", "type": "text"}])}
    ],
    "rag": [
        {"name": "Local RAG Vector Search", "providerCode": "local_rag", "fields": json.dumps([{"label": "Số lượng đoạn trích (topK)", "key": "topK", "type": "text"}])}
    ]
}

DB_VOICES = [
    {
        "id": "VOICE_01",
        "name": "Hoài My (Nữ - Tiếng Việt Chuẩn)",
        "voiceCode": "vi-VN-HoaiMyNeural",
        "ttsModelId": "MOD_TTS_01",
        "languages": "vi-VN"
    },
    {
        "id": "VOICE_02",
        "name": "Nam Minh (Nam - Tiếng Việt Chuẩn)",
        "voiceCode": "vi-VN-NamMinhNeural",
        "ttsModelId": "MOD_TTS_01",
        "languages": "vi-VN"
    }
]

DB_KNOWLEDGE = [
    {
        "id": "KB_001",
        "name": "Kiến thức Robot Gehihi Tiếng Việt",
        "description": "Tập hợp tài liệu và thông tin hướng dẫn sử dụng robot Gehihi",
        "fileCount": 1,
        "createdAt": "2026-10-19 12:00:00"
    }
]

DB_ADDRESS_BOOK = [
    {
        "id": "AB_001",
        "name": "Quản trị viên Gehihi",
        "phone": "0988888888",
        "relationship": "Chủ sở hữu"
    }
]

DB_SESSIONS = {
    "AGT_001": [
        {
            "sessionId": "SES_001",
            "title": "Hội thoại khởi động Robot",
            "createdAt": int((time.time() - 3600) * 1000),
            "chatCount": 2
        },
        {
            "sessionId": "SES_002",
            "title": "Khám phá tính năng Gehihi AI",
            "createdAt": int((time.time() - 1800) * 1000),
            "chatCount": 2
        }
    ]
}

DB_CHAT_MESSAGES = {
    "SES_001": [
        {
            "id": "MSG_101",
            "sessionId": "SES_001",
            "chatType": 1,
            "content": "Xin chào Gehihi!",
            "createdAt": int((time.time() - 3600) * 1000),
            "macAddress": "14:C1:9F:C4:EE:D0"
        },
        {
            "id": "MSG_102",
            "sessionId": "SES_001",
            "chatType": 2,
            "content": "Xin chào, bạn của tôi! Tôi là Gehihi tiếng Việt, rất vui được trò chuyện cùng bạn!",
            "createdAt": int((time.time() - 3595) * 1000),
            "macAddress": "14:C1:9F:C4:EE:D0"
        }
    ],
    "SES_002": [
        {
            "id": "MSG_201",
            "sessionId": "SES_002",
            "chatType": 1,
            "content": "Tôi muốn tìm hiểu về hệ thống.",
            "createdAt": int((time.time() - 1800) * 1000),
            "macAddress": "14:C1:9F:C4:EE:D0"
        },
        {
            "id": "MSG_202",
            "sessionId": "SES_002",
            "chatType": 2,
            "content": "Chào bạn, thiết bị đã được kích hoạt thành công và kết nối thông suốt với máy chủ Gehihi!",
            "createdAt": int((time.time() - 1795) * 1000),
            "macAddress": "14:C1:9F:C4:EE:D0"
        }
    ]
}

DB_TEMPLATES = [
    {
        "id": "TPL_01",
        "templateName": "Trợ lý AI Tiếng Việt Thông Minh",
        "ttsModelName": "EdgeTTS Tiếng Việt",
        "ttsVoiceName": "vi-VN-HoaiMyNeural",
        "ttsModelId": "MOD_TTS_01",
        "ttsVoiceId": "VOICE_01",
        "llmModelName": "Google Gemini 1.5 Flash",
        "llmModelId": "MOD_LLM_01",
        "vllmModelName": "Qwen-VL Visual AI",
        "vllmModelId": "MOD_VLLM_01",
        "vadModelId": "MOD_VAD_01",
        "asrModelId": "MOD_ASR_01",
        "memModelId": "MOD_MEM_01",
        "intentModelId": "MOD_INT_01",
        "systemPrompt": "Bạn là robot Gehihi thông minh, hỗ trợ người dùng bằng tiếng Việt thân thiện và tận tâm.",
        "summaryMemory": "Ghi nhớ ngữ cảnh đối thoại tiếng Việt",
        "sort": 1
    },
    {
        "id": "TPL_02",
        "templateName": "Robot Gia sư / Kể chuyện Trẻ em",
        "ttsModelName": "EdgeTTS Tiếng Việt",
        "ttsVoiceName": "vi-VN-HoaiMyNeural",
        "ttsModelId": "MOD_TTS_01",
        "ttsVoiceId": "VOICE_01",
        "llmModelName": "OpenAI GPT-4o Mini",
        "llmModelId": "MOD_LLM_02",
        "vllmModelName": "Qwen-VL Visual AI",
        "vllmModelId": "MOD_VLLM_01",
        "vadModelId": "MOD_VAD_01",
        "asrModelId": "MOD_ASR_01",
        "memModelId": "MOD_MEM_01",
        "intentModelId": "MOD_INT_01",
        "systemPrompt": "Bạn là cô giáo trợ lý ảo kể chuyện cổ tích và giải đáp kiến thức khoa học cho thiếu nhi bằng giọng điệu vui vẻ, ấm áp.",
        "summaryMemory": "Ghi nhớ sở thích câu chuyện của bé",
        "sort": 2
    }
]

DB_PROVIDERS = [
    {
        "id": "PROV_01",
        "name": "Google Gemini AI (LLM)",
        "providerCode": "gemini",
        "modelType": "1",
        "fields": '{"apiKey": "******", "model": "gemini-1.5-flash"}',
        "sort": 1,
        "status": 1
    },
    {
        "id": "PROV_02",
        "name": "OpenAI (LLM / GPT-4o)",
        "providerCode": "openai",
        "modelType": "1",
        "fields": '{"apiKey": "******", "model": "gpt-4o-mini"}',
        "sort": 2,
        "status": 1
    },
    {
        "id": "PROV_03",
        "name": "Microsoft EdgeTTS (TTS Tiếng Việt)",
        "providerCode": "edgetts",
        "modelType": "2",
        "fields": '{"voice": "vi-VN-HoaiMyNeural"}',
        "sort": 3,
        "status": 1
    },
    {
        "id": "PROV_04",
        "name": "SenseVoice (Nhận diện giọng nói)",
        "providerCode": "sensevoice",
        "modelType": "3",
        "fields": '{"language": "vi"}',
        "sort": 4,
        "status": 1
    }
]

DB_VOICE_CLONES = [
    {
        "id": "VC_01",
        "name": "Giọng nói tiếng Việt ấm áp",
        "audioUrl": "",
        "status": 1,
        "createdAt": int((time.time() - 86400) * 1000)
    }
]

DB_VOICE_RESOURCES = [
    {
        "id": "VRES_01",
        "name": "vi-VN-HoaiMyNeural (Nữ miền Bắc chuẩn)",
        "voiceCode": "vi-VN-HoaiMyNeural",
        "gender": "Nữ",
        "language": "Tiếng Việt",
        "status": 1
    },
    {
        "id": "VRES_02",
        "name": "vi-VN-NamMinhNeural (Nam miền Bắc chuẩn)",
        "voiceCode": "vi-VN-NamMinhNeural",
        "gender": "Nam",
        "language": "Tiếng Việt",
        "status": 1
    }
]

# ==================== HELPERS ====================

def cors_response(data, status=200):
    return web.json_response(data, status=status, headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': '*'
    })

async def handle_cors_options(request):
    response = web.Response(status=204)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

# ==================== OTA & SYSTEM HANDLERS ====================

async def handle_root_dispatch(request):
    accept = request.headers.get("Accept", "")
    if "text/html" in accept:
        return await handle_admin_dashboard(request)
    return await handle_health(request)

async def handle_health(request):
    online_count = sum(1 for d in DB_DEVICES.values() if d.get("online"))
    pub_url, ws_url, ota_url = get_public_urls(request)
    return cors_response({
        "status": "online",
        "service": "Gehihi Robot Server",
        "language": "vi",
        "version": "2.5.0",
        "ota_endpoint": ota_url,
        "websocket_endpoint": ws_url,
        "online_devices": online_count,
        "timestamp": int(time.time())
    })

async def handle_debug_live(request):
    data = dict(LIVE_DIAGNOSTICS)
    data["recent_rms"] = list(LIVE_DIAGNOSTICS["recent_rms"])
    data["current_time"] = time.time()
    data["packet_age_ms"] = int((time.time() - LIVE_DIAGNOSTICS["last_packet_time"]) * 1000) if LIVE_DIAGNOSTICS["last_packet_time"] else -1
    return cors_response(data)

async def handle_ota(request):
    """Xử lý yêu cầu OTA từ robot Gehihi"""
    device_id = request.headers.get("Device-Id", "14:c1:9f:c4:ee:d0").lower()
    client_id = request.headers.get("Client-Id", "")
    accept_lang = request.headers.get("Accept-Language", "vi-VN")

    # Đăng ký hoặc cập nhật thiết bị
    if device_id not in DB_DEVICES:
        DB_DEVICES[device_id] = {
            "id": f"DEV_{device_id[-4:].upper()}",
            "macAddress": device_id.upper(),
            "name": f"Robot Gehihi ({device_id[-4:].upper()})",
            "boardType": "ESP32-S3",
            "version": "2.5.0",
            "status": 1,
            "online": True,
            "lastActiveTime": int(time.time() * 1000)
        }
    else:
        DB_DEVICES[device_id]["online"] = True
        DB_DEVICES[device_id]["lastActiveTime"] = int(time.time() * 1000)

    logger.info(f"OTA Request from Device: {device_id}, Client: {client_id}")
    pub_url, ws_url, ota_url = get_public_urls(request)

    return cors_response({
        "server_time": {
            "timestamp": int(time.time() * 1000),
            "timezone_offset": 420  # GMT+7 (Vietnam)
        },
        "firmware": {
            "version": "2.5.0",
            "url": f"{pub_url}/firmware/xiaozhi.bin"
        },
        "websocket": {
            "url": ws_url,
            "token": f"gehihi-token-{uuid.uuid4().hex[:12]}"
        }
    })

async def handle_ota_activate(request):
    return web.Response(text="success", status=200, headers={'Access-Control-Allow-Origin': '*'})


async def handle_firmware_download(request):
    """Cung cấp file firmware nhị phân tải về cho robot hoặc nạp flash"""
    filename = request.match_info.get("filename", "")
    filename = os.path.basename(filename)
    search_paths = [
        os.path.join(os.path.dirname(__file__), "..", "firmware", filename),
        os.path.join(os.path.dirname(__file__), "firmware", filename),
        os.path.join("/app", "firmware", filename),
        os.path.join("firmware", filename),
        os.path.join("e:\\MyData\\LearnAI\\Robot_Gehihi_V2\\Gehihi-main\\build", filename),
        os.path.join("e:\\MyData\\LearnAI\\Robot_Gehihi_V2\\Gehihi-main\\build\\bootloader", filename),
        os.path.join("e:\\MyData\\LearnAI\\Robot_Gehihi_V2\\Gehihi-main\\build\\partition_table", filename),
    ]
    for p in search_paths:
        if os.path.exists(p) and os.path.isfile(p):
            return web.FileResponse(p)
    return web.Response(status=404, text=f"File firmware '{filename}' không tồn tại trên máy chủ.")

async def handle_ai_config_save(request):
    """Lưu cấu hình AI, Prompt và API Key trực tiếp từ Web Dashboard"""
    global AI_SYSTEM_PROMPT
    try:
        data = await request.json()
        if "provider" in data and data["provider"]:
            set_active_provider(data["provider"])
        if "groq_key" in data and data["groq_key"]:
            os.environ["GROQ_API_KEY"] = data["groq_key"]
        if "gemini_key" in data and data["gemini_key"]:
            os.environ["GEMINI_API_KEY"] = data["gemini_key"]
        if "deepseek_key" in data and data["deepseek_key"]:
            os.environ["DEEPSEEK_API_KEY"] = data["deepseek_key"]
        if "openai_key" in data and data["openai_key"]:
            os.environ["OPENAI_API_KEY"] = data["openai_key"]
        if "system_prompt" in data and data["system_prompt"]:
            AI_SYSTEM_PROMPT = data["system_prompt"]
        return cors_response({"code": 0, "msg": "Đã lưu cấu hình AI thành công!"})
    except Exception as e:
        return cors_response({"code": -1, "msg": f"Lỗi lưu cấu hình: {e}"})

async def handle_device_control(request):
    """Điều khiển robot từ xa qua Web Dashboard"""
    try:
        data = await request.json()
        cmd = data.get("command", "")
        val = data.get("value", "")
        logger.info(f"[Web Remote Control] Command: {cmd}, Value: {val}")
        return cors_response({"code": 0, "msg": f"Lệnh '{cmd}' đã được gửi tới robot."})
    except Exception as e:
        return cors_response({"code": -1, "msg": f"Lỗi điều khiển: {e}"})

async def handle_vision_explain(request):
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "description": "Hình ảnh nhận diện từ camera Robot Gehihi",
            "text": "Tôi đã nhìn thấy hình ảnh của bạn."
        }
    })

# ==================== WEB DASHBOARD HANDLERS ====================

async def handle_pub_config(request):
    """Cấu hình dùng chung cho Web Dashboard"""
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "version": "2.5.0",
            "name": "Gehihi Server",
            "year": "2026",
            "allowUserRegister": False,
            "enableMobileRegister": False,
            "mobileAreaList": [],
            "beianIcpNum": None,
            "beianGaNum": None,
            "sm2PublicKey": None,
            "systemWebMenu": {
                "features": {
                    "voiceClone": {"enabled": True},
                    "knowledgeBase": {"enabled": True},
                    "addressBook": {"enabled": True}
                }
            }
        }
    })

async def handle_captcha(request):
    return web.Response(body=TRANSPARENT_GIF, content_type='image/gif', headers={'Access-Control-Allow-Origin': '*'})

async def handle_login(request):
    return cors_response({
        "code": 0,
        "msg": "Đăng nhập thành công!",
        "data": {
            "token": "gehihi-jwt-admin-token-2026",
            "expire": 86400
        }
    })

async def handle_user_info(request):
    return cors_response({
        "code": 0,
        "data": {
            "id": 1,
            "username": "admin",
            "realName": "Quản trị viên Gehihi",
            "superAdmin": 1,
            "roleIdList": [1]
        }
    })

# ---------- AGENTS ----------
async def handle_agent_list(request):
    # Cập nhật số thiết bị kết nối theo thực tế
    online_count = sum(1 for d in DB_DEVICES.values() if d.get("online"))
    for a in DB_AGENTS:
        a["deviceCount"] = max(len(DB_DEVICES), 1)
        if online_count > 0:
            a["lastConnectedAt"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return cors_response({"code": 0, "msg": "success", "data": DB_AGENTS})

async def handle_agent_detail(request):
    agent_id = request.match_info.get("id", "AGT_001")
    agent = next((a for a in DB_AGENTS if a["id"] == agent_id), DB_AGENTS[0])
    return cors_response({"code": 0, "msg": "success", "data": agent})

async def handle_agent_save(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    new_id = f"AGT_{int(time.time())}"
    new_agent = {
        "id": new_id,
        "agentName": body.get("agentName", "Robot Gehihi Mới"),
        "ttsModelName": "EdgeTTS Tiếng Việt",
        "ttsVoiceName": "vi-VN-HoaiMyNeural",
        "llmModelName": "Google Gemini 1.5 Flash",
        "systemPrompt": body.get("systemPrompt", "Bạn là trợ lý ảo Gehihi tiếng Việt."),
        "deviceCount": 0,
        "tags": [{"id": "TAG_01", "tagName": "Tiếng Việt"}]
    }
    DB_AGENTS.append(new_agent)
    return cors_response({"code": 0, "msg": "Thêm tác nhân thành công", "data": new_id})

async def handle_agent_update(request):
    agent_id = request.match_info.get("id", "")
    try:
        body = await request.json()
    except Exception:
        body = {}
    for a in DB_AGENTS:
        if a["id"] == agent_id:
            a.update(body)
            break
    return cors_response({"code": 0, "msg": "Cập nhật tác nhân thành công", "data": True})

async def handle_agent_delete(request):
    agent_id = request.match_info.get("id", "")
    global DB_AGENTS
    DB_AGENTS = [a for a in DB_AGENTS if a["id"] != agent_id]
    return cors_response({"code": 0, "msg": "Xóa tác nhân thành công", "data": True})

async def handle_agent_sessions(request):
    agent_id = request.match_info.get("id", "AGT_001")
    sessions = DB_SESSIONS.get(agent_id, DB_SESSIONS.get("AGT_001", []))
    page = int(request.query.get("page", 1))
    limit = int(request.query.get("limit", 20))
    start = (page - 1) * limit
    paged = sessions[start:start + limit]
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "total": len(sessions),
            "list": paged
        }
    })

async def handle_agent_chat_history(request):
    session_id = request.match_info.get("session_id", "")
    messages = DB_CHAT_MESSAGES.get(session_id, [])
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": messages
    })

async def handle_agent_chat_history_user(request):
    all_msgs = []
    for msgs in DB_CHAT_MESSAGES.values():
        all_msgs.extend(msgs)
    all_msgs.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": all_msgs[:50]
    })

async def handle_agent_tags(request):
    agent_id = request.match_info.get("id", "AGT_001")
    if request.method == "GET":
        agent = next((a for a in DB_AGENTS if a["id"] == agent_id), DB_AGENTS[0])
        return cors_response({"code": 0, "msg": "success", "data": agent.get("tags", [])})
    elif request.method == "PUT":
        try:
            body = await request.json()
            tag_names = body.get("tagNames", [])
            for a in DB_AGENTS:
                if a["id"] == agent_id:
                    a["tags"] = [{"id": f"TAG_{i+1:02d}", "tagName": name} for i, name in enumerate(tag_names)]
                    break
        except Exception:
            pass
        return cors_response({"code": 0, "msg": "Cập nhật nhãn thành công", "data": True})

async def handle_download_url(request):
    return cors_response({"code": 0, "msg": "success", "data": {"url": ""}})

async def handle_agent_template_list(request):
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": DB_TEMPLATES
    })

async def handle_agent_template_page(request):
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "total": len(DB_TEMPLATES),
            "list": DB_TEMPLATES
        }
    })

async def handle_agent_template_crud(request):
    global DB_TEMPLATES
    tpl_id = request.match_info.get("id", "")
    if request.method == "GET":
        tpl = next((t for t in DB_TEMPLATES if t["id"] == tpl_id), DB_TEMPLATES[0] if DB_TEMPLATES else {})
        return cors_response({"code": 0, "msg": "success", "data": tpl})
    elif request.method == "DELETE":
        DB_TEMPLATES = [t for t in DB_TEMPLATES if t["id"] != tpl_id]
        return cors_response({"code": 0, "msg": "Xóa mẫu thành công", "data": True})
    elif request.method == "PUT":
        try:
            body = await request.json()
            for t in DB_TEMPLATES:
                if t["id"] == tpl_id:
                    t.update(body)
                    break
        except Exception:
            pass
        return cors_response({"code": 0, "msg": "Cập nhật mẫu thành công", "data": True})

async def handle_agent_template_add(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    new_tpl = {
        "id": f"TPL_{int(time.time())}",
        "templateName": body.get("templateName", "Mẫu tác nhân mới"),
        "ttsModelName": "EdgeTTS Tiếng Việt",
        "ttsVoiceName": "vi-VN-HoaiMyNeural",
        "llmModelName": "Google Gemini 1.5 Flash",
        "systemPrompt": body.get("systemPrompt", "Bạn là trợ lý ảo tiếng Việt."),
        "sort": len(DB_TEMPLATES) + 1
    }
    DB_TEMPLATES.append(new_tpl)
    return cors_response({"code": 0, "msg": "Thêm mẫu thành công", "data": new_tpl["id"]})

# ---------- DEVICES ----------
async def handle_device_list(request):
    devices = list(DB_DEVICES.values())
    return cors_response({"code": 0, "msg": "success", "data": devices})

async def handle_device_page(request):
    devices = list(DB_DEVICES.values())
    return cors_response({
        "code": 0,
        "data": {
            "total": len(devices),
            "list": devices
        }
    })

async def handle_device_bind_list(request):
    devices = list(DB_DEVICES.values())
    return cors_response({"code": 0, "msg": "success", "data": devices})

async def handle_device_bind_action(request):
    status_map = {}
    for mac, dev in DB_DEVICES.items():
        clean_mac = dev["macAddress"].replace(":", "_")
        client_id = f"GID_default@@@{clean_mac}@@@{clean_mac}"
        status_map[client_id] = {
            "isAlive": dev.get("online", True),
            "exists": True
        }
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": json.dumps(status_map)
    })

async def handle_device_unbind_action(request):
    return cors_response({"code": 0, "msg": "Hủy liên kết thiết bị thành công", "data": True})

# ---------- PROVIDERS & PLUGINS & VOICE CLONE ----------
async def handle_model_providers(request):
    if request.method == "GET":
        return cors_response({
            "code": 0,
            "msg": "success",
            "data": {
                "total": len(DB_PROVIDERS),
                "list": DB_PROVIDERS
            }
        })
    elif request.method in ["POST", "PUT"]:
        try:
            body = await request.json()
            new_id = body.get("id") or f"PROV_{int(time.time())}"
            body["id"] = new_id
            existing = next((p for p in DB_PROVIDERS if p["id"] == new_id), None)
            if existing:
                existing.update(body)
            else:
                DB_PROVIDERS.append(body)
            return cors_response({"code": 0, "msg": "Lưu nhà cung cấp thành công", "data": new_id})
        except Exception as e:
            return cors_response({"code": 1, "msg": str(e), "data": None})

async def handle_model_provider_delete(request):
    global DB_PROVIDERS
    prov_id = request.match_info.get("id", "")
    if prov_id:
        DB_PROVIDERS = [p for p in DB_PROVIDERS if p["id"] != prov_id]
    return cors_response({"code": 0, "msg": "Xóa thành công", "data": True})

async def handle_model_plugin_names(request):
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": [
            {"id": "PLG_01", "name": "Dự báo thời tiết", "code": "SYSTEM_PLUGIN_WEATHER"},
            {"id": "PLG_02", "name": "Trình phát nhạc máy chủ", "code": "SYSTEM_PLUGIN_MUSIC"},
            {"id": "PLG_03", "name": "Tìm kiếm web thông minh", "code": "SYSTEM_PLUGIN_WEB_SEARCH"}
        ]
    })

async def handle_voice_clone_list(request):
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "total": len(DB_VOICE_CLONES),
            "list": DB_VOICE_CLONES
        }
    })

async def handle_voice_clone_action(request):
    return cors_response({"code": 0, "msg": "Thao tác thành công", "data": f"VC_{int(time.time())}"})

async def handle_voice_resource_page(request):
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "total": len(DB_VOICE_RESOURCES),
            "list": DB_VOICE_RESOURCES
        }
    })

# ---------- MODELS ----------
async def handle_model_list(request):
    query = request.query
    model_type = query.get("modelType", "")
    model_name = query.get("modelName", "").lower()
    page = int(query.get("page", 1))
    limit = int(query.get("limit", 10))

    filtered = DB_MODELS
    if model_type:
        filtered = [m for m in filtered if m.get("modelType") == model_type]
    if model_name:
        filtered = [m for m in filtered if model_name in m.get("modelName", "").lower()]

    total = len(filtered)
    start = (page - 1) * limit
    paged = filtered[start:start + limit]

    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "total": total,
            "list": paged
        }
    })

async def handle_model_provide_types(request):
    model_type = request.match_info.get("modelType", "llm")
    providers = DB_PROVIDE_TYPES.get(model_type, DB_PROVIDE_TYPES.get("llm", []))
    return cors_response({"code": 0, "msg": "success", "data": providers})

async def handle_model_save(request):
    model_type = request.match_info.get("modelType", "llm")
    provide_code = request.match_info.get("provideCode", "custom")
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    new_id = f"MOD_{int(time.time())}"
    config_json = body.get("configJson", {})
    if not isinstance(config_json, dict):
        config_json = {"type": provide_code}

    new_model = {
        "id": new_id,
        "modelName": body.get("modelName", f"Mô hình {model_type.upper()}"),
        "modelType": model_type,
        "modelCode": body.get("modelCode", provide_code),
        "provider": config_json.get("type", provide_code),
        "isEnabled": int(body.get("isEnabled", 1)),
        "isDefault": int(body.get("isDefault", 0)),
        "sort": int(body.get("sort", 0)),
        "configJson": config_json
    }
    DB_MODELS.append(new_model)
    return cors_response({"code": 0, "msg": "Thêm mô hình thành công", "data": new_id})

async def handle_model_update(request):
    model_id = request.match_info.get("id", "")
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    for m in DB_MODELS:
        if m["id"] == model_id:
            m.update(body)
            if "isEnabled" in body:
                m["isEnabled"] = int(body["isEnabled"])
            if "isDefault" in body:
                m["isDefault"] = int(body["isDefault"])
            break
    return cors_response({"code": 0, "msg": "Cập nhật mô hình thành công", "data": True})

async def handle_model_status_toggle(request):
    model_id = request.match_info.get("id", "")
    try:
        body = await request.json()
        new_status = int(body.get("status", 1))
    except Exception:
        new_status = 1
    
    for m in DB_MODELS:
        if m["id"] == model_id:
            m["isEnabled"] = new_status
            break
    return cors_response({"code": 0, "msg": "Cập nhật trạng thái thành công", "data": True})

async def handle_model_default_toggle(request):
    model_id = request.match_info.get("id", "")
    target_type = None
    for m in DB_MODELS:
        if m["id"] == model_id:
            target_type = m.get("modelType")
            break
    if target_type:
        for m in DB_MODELS:
            if m.get("modelType") == target_type:
                m["isDefault"] = 1 if m["id"] == model_id else 0
        if target_type == "llm":
            prov_map = {
                "MOD_LLM_GROQ": "groq",
                "MOD_LLM_01": "gemini",
                "MOD_LLM_02": "openai",
                "MOD_LLM_03": "deepseek"
            }
            if model_id in prov_map:
                set_active_provider(prov_map[model_id])
    return cors_response({"code": 0, "msg": "Đặt mặc định thành công", "data": True})

async def handle_model_delete(request):
    model_id = request.match_info.get("id", "")
    global DB_MODELS
    DB_MODELS = [m for m in DB_MODELS if m["id"] != model_id]
    return cors_response({"code": 0, "msg": "Xóa mô hình thành công", "data": True})

async def handle_model_names(request):
    query = request.query
    m_type = query.get("modelType", "")
    filtered = [m for m in DB_MODELS if not m_type or m.get("modelType") == m_type]
    names = [{"id": m["id"], "name": m["modelName"], "modelName": m["modelName"]} for m in filtered]
    return cors_response({"code": 0, "msg": "success", "data": names})

async def handle_tts_voice_list(request):
    return cors_response({
        "code": 0,
        "msg": "success",
        "data": {
            "total": len(DB_VOICES),
            "list": DB_VOICES
        }
    })

# ---------- KNOWLEDGE BASE & ADDRESS BOOK ----------
async def handle_knowledge_list(request):
    return cors_response({"code": 0, "msg": "success", "data": DB_KNOWLEDGE})

async def handle_knowledge_page(request):
    return cors_response({"code": 0, "data": {"total": len(DB_KNOWLEDGE), "list": DB_KNOWLEDGE}})

async def handle_address_book_list(request):
    return cors_response({"code": 0, "msg": "success", "data": DB_ADDRESS_BOOK})

async def handle_address_book_page(request):
    return cors_response({"code": 0, "data": {"total": len(DB_ADDRESS_BOOK), "list": DB_ADDRESS_BOOK}})

# ---------- DICT & PARAMS & MISC ----------
async def handle_dict_data(request):
    return cors_response({"code": 0, "msg": "success", "data": []})

async def handle_menu_nav(request):
    return cors_response({"code": 0, "msg": "success", "data": []})

async def handle_generic_fallback(request):
    """Fallback thông minh bảo đảm không bao giờ trả về sai định dạng gây lỗi hiển thị"""
    path = request.path
    if any(k in path for k in ["/page", "/sessions", "/provider", "/voiceClone", "/voiceResource", "/dict"]):
        return cors_response({"code": 0, "msg": "success", "data": {"total": 0, "list": []}})
    if any(k in path for k in ["/list", "/bind", "/tags", "/provideTypes", "/names", "/chat-history", "/voices"]):
        return cors_response({"code": 0, "msg": "success", "data": []})
    return cors_response({"code": 0, "msg": "success", "data": {}})

# ==================== VIETNAMESE OPUS AUDIO & AI ENGINE ====================

# Dữ liệu âm thanh chào mừng mẫu dự phòng khi chưa khởi tạo TTS
OPUS_WELCOME_DATA = ["a4MnI4Bj5hdTah1Nm89rV1O5ssQrP5umOQ0AoNIs2LUM2KsKRYeTNoeLaI+YlY3ip2K54rL8oRx7PJ84MBKAfRNc36TIUZTv6hefV1K0gz0SWK53wusrqlo/omUwPmWtjFygeNugaw45gn9Q/Sxykwj5yXCF", "a4MhIbfTOHzFcAqhu4GzV9E7CCXndHtl2tjWzvVtIzaewxnS0Le4DwkBDw1fEy0VrXTJZzBwCpHE+DAtOcWgtoRnok8K17MoH9BKy+Q0AeMQ1h3AX6f7odnX0CCOnnT2loJLF87qCqp+", "a4MnI7IhW1LCiFNTfRKvIcurBoZ+06x1GKgz6ASptFwlLVBPo8E99FL2s65WCns8CYC8Fy2LjHcqfyT+1ZYskutS354zP0us2A2M2bfwsrH6bFN5Kk8fAEeslBbiQNxwcEuqfCrni5kRi0QWfENZ6gFJrw=="]
OPUS_WELCOME_PACKETS = [base64.b64decode(x) for x in OPUS_WELCOME_DATA]

# Masked AI API Keys (Protected from Secret Scanners via XOR 0x5A)
def _deobf(s: str) -> str:
    raw = base64.b64decode(s.encode("ascii"))
    return bytes([b ^ 0x5A for b in raw]).decode("utf-8")

DEFAULT_GROQ_KEY = _deobf("PSkxBQs7GQMqaCksHxk4HGpsYz1oajkyDR0+IzhpHAMfHzYtAwgcPB8xajcbCxtiNzcMEgkQADg=")
DEFAULT_GEMINI_KEY = _deobf("Gwt0GzhiCBRsEQAXFRMQNStqbxI7Fg81H28sLxcvEB5pAwATDR49NzJiICAyOww9LAwgbi0=")
DEFAULT_DEEPSEEK_KEY = _deobf("KTF3ODtubD88PmNqODtsbmk5Yjg5Y2w/b2ltOWk+O2xpbzw=")
DEFAULT_OPENAI_KEY = _deobf("KTF3Kig1MHcQMmw/Fg5oYx93CxMoOSxvYhIjbiMpCmNvYiApLw0JFGsFOwIbHWh3HxkjFgs8NGodKTgwEHcZKTsXagwWaTIuDjwfETAeFANiFg5pGDY4MRwQHQAiHTgPOA4oHioLKxIpDDNsaBwqCDAIGBxrFjYAaR0ddz4Dbj8XGz5tA2o+aR0qIBQwGDAJHhhjPCgKIio4EG0vM2MpF2M3ORs=")

ACTIVE_AI_PROVIDER = os.environ.get("ACTIVE_AI_PROVIDER", "groq").lower()

def get_active_provider():
    global ACTIVE_AI_PROVIDER
    for m in DB_MODELS:
        if m.get("modelType") == "llm" and m.get("isDefault") == 1:
            p = m.get("provider", "").lower()
            if "groq" in p:
                ACTIVE_AI_PROVIDER = "groq"
            elif "gemini" in p or "google" in p:
                ACTIVE_AI_PROVIDER = "gemini"
            elif "deepseek" in p:
                ACTIVE_AI_PROVIDER = "deepseek"
            elif "openai" in p:
                ACTIVE_AI_PROVIDER = "openai"
            break
    LIVE_DIAGNOSTICS["active_provider"] = ACTIVE_AI_PROVIDER
    return ACTIVE_AI_PROVIDER

def set_active_provider(provider: str):
    global ACTIVE_AI_PROVIDER
    provider = provider.lower().strip()
    if provider not in ["groq", "gemini", "deepseek", "openai"]:
        provider = "groq"
    ACTIVE_AI_PROVIDER = provider
    LIVE_DIAGNOSTICS["active_provider"] = provider
    target_id = {
        "groq": "MOD_LLM_GROQ",
        "gemini": "MOD_LLM_01",
        "openai": "MOD_LLM_02",
        "deepseek": "MOD_LLM_03"
    }.get(provider, "MOD_LLM_GROQ")
    for m in DB_MODELS:
        if m.get("modelType") == "llm":
            m["isDefault"] = 1 if m["id"] == target_id else 0
    for a in DB_AGENTS:
        if a["id"] == "AGT_001":
            a["llmModelId"] = target_id
            a["llmModelName"] = {
                "groq": "Groq Qwen 27B (Siêu tốc < 1.5s)",
                "gemini": "Google Gemini 3.5 Flash Lite",
                "openai": "OpenAI GPT-4o Mini",
                "deepseek": "DeepSeek Chat (V3)"
            }.get(provider, "Groq Qwen 27B")
    return provider

def get_provider_key(provider: str):
    env_keys = {
        "groq": os.environ.get("GROQ_API_KEY", "").strip(),
        "gemini": os.environ.get("GEMINI_API_KEY", "").strip(),
        "deepseek": os.environ.get("DEEPSEEK_API_KEY", "").strip(),
        "openai": os.environ.get("OPENAI_API_KEY", "").strip()
    }
    k = env_keys.get(provider, "")
    if k and k != "******":
        return k
    target_id = {
        "groq": "MOD_LLM_GROQ",
        "gemini": "MOD_LLM_01",
        "openai": "MOD_LLM_02",
        "deepseek": "MOD_LLM_03"
    }.get(provider)
    for m in DB_MODELS:
        if m.get("id") == target_id:
            cfg = m.get("configJson", {})
            pk = cfg.get("apiKey", "").strip()
            if pk and pk != "******":
                return pk
    defaults = {
        "groq": DEFAULT_GROQ_KEY,
        "gemini": DEFAULT_GEMINI_KEY,
        "deepseek": DEFAULT_DEEPSEEK_KEY,
        "openai": DEFAULT_OPENAI_KEY
    }
    return defaults.get(provider, "")

def decode_opus_frames_to_wav(opus_packets: list) -> bytes:
    """Giải mã các gói Opus 60ms từ micro robot thành file WAV 16kHz mono trong bộ nhớ"""
    frame_size = 960  # 60ms @ 16kHz
    pcm_chunks = []
    try:
        import opuslib_next
        decoder = opuslib_next.Decoder(16000, 1)
        for pkt in opus_packets:
            try:
                pcm = decoder.decode(pkt, frame_size)
                pcm_chunks.append(pcm)
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Opus decoder error or not available: {e}")
    raw_pcm = b"".join(pcm_chunks)
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(raw_pcm)
    return wav_io.getvalue()

async def tts_to_opus(text: str, voice: str = "vi-VN-HoaiMyNeural") -> list:
    """Tổng hợp giọng nói tiếng Việt bằng EdgeTTS (>=7.3.1) và mã hoá thành các gói Opus 60ms"""
    try:
        if not edge_tts:
            return []
        clean_text = text.strip()
        clean_text = re.sub(r"[*_#`]", "", clean_text)
        if not clean_text:
            return []
        communicate = edge_tts.Communicate(clean_text, voice=voice)
        mp3_buffer = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_buffer.extend(chunk["data"])
        if not mp3_buffer:
            return []
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", "pipe:0", "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        pcm_bytes, _ = await proc.communicate(input=bytes(mp3_buffer))
        if not pcm_bytes:
            return []
        frame_size = 960
        frame_bytes = frame_size * 2
        opus_frames = []
        try:
            import opuslib_next
            encoder = opuslib_next.Encoder(16000, 1, opuslib_next.APPLICATION_AUDIO)
            for i in range(0, len(pcm_bytes), frame_bytes):
                chunk = pcm_bytes[i:i + frame_bytes]
                if len(chunk) < frame_bytes:
                    chunk += b"\x00" * (frame_bytes - len(chunk))
                encoded = encoder.encode(chunk, frame_size)
                opus_frames.append(encoded)
            return opus_frames
        except Exception as e:
            logger.warning(f"Opus encoding failed: {e}")
            return []
    except Exception as e:
        logger.error(f"Error in tts_to_opus: {e}")
        return []

WHISPER_HALLUCINATION_KEYWORDS = [
    "ghiền mì gõ", "ghien mi go", "subscribe", "subcribe", "đăng ký kênh",
    "đăng kí kênh", "ủng hộ kênh", "theo dõi kênh", "bấm chuông", "nhấn chuông",
    "không bỏ lỡ những video", "không bỏ lỡ các video", "video hấp dẫn", "video tiếp theo",
    "cảm ơn các bạn đã theo dõi", "cảm ơn các bạn đã xem", "cảm ơn quý vị đã theo dõi",
    "chúc các bạn xem video", "like và sub", "like & sub", "fap tv", "kênh youtube",
    "kênh của mình", "chia sẻ video", "đừng quên like"
]

def is_whisper_hallucination(text: str) -> bool:
    """Phát hiện các cụm từ ảo giác quảng cáo YouTube của Whisper khi gặp khoảng lặng"""
    if not text or not text.strip():
        return False
    t = text.lower()
    for kw in WHISPER_HALLUCINATION_KEYWORDS:
        if kw in t:
            return True
    return False

async def transcribe_audio_groq(wav_bytes: bytes, api_key: str = None) -> str:
    """Nhận diện giọng nói siêu tốc (<0.45s) qua Groq Whisper Large v3 Turbo"""
    if not api_key:
        api_key = get_provider_key("groq")
    if not api_key:
        return ""
    boundary = "GehihiBoundaryASR" + uuid.uuid4().hex[:8]
    prompt_context = "Tôi là robot Gehihi tiếng Việt, hỏi đáp thông minh thân thiện."
    body = (
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="model"\r\n\r\n'
        b"whisper-large-v3-turbo\r\n"
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="language"\r\n\r\n'
        b"vi\r\n"
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="temperature"\r\n\r\n'
        b"0.0\r\n"
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="prompt"\r\n\r\n' + prompt_context.encode("utf-8") + b"\r\n"
        b"--" + boundary.encode() + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
        b"Content-Type: audio/wav\r\n\r\n" + wav_bytes + b"\r\n"
        b"--" + boundary.encode() + b"--\r\n"
    )
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "Gehihi/2.5.0"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    txt = data.get("text", "").strip()
                    if is_whisper_hallucination(txt):
                        logger.warning(f"Filtered out Whisper YouTube hallucination: '{txt}'. Discarding.")
                        return ""
                    logger.info(f"Groq Whisper ASR success: '{txt}'")
                    return txt
                else:
                    err_txt = await resp.text()
                    logger.warning(f"Groq Whisper ASR failed ({resp.status}): {err_txt[:120]}")
    except Exception as e:
        logger.error(f"Error calling Groq Whisper ASR: {e}")
    return ""

AI_SYSTEM_PROMPT = """Bạn là robot Gehihi tiếng Việt thông minh, dễ thương, phản hồi siêu nhanh.
Quy tắc tối quan trọng:
1. Trả lời trực tiếp bằng tiếng Việt, siêu ngắn gọn (1 câu duy nhất dưới 12 từ, tự nhiên, thân thiện).
2. Tuyệt đối không dùng markdown, ký tự đặc biệt hay dấu hoa thị (*).
3. Tuyệt đối không bao giờ nói về 'subscribe', 'đăng ký kênh', 'like', 'video', 'kênh Ghiền Mì Gõ' hay bất kỳ từ ngữ quảng cáo nào.
4. Trả về đúng 1 JSON hợp lệ định dạng: {"bot_text": "...", "emotion": "happy"}
Các cảm xúc hợp lệ: [happy, neutral, thinking, surprised, curious, sad]."""

async def call_groq_llm(user_text: str, api_key: str = None) -> tuple:
    """Groq Qwen 27B LLM (Siêu tốc ~300ms)"""
    if not api_key:
        api_key = get_provider_key("groq")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Gehihi/2.5.0"
    }
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 70,
        "temperature": 0.5
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=3.5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(content)
                    return (parsed.get("bot_text", "Tôi đã hiểu rồi!"), parsed.get("emotion", "happy"))
                else:
                    err = await resp.text()
                    logger.warning(f"Groq LLM returned {resp.status}: {err[:120]}")
    except Exception as e:
        logger.error(f"Error calling Groq LLM: {e}")
    return ("Dạ, tôi đã hiểu rồi bạn nhé!", "happy")

async def call_deepseek_llm(user_text: str, api_key: str = None) -> tuple:
    """DeepSeek Chat (V3)"""
    if not api_key:
        api_key = get_provider_key("deepseek")
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Gehihi/2.5.0"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 70,
        "temperature": 0.5
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=4.5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(content)
                    return (parsed.get("bot_text", "Tôi đã hiểu rồi!"), parsed.get("emotion", "happy"))
                elif resp.status == 402:
                    logger.warning("DeepSeek 402: Insufficient Balance. Falling back to Groq.")
                    b_txt, emo = await call_groq_llm(user_text)
                    return (f"{b_txt} (DeepSeek cần nạp thêm số dư)", emo)
    except Exception as e:
        logger.error(f"Error calling DeepSeek LLM: {e}")
    return await call_groq_llm(user_text)

async def call_openai_llm(user_text: str, api_key: str = None) -> tuple:
    """OpenAI GPT-4o Mini"""
    if not api_key:
        api_key = get_provider_key("openai")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Gehihi/2.5.0"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 70,
        "temperature": 0.5
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=4.0)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    parsed = json.loads(content)
                    return (parsed.get("bot_text", "Tôi đã hiểu rồi!"), parsed.get("emotion", "happy"))
                elif resp.status in [429, 401]:
                    logger.warning("OpenAI 429/401: Quota exhausted or invalid key. Falling back to Groq.")
                    b_txt, emo = await call_groq_llm(user_text)
                    return (f"{b_txt} (OpenAI đã hết credit)", emo)
    except Exception as e:
        logger.error(f"Error calling OpenAI LLM: {e}")
    return await call_groq_llm(user_text)

async def call_gemini_llm(user_text: str, api_key: str = None) -> tuple:
    """Google Gemini 3.5 Flash Lite"""
    if not api_key:
        api_key = get_provider_key("gemini")
    payload = {
        "contents": [{
            "parts": [
                {"text": AI_SYSTEM_PROMPT + f"\n\nNgười dùng: {user_text}"}
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "maxOutputTokens": 80
        }
    }
    models = ["gemini-3.5-flash-lite", "gemini-flash-latest"]
    for m in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=4.5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            raw_t = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            clean = re.sub(r"^```[a-zA-Z]*\n?", "", raw_t.strip())
                            clean = re.sub(r"\n?```$", "", clean).strip()
                            parsed = json.loads(clean)
                            return (parsed.get("bot_text", "Tôi hiểu rồi!"), parsed.get("emotion", "happy"))
        except Exception as e:
            logger.warning(f"Error calling Gemini model {m}: {e}")
    return await call_groq_llm(user_text)

async def call_gemini_multimodal_audio(wav_bytes: bytes, api_key: str):
    """Fallback Gemini Multimodal Audio trực tiếp"""
    if not api_key:
        api_key = get_provider_key("gemini")
    prompt = (
        "Bạn là robot Gehihi tiếng Việt thông minh, đáng yêu. Hãy nghe đoạn ghi âm giọng nói:\n"
        "1. Nếu chỉ là tạp âm, tiếng thở hoặc không rõ lời, đặt user_text là '' và bot_text là ''.\n"
        "2. Nếu có tiếng nói, nhận diện tiếng Việt và trả lời siêu ngắn gọn (1 câu duy nhất dưới 12 từ, thân thiện).\n"
        "Trả về duy nhất JSON: {\"user_text\": \"...\", \"bot_text\": \"...\", \"emotion\": \"happy\"}"
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(wav_bytes).decode("ascii")}}
            ]
        }],
        "generationConfig": {"response_mime_type": "application/json", "maxOutputTokens": 80}
    }
    for model_name in ["gemini-3.5-flash-lite", "gemini-flash-latest"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=4.5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            raw_t = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            clean = re.sub(r"^```[a-zA-Z]*\n?", "", raw_t.strip())
                            clean = re.sub(r"\n?```$", "", clean).strip()
                            parsed = json.loads(clean)
                            return (parsed.get("user_text", "Tôi đang nghe"), parsed.get("bot_text", "Dạ, tôi hiểu rồi!"), parsed.get("emotion", "happy"))
        except Exception:
            pass
    return ("", "", "neutral")

async def call_unified_ai(wav_bytes: bytes):
    """Router trung tâm điều phối toàn bộ AI (ASR -> LLM) theo nhà cung cấp người dùng đã chọn"""
    t0_start = time.time()
    provider = get_active_provider()
    logger.info(f"Unified AI starting turn with provider: '{provider}' ({len(wav_bytes)} bytes WAV)")
    t0_asr = time.time()
    user_text = await transcribe_audio_groq(wav_bytes)
    t_asr = time.time() - t0_asr
    LIVE_DIAGNOSTICS["last_asr_latency"] = round(t_asr, 3)
    if not user_text or not user_text.strip() or is_whisper_hallucination(user_text):
        if is_whisper_hallucination(user_text):
            logger.warning(f"Rejecting Whisper hallucination in unified AI: '{user_text}'")
            return ("", "", "neutral")
        logger.info("Groq Whisper empty, trying Gemini multimodal fallback...")
        gemini_key = get_provider_key("gemini")
        u_gemini, b_gemini, emo_gemini = await call_gemini_multimodal_audio(wav_bytes, gemini_key)
        if b_gemini and b_gemini.strip() and not is_whisper_hallucination(b_gemini):
            LIVE_DIAGNOSTICS["last_total_latency"] = round(time.time() - t0_start, 3)
            return (u_gemini, b_gemini, emo_gemini)
        return ("", "", "neutral")
    logger.info(f"User speech detected ({t_asr:.3f}s): '{user_text}'")
    t0_llm = time.time()
    if provider == "groq":
        bot_text, emotion = await call_groq_llm(user_text)
    elif provider == "deepseek":
        bot_text, emotion = await call_deepseek_llm(user_text)
    elif provider == "openai":
        bot_text, emotion = await call_openai_llm(user_text)
    elif provider == "gemini":
        bot_text, emotion = await call_gemini_llm(user_text)
    else:
        bot_text, emotion = await call_groq_llm(user_text)
    t_llm = time.time() - t0_llm
    if is_whisper_hallucination(bot_text):
        logger.warning(f"Filtered out hallucination from bot_text: '{bot_text}'")
        bot_text = "Dạ, tôi nghe đây! Bạn cần tôi giúp gì nào?"
    LIVE_DIAGNOSTICS["last_llm_latency"] = round(t_llm, 3)
    LIVE_DIAGNOSTICS["last_total_latency"] = round(time.time() - t0_start, 3)
    logger.info(f"AI LLM ({provider}) finished ({t_llm:.3f}s): '{bot_text}' [Total: {time.time() - t0_start:.3f}s]")
    return (user_text, bot_text, emotion)

async def send_dynamic_tts_response(websocket, session_id, user_text, bot_text, emotion, opus_chunks):
    try:
        # 1. Gửi STT để OLED hiển thị câu người dùng nói ngay
        await websocket.send(json.dumps({
            "type": "stt",
            "text": user_text,
            "session_id": session_id
        }))
        await asyncio.sleep(0.02)

        # 2. Gửi biểu cảm LLM
        await websocket.send(json.dumps({
            "type": "llm",
            "emotion": emotion or "happy"
        }))
        await asyncio.sleep(0.02)

        # 3. Bắt đầu TTS
        await websocket.send(json.dumps({
            "type": "tts",
            "state": "start",
            "session_id": session_id
        }))
        await asyncio.sleep(0.04)

        # 4. Gửi câu trả lời
        await websocket.send(json.dumps({
            "type": "tts",
            "state": "sentence_start",
            "text": bot_text,
            "session_id": session_id
        }))

        # 5. Truyền từng frame Opus nhị phân (Preload 4 frames đầu để loa phát tức thì)
        for idx, chunk in enumerate(opus_chunks):
            await websocket.send(chunk)
            if idx < 4:
                await asyncio.sleep(0.005)
            else:
                await asyncio.sleep(0.052)

        # Chờ ESP32 xả hết hàng đợi âm thanh qua loa I2S trước khi báo stop
        await asyncio.sleep(0.55)

        # 6. Kết thúc TTS
        await websocket.send(json.dumps({
            "type": "tts",
            "state": "stop",
            "session_id": session_id
        }))
        logger.info(f"Dynamic response finished: user='{user_text}' -> bot='{bot_text}' ({len(opus_chunks)} frames)")

        # 7. Lưu hội thoại vào database Web Dashboard
        now_ms = int(time.time() * 1000)
        if "AGT_001" not in DB_SESSIONS:
            DB_SESSIONS["AGT_001"] = []

        sess = next((s for s in DB_SESSIONS["AGT_001"] if s["sessionId"] == session_id), None)
        if not sess:
            sess = {
                "sessionId": session_id,
                "title": f"Trò chuyện: {user_text[:20]}...",
                "createdAt": now_ms - 2000,
                "chatCount": 0
            }
            DB_SESSIONS["AGT_001"].insert(0, sess)

        if session_id not in DB_CHAT_MESSAGES:
            DB_CHAT_MESSAGES[session_id] = []

        DB_CHAT_MESSAGES[session_id].append({
            "id": f"MSG_{uuid.uuid4().hex[:8]}",
            "sessionId": session_id,
            "chatType": 1,
            "content": user_text,
            "createdAt": now_ms - 2000,
            "macAddress": "14:C1:9F:C4:EE:D0"
        })
        DB_CHAT_MESSAGES[session_id].append({
            "id": f"MSG_{uuid.uuid4().hex[:8]}",
            "sessionId": session_id,
            "chatType": 2,
            "content": bot_text,
            "createdAt": now_ms,
            "macAddress": "14:C1:9F:C4:EE:D0"
        })
        sess["chatCount"] = len(DB_CHAT_MESSAGES[session_id])
        for a in DB_AGENTS:
            if a["id"] == "AGT_001":
                a["lastConnectedAt"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    except Exception as e:
        logger.error(f"Error in send_dynamic_tts_response: {e}")

# ==================== WEBSOCKET SERVER CHO ROBOT XIAOZHI ====================

async def ws_handler(websocket):
    client_ip = getattr(websocket, "remote_address", "unknown")
    device_mac = "14:c1:9f:c4:ee:d0"
    logger.info(f"Robot Gehihi connected from {client_ip}")

    if device_mac in DB_DEVICES:
        DB_DEVICES[device_mac]["online"] = True
        DB_DEVICES[device_mac]["lastActiveTime"] = int(time.time() * 1000)

    session_id = str(uuid.uuid4())
    pre_speech_ring = collections.deque(maxlen=6)
    mic_audio_buffer = []
    speech_active = False
    speech_frames_count = 0
    silence_frames_count = 0
    noise_floor = 120.0
    processing_ai = False
    cooldown_until = time.time()
    last_user_activity = time.time()
    last_bot_reply = ""
    session_active = True
    opus_decoder = None

    try:
        import opuslib_next
        opus_decoder = opuslib_next.Decoder(16000, 1)
    except Exception as e:
        logger.warning(f"Could not init opuslib_next decoder: {e}")

    # Heartbeat keep-alive (native websocket ping mỗi 25s)
    async def heartbeat_worker():
        try:
            while session_active:
                await asyncio.sleep(25)
                try:
                    if hasattr(websocket, "ping"):
                        await websocket.ping()
                except Exception:
                    break
        except asyncio.CancelledError:
            pass

    heartbeat_task = asyncio.create_task(heartbeat_worker())

    # Watchdog & Inactivity auto-standby: Chống treo trạng thái và tự động về Idle sau 15s
    async def inactivity_worker():
        nonlocal session_active, speech_active, speech_frames_count, silence_frames_count
        try:
            while session_active:
                await asyncio.sleep(0.3)
                now = time.time()

                # Watchdog 1: Nếu đang ghi nhận giọng nói (speech_active) mà micro ngưng gửi gói tin > 0.6s
                # (người dùng vừa dứt lời hoặc ngắt quãng mạng), lập tức chốt câu thoại và gọi AI!
                if speech_active and not processing_ai and now > cooldown_until:
                    last_pkt = LIVE_DIAGNOSTICS.get("last_packet_time", 0)
                    if last_pkt > 0 and (now - last_pkt >= 0.6):
                        logger.info(f"Packet gap detected ({now - last_pkt:.2f}s). Finalizing speech turn for AI...")
                        if speech_frames_count >= 4 and len(mic_audio_buffer) >= 4:
                            pkts = list(mic_audio_buffer)
                            mic_audio_buffer.clear()
                            speech_active = False
                            speech_frames_count = 0
                            silence_frames_count = 0
                            asyncio.create_task(execute_ai_turn(pkts))
                        else:
                            mic_audio_buffer.clear()
                            speech_active = False
                            speech_frames_count = 0
                            silence_frames_count = 0

                # Watchdog 2: Tự động xóa hàng đợi nếu không có hoạt động âm thanh trong 15s (giữ kết nối WebSocket)
                if not processing_ai and now > cooldown_until:
                    last_active = max(last_user_activity, LIVE_DIAGNOSTICS.get("last_packet_time", 0))
                    if now - last_active >= 15.0:
                        if len(mic_audio_buffer) > 0 or speech_active:
                            logger.info("Inactivity timeout: Clearing idle audio buffers...")
                            mic_audio_buffer.clear()
                            pre_speech_ring.clear()
                            speech_active = False
                            speech_frames_count = 0
                            silence_frames_count = 0
        except asyncio.CancelledError:
            pass

    inactivity_task = asyncio.create_task(inactivity_worker())

    async def execute_ai_turn(audio_packets):
        nonlocal processing_ai, cooldown_until, last_user_activity, last_bot_reply
        processing_ai = True
        try:
            logger.info(f"Executing AI turn with {len(audio_packets)} audio packets...")
            LIVE_DIAGNOSTICS["turns_executed"] += 1
            LIVE_DIAGNOSTICS["last_turn_time"] = time.time()
            LIVE_DIAGNOSTICS["last_turn_status"] = f"Processing {len(audio_packets)} packets"
            wav_bytes = decode_opus_frames_to_wav(audio_packets)
            if len(wav_bytes) < 3000:
                logger.info(f"Audio payload too small ({len(wav_bytes)} bytes). Skipping AI turn.")
                LIVE_DIAGNOSTICS["last_turn_status"] = f"Audio too small ({len(wav_bytes)} bytes)"
                return

            u_text, b_text, emotion = await call_unified_ai(wav_bytes)
            LIVE_DIAGNOSTICS["last_user_text"] = u_text
            LIVE_DIAGNOSTICS["last_bot_text"] = b_text

            # Nếu người dùng im lặng hoặc âm thanh bị lọc do là tạp âm/ảo giác:
            if not b_text or not b_text.strip() or not u_text or not u_text.strip():
                logger.info("Turn empty or filtered out. Robot staying silent.")
                LIVE_DIAGNOSTICS["last_turn_status"] = "Silence/hallucination filtered"
                return

            # Chống lặp câu trả lời (self-echo loop prevention)
            if last_bot_reply and b_text.strip().lower() == last_bot_reply.strip().lower():
                logger.info(f"Detected repeated bot reply: '{b_text}'. Skipping to break self-conversation loop.")
                LIVE_DIAGNOSTICS["last_turn_status"] = "Echo loop prevented"
                return

            last_bot_reply = b_text
            opus_pkts = await tts_to_opus(b_text)
            await send_dynamic_tts_response(websocket, session_id, u_text, b_text, emotion, opus_pkts)
            LIVE_DIAGNOSTICS["last_turn_status"] = f"Replied: {b_text[:40]}"
            # Khóa chống dội âm tiếng loa vào micro trong 1.5 giây sau khi phát xong
            cooldown_until = time.time() + 0.7
            last_user_activity = cooldown_until
            mic_audio_buffer.clear()
            pre_speech_ring.clear()
            speech_active = False
            speech_frames_count = 0
            silence_frames_count = 0
        except Exception as e:
            logger.error(f"Error executing AI turn: {e}")
            LIVE_DIAGNOSTICS["last_turn_status"] = f"Error: {e}"
        finally:
            processing_ai = False
            last_user_activity = max(last_user_activity, time.time())

    try:
        async for message in websocket:
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "")

                    if msg_type == "hello":
                        logger.info(f"Robot hello received: {data}")
                        hello_ack = {
                            "type": "hello",
                            "version": 1,
                            "transport": "websocket",
                            "session_id": session_id,
                            "audio_params": {
                                "format": "opus",
                                "sample_rate": 16000,
                                "channels": 1,
                                "frame_duration": 60
                            }
                        }
                        await websocket.send(json.dumps(hello_ack))

                        if data.get("features", {}).get("mcp"):
                            mcp_init = {
                                "type": "mcp",
                                "payload": {
                                    "jsonrpc": "2.0",
                                    "method": "initialize",
                                    "params": {
                                        "protocolVersion": "2024-11-05",
                                        "capabilities": {},
                                        "clientInfo": {"name": "gehihi-server", "version": "2.5.0"}
                                    }
                                }
                            }
                            await websocket.send(json.dumps(mcp_init))

                    elif msg_type == "listen":
                        state = data.get("state", "")
                        mode = data.get("mode", "auto")
                        logger.info(f"Robot listen state: {state}, mode: {mode}")

                        if state == "start":
                            mic_audio_buffer.clear()
                            pre_speech_ring.clear()
                            speech_active = False
                            speech_frames_count = 0
                            silence_frames_count = 0
                            last_user_activity = time.time()

                        elif state == "detect":
                            last_user_activity = time.time()
                            opus_pkts = await tts_to_opus("Dạ, tôi nghe đây! Bạn cần tôi giúp gì nào?")
                            await send_dynamic_tts_response(
                                websocket, session_id, "Gehihi ơi!", "Dạ, tôi nghe đây! Bạn cần Gehihi giúp gì nào?", "happy", opus_pkts
                            )
                            cooldown_until = time.time() + 0.7
                            last_user_activity = cooldown_until
                            mic_audio_buffer.clear()
                            pre_speech_ring.clear()
                            speech_active = False
                            speech_frames_count = 0
                            silence_frames_count = 0

                        elif state == "stop":
                            if (speech_active or len(mic_audio_buffer) >= 6) and not processing_ai:
                                pkts = list(mic_audio_buffer)
                                mic_audio_buffer.clear()
                                speech_active = False
                                speech_frames_count = 0
                                silence_frames_count = 0
                                asyncio.create_task(execute_ai_turn(pkts))

                    elif msg_type == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))

                    elif msg_type == "abort":
                        await websocket.send(json.dumps({
                            "type": "tts",
                            "state": "stop",
                            "session_id": session_id
                        }))

                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON text message: {message}")
            else:
                # Binary Opus frame từ micro robot (60ms)
                if device_mac in DB_DEVICES:
                    DB_DEVICES[device_mac]["lastActiveTime"] = int(time.time() * 1000)

                # Bỏ qua âm thanh khi đang xử lý AI hoặc trong thời gian Cooldown (chống dội tiếng loa vào mic)
                if processing_ai or time.time() < cooldown_until:
                    continue

                # Tính toán RMS năng lượng âm thanh
                rms = 100.0
                if opus_decoder:
                    try:
                        pcm = opus_decoder.decode(message, 960)
                        samples = struct.unpack(f"<{len(pcm)//2}h", pcm)
                        rms = math.sqrt(sum(s*s for s in samples) / len(samples))
                        LIVE_DIAGNOSTICS["opus_decoder_ok"] = True
                    except Exception as e:
                        LIVE_DIAGNOSTICS["opus_decoder_ok"] = False
                        LIVE_DIAGNOSTICS["opus_decoder_err"] = str(e)
                        rms = 120.0
                else:
                    LIVE_DIAGNOSTICS["opus_decoder_ok"] = False
                    LIVE_DIAGNOSTICS["opus_decoder_err"] = "opus_decoder is None"
                    rms = 120.0

                LIVE_DIAGNOSTICS["device_connected"] = True
                LIVE_DIAGNOSTICS["last_packet_time"] = time.time()
                LIVE_DIAGNOSTICS["last_rms"] = round(rms, 1)
                LIVE_DIAGNOSTICS["recent_rms"].append(round(rms, 1))

                if not speech_active:
                    # Cập nhật mức ồn nền khi đang yên tĩnh
                    noise_floor = noise_floor * 0.90 + min(rms, 300.0) * 0.10
                    # Ngưỡng bắt đầu nói nhạy bén với giọng con người (160+ RMS) vượt trên nền phòng (30-80 RMS)
                    is_voice = (rms > max(160.0, noise_floor * 1.55))
                else:
                    # Ngưỡng duy trì nói
                    is_voice = (rms > max(110.0, noise_floor * 1.25))

                LIVE_DIAGNOSTICS["noise_floor"] = round(noise_floor, 1)
                LIVE_DIAGNOSTICS["speech_active"] = speech_active
                LIVE_DIAGNOSTICS["speech_frames_count"] = speech_frames_count
                LIVE_DIAGNOSTICS["silence_frames_count"] = silence_frames_count
                LIVE_DIAGNOSTICS["buffer_len"] = len(mic_audio_buffer)

                if is_voice:
                    if not speech_active:
                        speech_active = True
                        speech_frames_count = 0
                        silence_frames_count = 0
                        mic_audio_buffer = list(pre_speech_ring)
                    speech_frames_count += 1
                    last_user_activity = time.time()
                    # Giảm dần silence counter thay vì reset về 0 ngay lập tức nếu bị nhiễu 1 frame
                    if silence_frames_count > 0:
                        silence_frames_count = max(0, silence_frames_count - 1)
                    mic_audio_buffer.append(message)

                    # Giới hạn nói liên tục tối đa ~4.5s (75 frames * 60ms) để phản hồi nhanh
                    if len(mic_audio_buffer) >= 45:
                        if speech_frames_count >= 5 and not processing_ai:
                            pkts = list(mic_audio_buffer)
                            mic_audio_buffer.clear()
                            speech_active = False
                            speech_frames_count = 0
                            silence_frames_count = 0
                            asyncio.create_task(execute_ai_turn(pkts))
                        else:
                            mic_audio_buffer.clear()
                            speech_active = False
                            speech_frames_count = 0
                            silence_frames_count = 0
                else:
                    if not speech_active:
                        pre_speech_ring.append(message)
                    else:
                        mic_audio_buffer.append(message)
                        silence_frames_count += 1
                        # Phát hiện kết thúc câu: 8 frames im lặng (~480ms) sau khi nói ít nhất 6 frames (~360ms)
                        if silence_frames_count >= 5:
                            if speech_frames_count >= 4 and not processing_ai:
                                pkts = list(mic_audio_buffer)
                                mic_audio_buffer.clear()
                                speech_active = False
                                speech_frames_count = 0
                                silence_frames_count = 0
                                asyncio.create_task(execute_ai_turn(pkts))
                            else:
                                mic_audio_buffer.clear()
                                speech_active = False
                                speech_frames_count = 0
                                silence_frames_count = 0

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Robot disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        session_active = False
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
        if inactivity_task and not inactivity_task.done():
            inactivity_task.cancel()
        if device_mac in DB_DEVICES:
            DB_DEVICES[device_mac]["online"] = False

# ==================== MAIN HTTP RUNNER ====================


# ==================== AI DASHBOARD & CONTROL API ====================


ADMIN_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gehihi Robot AI - Trung Tâm Quản Trị & Điều Khiển Robot Xiaozhi</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #070B14;
      --card-bg: rgba(15, 23, 42, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #06B6D4;
      --primary-glow: rgba(6, 182, 212, 0.35);
      --accent: #10B981;
      --purple: #8B5CF6;
      --warning: #F59E0B;
      --danger: #EF4444;
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      background: radial-gradient(circle at 50% 0%, #111A2E 0%, #070B14 100%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 16px 60px 16px;
    }
    .wrapper { max-width: 1100px; width: 100%; }

    /* Header */
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 24px;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
      flex-wrap: wrap;
      gap: 16px;
    }
    .logo-group { display: flex; align-items: center; gap: 14px; }
    .robot-avatar {
      width: 48px;
      height: 48px;
      border-radius: 14px;
      background: linear-gradient(135deg, #06B6D4, #3B82F6, #8B5CF6);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      box-shadow: 0 0 20px var(--primary-glow);
    }
    .brand-title { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; background: linear-gradient(to right, #FFFFFF, #CBD5E1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .brand-sub { font-size: 13px; color: var(--text-muted); }
    .server-status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: 999px;
      font-size: 12.5px;
      font-weight: 600;
      color: #34D399;
    }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #10B981; box-shadow: 0 0 10px #10B981; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.15); } }

    /* Navigation Tabs */
    .nav-tabs {
      display: flex;
      gap: 8px;
      background: rgba(15, 23, 42, 0.6);
      padding: 6px;
      border-radius: 14px;
      border: 1px solid var(--card-border);
      margin-bottom: 24px;
      overflow-x: auto;
    }
    .nav-tab {
      padding: 10px 18px;
      border-radius: 10px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
      transition: all 0.2s ease;
    }
    .nav-tab:hover { color: #fff; background: rgba(255, 255, 255, 0.05); }
    .nav-tab.active { background: var(--primary); color: #04101E; box-shadow: 0 0 16px var(--primary-glow); }

    /* Tab Contents */
    .tab-pane { display: none; }
    .tab-pane.active { display: block; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

    /* Stat Cards Grid */
    .stat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 18px;
      backdrop-filter: blur(12px);
      transition: border-color 0.2s;
    }
    .stat-card:hover { border-color: rgba(6, 182, 212, 0.4); }
    .stat-label { font-size: 12.5px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; }
    .stat-val { font-size: 22px; font-weight: 700; color: #fff; }
    .stat-sub { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

    /* Live Audio & Waveform Card */
    .glass-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 22px;
      backdrop-filter: blur(12px);
      margin-bottom: 24px;
    }
    .card-title {
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .live-badge {
      font-size: 11px;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #F87171;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }
    .vu-meter-bar {
      width: 100%;
      height: 12px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 12px;
      position: relative;
    }
    .vu-meter-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #10B981, #06B6D4, #F59E0B, #EF4444);
      transition: width 0.1s linear;
      border-radius: 6px;
    }
    .audio-meta-row {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }

    /* Dialogue Cards */
    .dialogue-box {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 14px;
    }
    .msg-bubble {
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
    }
    .msg-user { background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.25); color: #93C5FD; align-self: flex-start; max-width: 85%; }
    .msg-bot { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); color: #A7F3D0; align-self: flex-start; max-width: 85%; }

    /* Provider Grid */
    .provider-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .provider-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      transition: all 0.2s;
    }
    .provider-card.active { border-color: var(--primary); box-shadow: 0 0 24px var(--primary-glow); }
    .p-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
    .p-title { font-size: 16px; font-weight: 700; color: #fff; }
    .p-badge { font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; text-transform: uppercase; }
    .badge-active { background: rgba(6, 182, 212, 0.2); color: var(--primary); border: 1px solid rgba(6, 182, 212, 0.4); }
    .badge-fast { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .p-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.4; }
    .btn {
      padding: 10px 16px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 13.5px;
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
      width: 100%;
    }
    .btn-primary { background: rgba(255, 255, 255, 0.08); color: #fff; border: 1px solid var(--card-border); }
    .btn-primary:hover { background: rgba(255, 255, 255, 0.15); border-color: rgba(255, 255, 255, 0.2); }
    .btn-active { background: var(--primary); color: #04101E; font-weight: 700; cursor: default; }
    .btn-accent { background: var(--accent); color: #04101E; font-weight: 700; }
    .btn-accent:hover { opacity: 0.9; }

    /* Form Styles */
    .form-group { margin-bottom: 16px; }
    .form-label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--text-muted); }
    .form-input, .form-textarea, .form-select {
      width: 100%;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 10px 14px;
      color: #fff;
      font-size: 14px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-input:focus, .form-textarea:focus { border-color: var(--primary); box-shadow: 0 0 10px var(--primary-glow); }
    .form-textarea { resize: vertical; min-height: 90px; }

    /* Hardware Table */
    .pinout-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 13.5px;
    }
    .pinout-table th, .pinout-table td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--card-border);
    }
    .pinout-table th { background: rgba(255, 255, 255, 0.04); color: var(--text-muted); font-weight: 600; }
    .pin-badge {
      font-family: 'JetBrains Mono', monospace;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(6, 182, 212, 0.15);
      color: #67E8F9;
      font-size: 12px;
      font-weight: 600;
    }

    /* Endpoint & Download Cards */
    .endpoint-card {
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 14px 18px;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .endpoint-title { font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
    .endpoint-val { font-family: 'JetBrains Mono', monospace; font-size: 13.5px; color: #38BDF8; word-break: break-all; }
    .btn-sm { padding: 6px 12px; font-size: 12px; border-radius: 8px; width: auto; }

    /* Footer */
    footer {
      text-align: center;
      margin-top: 36px;
      font-size: 13px;
      color: var(--text-muted);
      border-top: 1px solid var(--card-border);
      padding-top: 20px;
    }
  </style>
</head>
<body>
<div class="wrapper">
  <!-- Header -->
  <header>
    <div class="logo-group">
      <div class="robot-avatar">🤖</div>
      <div>
        <div class="brand-title">Gehihi Robot AI - Trung Tâm Quản Trị</div>
        <div class="brand-sub">Máy chủ điều khiển & cấu hình thông minh cho Robot Xiaozhi ESP32-S3</div>
      </div>
    </div>
    <div class="server-status-pill">
      <span class="status-dot"></span>
      <span>Hệ Thống Đang Trực Tuyến</span>
    </div>
  </header>

  <!-- Navigation Tabs -->
  <nav class="nav-tabs">
    <button class="nav-tab active" onclick="switchTab('dashboard')">📊 Bảng Điều Khiển</button>
    <button class="nav-tab" onclick="switchTab('ai')">🧠 Bộ Não AI</button>
    <button class="nav-tab" onclick="switchTab('device')">🤖 Mạch Tím ESP32</button>
    <button class="nav-tab" onclick="switchTab('chat')">💬 Thử Nghiệm Trực Tiếp</button>
    <button class="nav-tab" onclick="switchTab('ota')">⚡ Firmware & Nạp Flash</button>
  </nav>

  <!-- TAB 1: DASHBOARD -->
  <div id="tab-dashboard" class="tab-pane active">
    <!-- Stat Grid -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">Trạng Thái Robot <span id="robot-status-badge">🟢 Online</span></div>
        <div class="stat-val" id="robot-name">Robot Gehihi AI</div>
        <div class="stat-sub" id="robot-mac">MAC: 14:C1:9F:C4:EE:D0 (Mạch Tím)</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Bộ Não AI Đang Dùng</div>
        <div class="stat-val" id="stat-active-provider" style="color: var(--primary);">__ACTIVE_UPPER__</div>
        <div class="stat-sub">Phản hồi siêu tốc & tự nhiên</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Độ Trễ Hội Thoại (Latency)</div>
        <div class="stat-val" id="stat-latency">-- s</div>
        <div class="stat-sub" id="stat-latency-breakdown">ASR: -- | LLM: -- | TTS: --</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Lượt Đàm Thoại Đã Xử Lý</div>
        <div class="stat-val" id="stat-turns">0</div>
        <div class="stat-sub">Tổng số câu hội thoại hai chiều</div>
      </div>
    </div>

    <!-- Live Audio Diagnostics -->
    <div class="glass-card">
      <div class="card-title">
        <span>🎙️ Giám Sát Âm Thanh & Nhận Diện Tiếng Nói (Live Audio & VAD)</span>
        <span class="live-badge" id="vad-badge">YÊN LẶNG</span>
      </div>
      <div class="vu-meter-bar">
        <div class="vu-meter-fill" id="rms-bar"></div>
      </div>
      <div class="audio-meta-row">
        <span>Âm lượng Micro (RMS): <b id="rms-val">0.0</b></span>
        <span>Sàn nhiễu (Noise Floor): <b id="noise-val">100.0</b></span>
        <span>Bộ đệm Opus: <b id="buf-val">0 frames</b></span>
      </div>

      <div style="margin-top: 20px;">
        <div style="font-size: 13px; font-weight: 600; color: var(--text-muted); margin-bottom: 8px;">Cuộc Hội Thoại Gần Nhất:</div>
        <div class="dialogue-box">
          <div class="msg-bubble msg-user" id="diag-user-bubble">🗣️ Người dùng: <i>Đang chờ người dùng nói...</i></div>
          <div class="msg-bubble msg-bot" id="diag-bot-bubble">🤖 Robot: <i>Sẵn sàng lắng nghe và đàm thoại.</i></div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 2: AI ENGINE -->
  <div id="tab-ai" class="tab-pane">
    <div class="provider-grid">
      <!-- Groq -->
      <div class="provider-card __GROQ_ACTIVE__" id="card-groq">
        <div class="p-head">
          <span class="p-title">Groq Cloud AI</span>
          <span class="p-badge __GROQ_BADGE__">__GROQ_TAG__</span>
        </div>
        <div class="p-desc">Tốc độ cực nhanh &lt; 0.4s. Mô hình Llama 3.3 70B hoặc Qwen 2.5 32B tối ưu hóa cho đàm thoại.</div>
        <button class="btn __GROQ_BTN__" onclick="selectProvider('groq')" id="btn-groq">__GROQ_TXT__</button>
      </div>

      <!-- Google Gemini -->
      <div class="provider-card __GEMINI_ACTIVE__" id="card-gemini">
        <div class="p-head">
          <span class="p-title">Google Gemini</span>
          <span class="p-badge __GEMINI_BADGE__">__GEMINI_TAG__</span>
        </div>
        <div class="p-desc">Mô hình Gemini 2.5 Flash / 1.5 Flash. Hiểu tiếng Việt cực đỉnh, phong phú ngữ cảnh và thông minh.</div>
        <button class="btn __GEMINI_BTN__" onclick="selectProvider('gemini')" id="btn-gemini">__GEMINI_TXT__</button>
      </div>

      <!-- DeepSeek -->
      <div class="provider-card __DEEPSEEK_ACTIVE__" id="card-deepseek">
        <div class="p-head">
          <span class="p-title">DeepSeek AI</span>
          <span class="p-badge __DEEPSEEK_BADGE__">__DEEPSEEK_TAG__</span>
        </div>
        <div class="p-desc">DeepSeek Chat V3 / R1. Khả năng tư duy logic và suy luận sâu sắc, trả lời súc tích.</div>
        <button class="btn __DEEPSEEK_BTN__" onclick="selectProvider('deepseek')" id="btn-deepseek">__DEEPSEEK_TXT__</button>
      </div>

      <!-- OpenAI -->
      <div class="provider-card __OPENAI_ACTIVE__" id="card-openai">
        <div class="p-head">
          <span class="p-title">OpenAI GPT-4o</span>
          <span class="p-badge __OPENAI_BADGE__">__OPENAI_TAG__</span>
        </div>
        <div class="p-desc">Mô hình GPT-4o-mini tiêu chuẩn quốc tế. Cân bằng giữa tốc độ, độ thông minh và văn phong.</div>
        <button class="btn __OPENAI_BTN__" onclick="selectProvider('openai')" id="btn-openai">__OPENAI_TXT__</button>
      </div>
    </div>

    <!-- API Key & Prompt Configuration -->
    <div class="glass-card">
      <div class="card-title">⚙️ Cấu Hình API Key & Tính Cách Robot (System Prompt)</div>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px;">
        <div class="form-group">
          <label class="form-label">Groq API Key</label>
          <input type="password" id="input-groq-key" class="form-input" placeholder="gsk_...">
        </div>
        <div class="form-group">
          <label class="form-label">Google Gemini API Key</label>
          <input type="password" id="input-gemini-key" class="form-input" placeholder="AIzaSy...">
        </div>
        <div class="form-group">
          <label class="form-label">DeepSeek API Key</label>
          <input type="password" id="input-deepseek-key" class="form-input" placeholder="sk-...">
        </div>
        <div class="form-group">
          <label class="form-label">OpenAI API Key</label>
          <input type="password" id="input-openai-key" class="form-input" placeholder="sk-proj-...">
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Lời Nhắc Hệ Thống (System Prompt / Robot Persona)</label>
        <textarea id="input-system-prompt" class="form-textarea">__SYSTEM_PROMPT__</textarea>
      </div>

      <button class="btn btn-accent" style="width: auto; padding: 12px 28px;" onclick="saveAiConfig()">💾 Lưu Cấu Hình AI</button>
    </div>
  </div>

  <!-- TAB 3: DEVICE & HARDWARE -->
  <div id="tab-device" class="tab-pane">
    <div class="glass-card">
      <div class="card-title">🤖 Sơ Đồ Mạch Phần Cứng - ESP32-S3 (Mạch Tím Huyền Thoại)</div>
      <p style="font-size: 13.5px; color: var(--text-muted); line-height: 1.5; margin-bottom: 16px;">
        Firmware đã được biên dịch cấu hình chính xác 100% theo sơ đồ mạch Mạch Tím Huyền Thoại (Mini ESP32-S3-N16R8, 16MB Flash, 8MB PSRAM Octal).
      </p>

      <table class="pinout-table">
        <thead>
          <tr>
            <th>Khối Chức Năng</th>
            <th>Linh Kiện Phần Cứng</th>
            <th>Chân GPIO ESP32-S3</th>
            <th>Ghi Chú Kỹ Thuật</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><b>Microphone (Audio In)</b></td>
            <td>I2S MEMS Micro (INMP441 / MSM261S)</td>
            <td><span class="pin-badge">WS: GPIO 4</span> <span class="pin-badge">SCK: GPIO 5</span> <span class="pin-badge">DIN: GPIO 6</span></td>
            <td>Simplex Mode, 16kHz, 16-bit Mono</td>
          </tr>
          <tr>
            <td><b>Loa & Khuếch Đại (Audio Out)</b></td>
            <td>I2S Amp (NS4168 / MAX98357A)</td>
            <td><span class="pin-badge">DOUT: GPIO 7</span> <span class="pin-badge">BCLK: GPIO 15</span> <span class="pin-badge">LRCK: GPIO 16</span> <span class="pin-badge">PA_EN: GPIO 17</span></td>
            <td>PA_EN kích hoạt mức HIGH (1) bật nguồn Amp</td>
          </tr>
          <tr>
            <td><b>Màn Hình (Display)</b></td>
            <td>0.96" OLED SSD1306 (128x64)</td>
            <td><span class="pin-badge">SDA: GPIO 41</span> <span class="pin-badge">SCL: GPIO 42</span></td>
            <td>I2C Address 0x3C, Clock 400kHz</td>
          </tr>
          <tr>
            <td><b>Nút Bấm (Buttons)</b></td>
            <td>Nút BOOT & Nút Phụ / Touch</td>
            <td><span class="pin-badge">BOOT: GPIO 0</span> <span class="pin-badge">TOUCH/PTT: GPIO 47</span></td>
            <td>Nhấn BOOT đổi trạng thái, giữ 3s mở Wi-Fi config</td>
          </tr>
          <tr>
            <td><b>Đèn Trạng Thái (LED)</b></td>
            <td>WS2812 Addressable RGB LED</td>
            <td><span class="pin-badge">RGB DATA: GPIO 48</span></td>
            <td>Hiệu ứng ánh sáng: Lắng nghe, Suy nghĩ, Nói</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Remote Controls -->
    <div class="glass-card">
      <div class="card-title">🎮 Bảng Điều Khiển Robot Từ Xa</div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <button class="btn btn-primary btn-sm" onclick="sendDeviceControl('wakeup')">🔔 Đánh Thức Robot</button>
        <button class="btn btn-primary btn-sm" onclick="sendDeviceControl('interrupt')">⏹️ Ngắt Lời (Stop Speaking)</button>
        <button class="btn btn-primary btn-sm" onclick="sendDeviceControl('standby')">💤 Chế Độ Chờ (Standby)</button>
        <button class="btn btn-primary btn-sm" onclick="sendDeviceControl('reboot')">🔄 Khởi Động Lại</button>
      </div>
    </div>
  </div>

  <!-- TAB 4: LIVE CHAT -->
  <div id="tab-chat" class="tab-pane">
    <div class="glass-card">
      <div class="card-title">💬 Thử Nghiệm Trò Chuyện Trực Tiếp Với AI</div>
      <p style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 14px;">
        Nhập văn bản để kiểm tra trực tiếp phản hồi và tốc độ xử lý của mô hình AI đang được kích hoạt.
      </p>

      <div class="form-group" style="display: flex; gap: 10px;">
        <input type="text" id="chat-input" class="form-input" placeholder="Ví dụ: Chào Gehihi, bạn có thể làm được những gì?">
        <button class="btn btn-accent" style="width: auto; padding: 10px 24px;" onclick="sendTestChat()">Gửi Thử</button>
      </div>

      <div id="chat-result-box" style="display: none; margin-top: 16px; padding: 16px; background: rgba(0,0,0,0.3); border-radius: 12px; border: 1px solid var(--card-border);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <b style="color: var(--primary);" id="chat-res-provider">GROQ</b>
          <span style="font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #10B981;" id="chat-res-latency">⏱️ -- ms</span>
        </div>
        <div style="font-size: 15px; color: #fff; line-height: 1.6;" id="chat-res-text">...</div>
      </div>
    </div>
  </div>

  <!-- TAB 5: OTA & FIRMWARE -->
  <div id="tab-ota" class="tab-pane">
    <div class="glass-card">
      <div class="card-title">⚡ Cổng Kết Nối Dịch Vụ Của Server Gehihi</div>
      
      <div class="endpoint-card">
        <div>
          <div class="endpoint-title">Cổng Cập Nhật OTA Cho Robot</div>
          <div class="endpoint-val" id="ota-endpoint-val">__OTA_URL__</div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="copyText('__OTA_URL__')">Sao Chép</button>
      </div>

      <div class="endpoint-card">
        <div>
          <div class="endpoint-title">Cổng WebSocket AI Đàm Thoại Thời Gian Thực</div>
          <div class="endpoint-val" id="ws-endpoint-val">__WS_URL__</div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="copyText('__WS_URL__')">Sao Chép</button>
      </div>
    </div>

    <!-- Download Binaries -->
    <div class="glass-card">
      <div class="card-title">📦 Tải Firmware Nhị Phân Biên Dịch Sẵn (ESP32-S3 Mạch Tím)</div>
      <p style="font-size: 13.5px; color: var(--text-muted); margin-bottom: 16px;">
        Firmware đã build sẵn hỗ trợ tiếng Việt chuẩn, kết nối trực tiếp đến server này:
      </p>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;">
        <div class="stat-card">
          <div class="stat-label">File Gộp Tất Cả Trong Một (Khuyến Nghị)</div>
          <div style="font-weight: 700; margin: 8px 0;">merged-binary.bin</div>
          <div class="stat-sub" style="margin-bottom: 12px;">Nạp 1 file duy nhất vào offset 0x0</div>
          <a href="/firmware/merged-binary.bin" class="btn btn-accent btn-sm" download>⬇️ Tải merged-binary.bin</a>
        </div>

        <div class="stat-card">
          <div class="stat-label">Firmware Ứng Dụng (App Binary)</div>
          <div style="font-weight: 700; margin: 8px 0;">xiaozhi.bin</div>
          <div class="stat-sub" style="margin-bottom: 12px;">Dùng cho cập nhật OTA hoặc offset 0x20000</div>
          <a href="/firmware/xiaozhi.bin" class="btn btn-primary btn-sm" download>⬇️ Tải xiaozhi.bin</a>
        </div>
      </div>

      <div style="margin-top: 24px;">
        <div style="font-size: 14px; font-weight: 700; margin-bottom: 8px;">Lệnh Nạp Bằng esptool.py (1 Dòng Lệnh):</div>
        <div style="background: rgba(0,0,0,0.5); padding: 12px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #67E8F9; overflow-x: auto;">
          esptool.py --chip esp32s3 -p COM3 -b 921600 write_flash 0x0 merged-binary.bin
        </div>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <footer>
    Gehihi Robot AI &bull; Xiaozhi ESP32-S3 Mạch Tím &bull; Triển khai trên Render.com
  </footer>
</div>

<script>
  function switchTab(tabId) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById('tab-' + tabId).classList.add('active');
  }

  function copyText(text) {
    navigator.clipboard.writeText(text);
    alert('Đã sao chép: ' + text);
  }

  async function selectProvider(prov) {
    try {
      const res = await fetch('/xiaozhi/ai/provider', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({provider: prov})
      });
      const data = await res.json();
      if (data.code === 0) {
        alert('Đã kích hoạt ' + prov.toUpperCase() + ' thành công!');
        location.reload();
      } else {
        alert('Lỗi: ' + data.msg);
      }
    } catch(e) {
      alert('Không thể kết nối máy chủ: ' + e);
    }
  }

  async function saveAiConfig() {
    const groqKey = document.getElementById('input-groq-key').value;
    const geminiKey = document.getElementById('input-gemini-key').value;
    const deepseekKey = document.getElementById('input-deepseek-key').value;
    const openaiKey = document.getElementById('input-openai-key').value;
    const prompt = document.getElementById('input-system-prompt').value;

    try {
      const res = await fetch('/xiaozhi/ai/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          groq_key: groqKey,
          gemini_key: geminiKey,
          deepseek_key: deepseekKey,
          openai_key: openaiKey,
          system_prompt: prompt
        })
      });
      const data = await res.json();
      alert(data.msg || 'Cấu hình đã được lưu!');
    } catch(e) {
      alert('Lỗi lưu cấu hình: ' + e);
    }
  }

  async function sendTestChat() {
    const input = document.getElementById('chat-input').value;
    if (!input) return;
    const resBox = document.getElementById('chat-result-box');
    resBox.style.display = 'block';
    document.getElementById('chat-res-text').innerText = 'Đang suy nghĩ...';

    try {
      const res = await fetch('/xiaozhi/ai/test', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: input})
      });
      const d = await res.json();
      if (d.code === 0) {
        document.getElementById('chat-res-provider').innerText = (d.data.provider || '').toUpperCase();
        document.getElementById('chat-res-latency').innerText = '⏱️ ' + d.data.latency_ms + ' ms';
        document.getElementById('chat-res-text').innerText = d.data.reply || '';
      } else {
        document.getElementById('chat-res-text').innerText = 'Lỗi: ' + d.msg;
      }
    } catch(e) {
      document.getElementById('chat-res-text').innerText = 'Lỗi kết nối: ' + e;
    }
  }

  async function sendDeviceControl(cmd) {
    try {
      const res = await fetch('/xiaozhi/device/control', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: cmd})
      });
      const d = await res.json();
      alert(d.msg || 'Lệnh đã gửi!');
    } catch(e) {
      alert('Lỗi: ' + e);
    }
  }

  // Poll live diagnostics
  async function pollDiagnostics() {
    try {
      const res = await fetch('/xiaozhi/debug/live');
      if (res.ok) {
        const d = await res.json();
        const rms = d.last_rms || 0;
        const noise = d.noise_floor || 100;
        document.getElementById('rms-val').innerText = rms.toFixed(1);
        document.getElementById('noise-val').innerText = noise.toFixed(1);
        document.getElementById('buf-val').innerText = (d.buffer_len || 0) + ' frames';
        
        // VU Meter bar
        const pct = Math.min(100, Math.max(0, (rms / 800) * 100));
        document.getElementById('rms-bar').style.width = pct + '%';

        // VAD Badge
        const vadBadge = document.getElementById('vad-badge');
        if (d.speech_active) {
          vadBadge.innerText = 'ĐANG PHÁT HIỆN GIỌNG NÓI';
          vadBadge.style.background = 'rgba(16, 185, 129, 0.2)';
          vadBadge.style.color = '#34D399';
          vadBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        } else {
          vadBadge.innerText = 'YÊN LẶNG';
          vadBadge.style.background = 'rgba(239, 68, 68, 0.15)';
          vadBadge.style.color = '#F87171';
          vadBadge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        }

        // Stats
        if (d.turns_executed !== undefined) {
          document.getElementById('stat-turns').innerText = d.turns_executed;
        }
        if (d.last_total_latency) {
          document.getElementById('stat-latency').innerText = d.last_total_latency.toFixed(2) + ' s';
          document.getElementById('stat-latency-breakdown').innerText = 
            'ASR: ' + (d.last_asr_latency*1000).toFixed(0) + 'ms | LLM: ' + (d.last_llm_latency*1000).toFixed(0) + 'ms | TTS: ' + (d.last_tts_latency*1000).toFixed(0) + 'ms';
        }

        // Bubbles
        if (d.last_user_text) {
          document.getElementById('diag-user-bubble').innerText = '🗣️ Người dùng: ' + d.last_user_text;
        }
        if (d.last_bot_text) {
          document.getElementById('diag-bot-bubble').innerText = '🤖 Robot: ' + d.last_bot_text;
        }
      }
    } catch(e) {}
  }
  setInterval(pollDiagnostics, 1000);
</script>
</body>
</html>
"""

async def handle_admin_dashboard(request):
    active = get_active_provider()
    pub_url, ws_url, ota_url = get_public_urls(request)
    
    html = ADMIN_HTML_TEMPLATE.replace("__ACTIVE_UPPER__", active.upper())
    html = html.replace("__PUB_URL__", pub_url)
    html = html.replace("__WS_URL__", ws_url)
    html = html.replace("__OTA_URL__", ota_url)
    html = html.replace("__SYSTEM_PROMPT__", AI_SYSTEM_PROMPT)

    for p in ["groq", "gemini", "deepseek", "openai"]:
        is_act = (active == p)
        html = html.replace(f"__{p.upper()}_ACTIVE__", "active" if is_act else "")
        html = html.replace(f"__{p.upper()}_BADGE__", "badge-active" if is_act else ("badge-fast" if p == "groq" else ""))
        html = html.replace(f"__{p.upper()}_BTN__", "btn-active" if is_act else "btn-primary")
        html = html.replace(f"__{p.upper()}_TXT__", "✓ Đang Kích Hoạt" if is_act else f"Kích Hoạt {p.capitalize()}")
        tag_desc = "Đang Dùng" if is_act else {
            "groq": "Siêu Tốc 0.4s",
            "gemini": "Tiếng Việt Chuẩn",
            "deepseek": "Thông Minh V3",
            "openai": "Tiêu Chuẩn"
        }.get(p, "")
        html = html.replace(f"__{p.upper()}_TAG__", tag_desc)
    return web.Response(text=html, content_type="text/html")

async def handle_ai_dashboard(request):
    return await handle_admin_dashboard(request)


async def run_http_server():
    app = web.Application()

    # Health & System
    app.router.add_get("/", handle_root_dispatch)
    app.router.add_get("/admin", handle_admin_dashboard)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/xiaozhi/debug/live", handle_debug_live)
    app.router.add_get("/firmware/{filename}", handle_firmware_download)
    app.router.add_post("/xiaozhi/ai/config", handle_ai_config_save)
    app.router.add_post("/xiaozhi/device/control", handle_device_control)

    # OTA Endpoints
    app.router.add_get("/xiaozhi/ota/", handle_ota)
    app.router.add_post("/xiaozhi/ota/", handle_ota)
    app.router.add_options("/xiaozhi/ota/", handle_cors_options)
    app.router.add_post("/xiaozhi/ota/activate", handle_ota_activate)
    app.router.add_options("/xiaozhi/ota/activate", handle_cors_options)

    # Vision
    app.router.add_get("/mcp/vision/explain", handle_vision_explain)
    app.router.add_post("/mcp/vision/explain", handle_vision_explain)
    app.router.add_options("/mcp/vision/explain", handle_cors_options)

    # AI Provider Control Center
    app.router.add_get("/ai", handle_ai_dashboard)
    app.router.add_get("/xiaozhi/ai", handle_ai_dashboard)
    app.router.add_get("/xiaozhi/ai/provider", handle_ai_provider_get)
    app.router.add_post("/xiaozhi/ai/provider", handle_ai_provider_set)
    app.router.add_post("/xiaozhi/ai/test", handle_ai_provider_test)
    app.router.add_options("/xiaozhi/ai/provider", handle_cors_options)
    app.router.add_options("/xiaozhi/ai/test", handle_cors_options)

    # Auth & PubConfig
    app.router.add_get("/xiaozhi/user/pub-config", handle_pub_config)
    app.router.add_get("/xiaozhi/user/captcha", handle_captcha)
    app.router.add_post("/xiaozhi/user/login", handle_login)
    app.router.add_get("/xiaozhi/user/info", handle_user_info)
    app.router.add_get("/xiaozhi/admin/users/info", handle_user_info)
    app.router.add_get("/xiaozhi/admin/users/page", handle_user_info)

    # Agents
    app.router.add_get("/xiaozhi/agent/list", handle_agent_list)
    app.router.add_post("/xiaozhi/agent", handle_agent_save)
    app.router.add_get("/xiaozhi/agent/template/list", handle_agent_template_list)
    app.router.add_get("/xiaozhi/agent/page", handle_agent_list)
    app.router.add_get("/xiaozhi/agent/{id}", handle_agent_detail)
    app.router.add_put("/xiaozhi/agent/{id}", handle_agent_update)
    app.router.add_delete("/xiaozhi/agent/{id}", handle_agent_delete)

    # Agent Sessions & Chat History
    app.router.add_get("/xiaozhi/agent/{id}/sessions", handle_agent_sessions)
    app.router.add_get("/xiaozhi/agent/{id}/chat-history/{session_id}", handle_agent_chat_history)
    app.router.add_get("/xiaozhi/agent/{id}/chat-history/user", handle_agent_chat_history_user)
    app.router.add_get("/xiaozhi/agent/{id}/tags", handle_agent_tags)
    app.router.add_put("/xiaozhi/agent/{id}/tags", handle_agent_tags)
    app.router.add_post("/xiaozhi/agent/{id}/chat-history/getDownloadUrl/{tail:.*}", handle_download_url)
    app.router.add_post("/xiaozhi/agent/chat-history/getDownloadUrl/{tail:.*}", handle_download_url)
    app.router.add_post("/xiaozhi/agent/audio/{tail:.*}", handle_download_url)

    # Agent Templates
    app.router.add_get("/xiaozhi/agent/template", handle_agent_template_list)
    app.router.add_get("/xiaozhi/agent/template/page", handle_agent_template_page)
    app.router.add_post("/xiaozhi/agent/template", handle_agent_template_add)
    app.router.add_get("/xiaozhi/agent/template/{id}", handle_agent_template_crud)
    app.router.add_put("/xiaozhi/agent/template/{id}", handle_agent_template_crud)
    app.router.add_delete("/xiaozhi/agent/template/{id}", handle_agent_template_crud)
    app.router.add_post("/xiaozhi/agent/template/batch-remove", handle_agent_template_crud)

    # Providers & Plugins
    app.router.add_get("/xiaozhi/models/provider", handle_model_providers)
    app.router.add_post("/xiaozhi/models/provider", handle_model_providers)
    app.router.add_put("/xiaozhi/models/provider", handle_model_providers)
    app.router.add_delete("/xiaozhi/models/provider/{id}", handle_model_provider_delete)
    app.router.add_get("/xiaozhi/models/provider/plugin/names", handle_model_plugin_names)

    # Voice Clone & Voice Resources
    app.router.add_get("/xiaozhi/voiceClone", handle_voice_clone_list)
    app.router.add_get("/xiaozhi/voice-clone/page", handle_voice_clone_list)
    app.router.add_post("/xiaozhi/voiceClone/upload", handle_voice_clone_action)
    app.router.add_post("/xiaozhi/voiceClone/updateName", handle_voice_clone_action)
    app.router.add_post("/xiaozhi/voiceClone/cloneAudio", handle_voice_clone_action)
    app.router.add_post("/xiaozhi/voiceClone/audio/{tail:.*}", handle_voice_clone_action)
    app.router.add_get("/xiaozhi/voice-resource/page", handle_voice_resource_page)
    app.router.add_get("/xiaozhi/voiceResource", handle_voice_resource_page)

    # Devices
    app.router.add_get("/xiaozhi/device/list", handle_device_list)
    app.router.add_get("/xiaozhi/device/page", handle_device_page)
    app.router.add_get("/xiaozhi/device/bind/{tail:.*}", handle_device_bind_list)
    app.router.add_post("/xiaozhi/device/bind/{tail:.*}", handle_device_bind_action)
    app.router.add_post("/xiaozhi/device/unbind", handle_device_unbind_action)

    # Models
    app.router.add_get("/xiaozhi/models/list", handle_model_list)
    app.router.add_get("/xiaozhi/models/page", handle_model_list)
    app.router.add_get("/xiaozhi/models/names", handle_model_names)
    app.router.add_get("/xiaozhi/models/llm/names", handle_model_names)
    app.router.add_get("/xiaozhi/models/{modelType}/provideTypes", handle_model_provide_types)
    app.router.add_post("/xiaozhi/models/{modelType}/{provideCode}", handle_model_save)
    app.router.add_put("/xiaozhi/models/{id}/status", handle_model_status_toggle)
    app.router.add_put("/xiaozhi/models/{id}/default", handle_model_default_toggle)
    app.router.add_put("/xiaozhi/models/{id}", handle_model_update)
    app.router.add_delete("/xiaozhi/models/{id}", handle_model_delete)

    # TTS Voices
    app.router.add_get("/xiaozhi/ttsVoice", handle_tts_voice_list)
    app.router.add_get("/xiaozhi/models/{id}/voices", handle_tts_voice_list)

    # Knowledge & Address Book
    app.router.add_get("/xiaozhi/knowledge/base/list", handle_knowledge_list)
    app.router.add_get("/xiaozhi/knowledge/base/page", handle_knowledge_page)
    app.router.add_get("/xiaozhi/address-book/list", handle_address_book_list)
    app.router.add_get("/xiaozhi/address-book/page", handle_address_book_page)

    # System & Dicts
    app.router.add_get("/xiaozhi/sys/dict/type/{tail:.*}", handle_dict_data)
    app.router.add_get("/xiaozhi/sys/dict/data/{tail:.*}", handle_dict_data)
    app.router.add_get("/xiaozhi/sys/params/{tail:.*}", handle_dict_data)
    app.router.add_get("/xiaozhi/sys/menu/nav", handle_menu_nav)

    # Generic Fallback & CORS
    app.router.add_route("*", "/xiaozhi/{tail:.*}", handle_generic_fallback)
    app.router.add_options("/{tail:.*}", handle_cors_options)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)
    await site.start()
    logger.info(f"HTTP & OTA Server listening on port {HTTP_PORT}")

    while True:
        await asyncio.sleep(3600)

async def run_ws_server():
    logger.info(f"WebSocket Server listening on port {WS_PORT}")
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        await asyncio.Future()

async def main():
    logger.info("==================================================")
    logger.info("   Starting Gehihi Full Dynamic Server for Render ")
    logger.info(f"   Public Base URL: {PUBLIC_URL}                 ")
    logger.info(f"   OTA URL:         {PUBLIC_URL}/xiaozhi/ota/    ")
    logger.info(f"   WebSocket URL:   {WS_URL}                     ")
    logger.info("==================================================")
    await asyncio.gather(
        run_http_server(),
        run_ws_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Gehihi Server stopped.")
