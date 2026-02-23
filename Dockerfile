FROM python:3.12-slim

LABEL maintainer="FunkPilot OE8YML"
LABEL description="BandWacht - OpenWebRX Band Monitor"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY bandwacht.py bandwacht_multi.py ./

# Create dirs
RUN mkdir -p /app/recordings /app/config

# Volume for recordings and config
VOLUME ["/app/recordings", "/app/config"]

# Default: use config file
ENTRYPOINT ["python", "bandwacht.py"]
CMD ["--config", "/app/config/bandwacht.json"]
