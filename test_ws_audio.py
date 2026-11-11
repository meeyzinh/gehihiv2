import asyncio
import websockets
import json

async def test():
    uri = 'wss://gehihiv2.onrender.com/ws/device'
    headers = {'device-id': '14:c1:9f:c4:ee:d0'}
    print("Connecting to", uri)
    async with websockets.connect(uri, additional_headers=headers) as ws:
        h1 = await ws.recv()
        print('Server Hello 1:', h1)

        # Gửi hello từ client
        client_hello = {
            "type": "hello",
            "version": 1,
            "transport": "websocket",
            "audio_params": {
                "format": "opus",
                "sample_rate": 16000,
                "channels": 1,
                "frame_duration": 60
            }
        }
        await ws.send(json.dumps(client_hello))

        h2 = await ws.recv()
        print('Server Hello 2:', h2)

        # Trigger listen
        await ws.send(json.dumps({"type": "listen", "state": "start", "mode": "auto"}))
        print("Sent listen start")

        # Gửi 10 frame âm thanh giả lập (silence opus frame: 0xf8, 0xff, 0xfe)
        # hoặc gửi câu lệnh văn bản nếu hỗ trợ
        for _ in range(5):
            await ws.send(bytes([0xf8, 0xff, 0xfe]))
            await asyncio.sleep(0.06)

        await ws.send(json.dumps({"type": "listen", "state": "stop"}))
        print("Sent listen stop")

        # Đợi phản hồi
        for i in range(30):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                if isinstance(msg, bytes):
                    print(f"[{i}] BYTES: len={len(msg)}, hex={msg[:20].hex()}")
                else:
                    print(f"[{i}] TEXT: {msg}")
            except asyncio.TimeoutError:
                print("No more messages")
                break

asyncio.run(test())
