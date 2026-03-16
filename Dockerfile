# 1. Imagen base: Usamos una imagen oficial de Python ligera.
FROM python:3.10-slim

# 2. Directorio de trabajo: Establecemos dónde vivirá nuestro código
#    dentro del contenedor.
WORKDIR /app

# 3. Copiar e instalar dependencias:
#    Copiamos solo el archivo de requisitos primero para aprovechar
#    el caché de capas de Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el script:
#    Copiamos nuestro script de Python al directorio /app.
COPY collector.py .

# 5. Comando de ejecución:
#    Este es el comando que se ejecutará cuando inicie el contenedor.
#    Es lo mismo que escribir "python collector.py" en la terminal.
CMD ["python", "collector.py"]