#!/usr/bin/env python3
"""
Run both the SDM reader and FastAPI server
"""
import sys
import threading
import uvicorn
from .sdm_modbus_reader import app as typer_app


def run_reader():
    """Run the modbus reader in a thread"""
    # Typer app expects sys.argv to be set
    typer_app()


def run_api(port=8000):
    """Run the FastAPI server"""
    uvicorn.run(
        "sdm_modbus_reader.api:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


def main():
    """Main entrypoint that runs both services"""
    # Extract --api-port if present
    api_port = 8000
    if "--api-port" in sys.argv:
        idx = sys.argv.index("--api-port")
        if idx + 1 < len(sys.argv):
            try:
                api_port = int(sys.argv[idx + 1])
            except ValueError:
                pass

    # Start reader in background thread
    reader_thread = threading.Thread(target=run_reader, daemon=True)
    reader_thread.start()

    # Run API in main thread
    run_api(port=api_port)


if __name__ == "__main__":
    main()