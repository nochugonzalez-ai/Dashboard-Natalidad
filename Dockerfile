# 1. Imagen base
FROM python:3.10-slim

# 2. Directorio de trabajo

WORKDIR /app

# 3. Copiar e instalar dependencias:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el script:
COPY collector.py .

# 5. Comando de ejecución:
CMD ["python", "collector.py"]
