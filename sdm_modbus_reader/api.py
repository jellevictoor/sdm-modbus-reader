"""
FastAPI web interface for SDM meter data
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from sdm_modbus_reader.adapters.memory_repository import InMemoryReadingRepository

# Global repository instance shared with main.py
# In a production app, this would be injected via dependency injection
_repository = None

def set_repository(repository: InMemoryReadingRepository):
    """Set the repository instance to use"""
    global _repository
    _repository = repository

app = FastAPI(title="SDM Meter Monitor")

# Setup Jinja2 templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/api/meters")
async def get_meters():
    """Get all meter data"""
    if _repository is None:
        return {}

    readings = _repository.get_all()
    return {meter_id: reading.to_dict() for meter_id, reading in readings.items()}


@app.get("/api/meters/{meter_id}")
async def get_meter(meter_id: int):
    """Get specific meter data"""
    if _repository is None:
        return {"error": "Repository not initialized"}

    reading = _repository.get_by_meter_id(meter_id)
    if reading is None:
        return {"error": "Meter not found"}
    return reading.to_dict()


@app.get("/")
async def root(request: Request):
    """Serve the main HTML page"""
    return templates.TemplateResponse("index.html", {"request": request})