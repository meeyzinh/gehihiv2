# ===================================================
# Gehihiv2 Server - Dockerfile cho Render.com (Free Tier 512MB RAM)
# Tích hợp FastAPI + WebSocket + Jinja2 Web Dashboard + YouTube Music (FFmpeg & Opus)
# ===================================================

FROM python:3.11-slim-bookworm

# Cài đặt curl, FFmpeg và Libopus cho stream nhạc YouTube
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ffmpeg \
        libopus0 \
        libopus-dev \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app

WORKDIR /app

# Cài đặt Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Sao chép toàn bộ mã nguồn
COPY . /app/

# Biến môi trường mặc định (Render tự truyền PORT động)
ENV PORT=10000
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 10000

# Khởi chạy server
CMD ["python", "server.py"]
