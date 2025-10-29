# ---------- BASE IMAGE ----------
FROM python:3.10-slim

# ---------- LABELS ----------
LABEL maintainer="Aditya Kale"
LABEL image="digitaltiranga:1.0"
LABEL version="2.0"
LABEL description="Flask app for fornation (Digital Tiranga)"

# ---------- ENVIRONMENT ----------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME_DIR=/var/www/FLASKAPPS/digital
ENV PORT=8080

# ---------- SET WORK DIRECTORY ----------
WORKDIR $HOME_DIR

# ---------- COPY FILES ----------
COPY requirements.txt .
COPY ./ .

# ---------- INSTALL DEPENDENCIES ----------
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install flask-socketio textblob reportlab requests Pillow pygame

# ---------- PERMISSIONS ----------
RUN chmod -R 755 $HOME_DIR

# ---------- EXPOSE PORT ----------
EXPOSE 8080

# ---------- RUN THE APPLICATION ----------
# Flask must listen on 0.0.0.0 and use $PORT
CMD ["python", "app.py"]
