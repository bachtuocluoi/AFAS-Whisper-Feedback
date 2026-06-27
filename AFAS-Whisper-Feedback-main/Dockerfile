FROM python:3.11-slim

# ffmpeg for openai-whisper; default-jre-headless for language_tool_python
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper small.en model so the first request isn't slow
RUN python -c "import whisper; whisper.load_model('small.en')"

COPY . .

EXPOSE 8100

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8100"]
