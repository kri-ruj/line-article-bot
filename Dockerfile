# Use Python slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install gsutil for Google Cloud Storage access
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-sdk \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY app_firestore_final.py .
COPY requirements_firestore.txt requirements.txt
COPY .env.production .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for database (Cloud Run uses /tmp)
RUN mkdir -p /tmp

# Set environment variables
ENV PORT=8080
ENV DB_PATH=/tmp/articles.db
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the application
CMD ["python", "app_firestore_final.py"]