FROM docker:dind

# Install Python, pip, and other required dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    tzdata \
    && python3 -m venv /opt/venv

# Make sure we use the virtualenv's pip
ENV PATH="/opt/venv/bin:$PATH"

# Install required Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DOCKER_HOST=unix:///var/run/docker.sock
ENV TZ=America/Vancouver

# Create a directory for spawn data
RUN mkdir -p /app/spawns
RUN mkdir -p /app/backups

# Start Docker daemon, then start the web app in the foreground
CMD ["sh", "-c", "dockerd-entrypoint.sh & sleep 10 && python app.py"]
