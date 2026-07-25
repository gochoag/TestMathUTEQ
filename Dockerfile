FROM python:3.10-slim

WORKDIR /app                                                                                                                                             

RUN apt-get update && \                                                                                                                                  
  apt-get install -y --no-install-recommends \                                                                                                         
  build-essential \                                                                                                                                  
  pkg-config \                                                                                                                                       
  default-libmysqlclient-dev \                                                                                                                       
  libssl-dev \                                                                                                                                       
  libffi-dev \                                                                                                                                       
  curl \                                                                                                                                             
  && rm -rf /var/lib/apt/lists/*                                                                                                                       

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/                                                                                         

COPY pyproject.toml uv.lock ./                                                                                                                           

RUN uv sync --frozen --no-cache                                                                                                                          

ENV PATH="/app/.venv/bin:$PATH" \                                                                                                                        
  PYTHONDONTWRITEBYTECODE=1 \                                                                                                                          
  PYTHONUNBUFFERED=1                                                                                                                                   

COPY . .                                                                                                                                                 

EXPOSE 8000                                                                                                                                              

CMD ["python", "matholymp/manage.py", "runserver", "0.0.0.0:8000"] 
