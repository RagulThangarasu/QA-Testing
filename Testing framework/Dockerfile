FROM python:3.10-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1     PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Install system deps for playwright and opencv
RUN apt-get update && apt-get install -y     wget gnupg ca-certificates fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0     libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2     libgbm1 libasound2 libxshmfence1 libjpeg62-turbo libpng16-16     && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt     && python -m playwright install --with-deps

COPY . /app

EXPOSE 7860
CMD ["python", "app.py"]
