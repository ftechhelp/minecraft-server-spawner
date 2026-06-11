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

# Start Docker daemon, then start the web app in the foreground.
# Stale pid files survive a plain `docker restart` and make the inner
# dockerd fail with "containerd is still running" / startup timeout, so
# remove them first. Then wait (up to 60s) for the daemon to actually
# answer instead of sleeping a fixed 10s.
CMD ["sh", "-c", "rm -f /var/run/docker.pid /var/run/docker/containerd/containerd.pid; dockerd-entrypoint.sh & i=0; until docker info >/dev/null 2>&1 || [ $i -ge 60 ]; do i=$((i+1)); sleep 1; done; python app.py"]
