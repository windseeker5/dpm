FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Create non-root user and set ownership
# UID 1000 matches typical Linux user IDs for compatibility
RUN useradd -m -u 1000 minipass && \
    mkdir -p /app/static/uploads/avatars && \
    mkdir -p /app/static/uploads/passports && \
    mkdir -p /app/static/uploads/surveys && \
    mkdir -p /app/static/backups && \
    chown -R minipass:minipass /app

# Run as non-root user for security and proper file permissions
USER minipass

EXPOSE 8889
CMD ["gunicorn", "--workers=2", "--threads=4", "--bind=0.0.0.0:8889", "app:app"]
