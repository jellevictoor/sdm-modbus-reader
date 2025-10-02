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

# Run the script
CMD ["python", "-m", "sdm_modbus_reader.sdm_modbus_reader"]