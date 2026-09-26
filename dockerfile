FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Create non-root user and set ownership
# UID 1000 matches typical Linux user IDs for compatibility
RUN useradd -m -u 1000 minipass && \
    mkdir -p /app/static/uploads/avatars && \
    mkdir -p /app/static/uploads/passports && \
    mkdir -p /app/static/uploads/surveys && \
    chown -R minipass:minipass /app

# Run as non-root user for security and proper file permissions
USER minipass

EXPOSE 8889
# --timeout 120: the "Check for new payments now" button runs the Interac inbox scan inside the
# request, which can take longer than gunicorn's 30s default, and a timeout kills the worker mid-run.
CMD ["gunicorn", "--workers=2", "--threads=4", "--timeout=120", "--bind=0.0.0.0:8889", "app:app"]
