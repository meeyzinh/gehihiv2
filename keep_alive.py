#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Ping tự động giữ cho Server Render (gehihiv2.onrender.com) hoạt động liên tục 24/7.
Cơ chế: Render miễn phí sẽ tắt (sleep) sau 15 phút nếu không có request.
Script này gửi HTTP GET request mỗi 10 phút để server không bao giờ bị sleep!
"""

import sys
import time
import datetime
import urllib.request
import urllib.error

TARGET_URL = "https://gehihiv2.onrender.com/api/health"
FALLBACK_URL = "https://gehihiv2.onrender.com/"
PING_INTERVAL_SECONDS = 600  # 10 phút (Render sleep sau 15 phút)

def ping_server(url: str, timeout: int = 30) -> tuple[int, float, str]:
    start_time = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "GMbot-KeepAlive/2.0 (+https://gehihiv2.onrender.com)"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            elapsed = time.time() - start_time
            body = response.read().decode("utf-8", errors="ignore")
            return status, elapsed, body
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_time
        return e.code, elapsed, str(e)
    except Exception as e:
        elapsed = time.time() - start_time
        return 0, elapsed, str(e)

def main():
    print("=" * 65)
    print("🚀 GMBOT RENDER 24/7 KEEP-ALIVE SERVICE")
    print(f"🎯 Mục tiêu: {TARGET_URL}")
    print(f"⏱ Chu kỳ ping: Mỗi {PING_INTERVAL_SECONDS // 60} phút")
    print("=" * 65)

    count = 0
    while True:
        count += 1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] #{count} Đang gửi request tới Server Render...")
        
        status, elapsed, body = ping_server(TARGET_URL)
        
        if status == 200:
            print(f"[{now}] ✓ THÀNH CÔNG: HTTP 200 OK (Thời gian: {elapsed:.2f}s)")
            print(f"     Nội dung: {body.strip()[:100]}")
        else:
            print(f"[{now}] ⚠ Endpoint /api/health trả về status {status} (Lỗi: {body[:80]}). Đang ping trang chủ...")
            status2, elapsed2, _ = ping_server(FALLBACK_URL)
            if 200 <= status2 < 400:
                print(f"[{now}] ✓ Trang chủ phản hồi tốt: HTTP {status2} ({elapsed2:.2f}s)")
            else:
                print(f"[{now}] ❌ Lỗi kết nối tới Render ({elapsed2:.2f}s): Có thể server đang khởi động lại.")

        next_ping = datetime.datetime.now() + datetime.timedelta(seconds=PING_INTERVAL_SECONDS)
        print(f"💤 Tạm nghỉ 10 phút. Lần ping tiếp theo vào lúc: {next_ping.strftime('%H:%M:%S')}")
        
        try:
            time.sleep(PING_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n[DỪNG] Đã dừng tiến trình Keep-Alive theo yêu cầu người dùng.")
            break

if __name__ == "__main__":
    main()
