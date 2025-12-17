FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      pkg-config \
      default-libmysqlclient-dev \
      libssl-dev \
      libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Debug: mostrar contenido
RUN ls -la /app && ls -la /app/matholymp || echo "matholymp no existe"

EXPOSE 8000
CMD ["python", "matholymp/manage.py", "runserver", "0.0.0.0:8000"]
