#!/usr/bin/env python3
"""
Run both the SDM reader and FastAPI server
"""
import threading
import uvicorn
from .sdm_modbus_reader import main as reader_main


def run_reader():
    """Run the modbus reader in a thread"""
    reader_main()


def run_api():
    """Run the FastAPI server"""
    uvicorn.run(
        "sdm_modbus_reader.api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    # Start reader in background thread
    reader_thread = threading.Thread(target=run_reader, daemon=True)
    reader_thread.start()

    # Run API in main thread
    run_api()