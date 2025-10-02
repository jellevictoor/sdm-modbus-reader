FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY sdm_modbus_reader ./sdm_modbus_reader

# Install Python dependencies
RUN pip install --no-cache-dir .

# Expose the web interface port
EXPOSE 8000

# Run both the modbus reader and web API
CMD ["python", "-m", "sdm_modbus_reader.run"]