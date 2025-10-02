FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add user to dialout group for serial port access
RUN usermod -a -G dialout root

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY sdm_modbus_reader ./sdm_modbus_reader
COPY entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Install Python dependencies
RUN pip install --no-cache-dir .

# Expose the web interface port
EXPOSE 8000

# Use entrypoint to pass arguments correctly
ENTRYPOINT ["./entrypoint.sh"]

# Default arguments (can be overridden in docker-compose)
CMD []