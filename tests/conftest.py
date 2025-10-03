"""
Pytest configuration and shared fixtures
"""
import pytest
from datetime import datetime
from sdm_modbus_reader.domain.models import MeterType, MeterConfig, MeterReading


@pytest.fixture
def sdm120_config():
    """Standard SDM120 meter configuration"""
    return MeterConfig(
        meter_type=MeterType.SDM120,
        address=101,
        display_name="Test SDM120",
        slug="test-sdm120"
    )


@pytest.fixture
def sdm630_config():
    """Standard SDM630 meter configuration"""
    return MeterConfig(
        meter_type=MeterType.SDM630,
        address=100,
        display_name="Test SDM630",
        slug="test-sdm630"
    )


@pytest.fixture
def sample_sdm120_data():
    """Sample data from SDM120 meter"""
    return {
        "Voltage": 230.5,
        "Current": 1.234,
        "Power": 284.5,
        "ApparentPower": 299.0,
        "ReactivePower": 89.3,
        "Cosphi": 0.95,
        "PhaseAngle": 18.2,
        "Frequency": 50.0,
        "Import": 1234.5,
        "Export": 0.0,
        "Sum": 1234.5
    }


@pytest.fixture
def sample_sdm630_data():
    """Sample data from SDM630 meter"""
    return {
        "Voltage/L1": 230.0,
        "Voltage/L2": 231.5,
        "Voltage/L3": 229.8,
        "Voltage": 230.4,
        "Current/L1": 5.2,
        "Current/L2": 4.8,
        "Current/L3": 5.5,
        "Current": 15.5,
        "Power/L1": 1196.0,
        "Power/L2": 1111.2,
        "Power/L3": 1263.9,
        "Power": 3571.1,
        "Frequency": 50.0,
        "Import": 9876.5,
        "Sum": 9876.5
    }


@pytest.fixture
def sample_reading(sdm120_config, sample_sdm120_data):
    """Sample meter reading"""
    return MeterReading(
        meter_id=sdm120_config.address,
        meter_type=sdm120_config.meter_type,
        meter_name=sdm120_config.display_name,
        data=sample_sdm120_data,
        timestamp=datetime.now()
    )
