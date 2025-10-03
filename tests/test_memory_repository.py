"""
Tests for in-memory repository adapter
"""
import pytest
from datetime import datetime
from sdm_modbus_reader.domain.models import MeterType, MeterReading
from sdm_modbus_reader.adapters.memory_repository import InMemoryReadingRepository


class TestInMemoryReadingRepository:
    """Tests for InMemoryReadingRepository - testing behavior through the port interface"""

    @pytest.fixture
    def repository(self):
        """Create a fresh repository for each test"""
        return InMemoryReadingRepository()

    @pytest.fixture
    def sample_reading(self):
        """Create a sample meter reading"""
        return MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5, "Current": 1.2, "Power": 276.6},
            timestamp=datetime.now()
        )

    def test_can_retrieve_saved_reading(self, repository, sample_reading):
        """Test that a saved reading can be retrieved"""
        repository.save(sample_reading)
        retrieved = repository.get_by_meter_id(101)

        assert retrieved is not None

    def test_returns_none_for_nonexistent_meter(self, repository):
        """Test that getting a non-existent meter returns None"""
        result = repository.get_by_meter_id(999)

        assert result is None

    def test_overwrites_previous_reading_for_same_meter(self, repository, sample_reading):
        """Test that saving a new reading for the same meter overwrites the previous one"""
        repository.save(sample_reading)

        updated_reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen Updated",
            data={"Voltage": 235.0, "Current": 1.5},
            timestamp=datetime.now()
        )
        repository.save(updated_reading)

        retrieved = repository.get_by_meter_id(101)

        assert retrieved.meter_name == "Kitchen Updated"

    def test_returns_empty_dict_when_no_readings_exist(self, repository):
        """Test that get_all returns empty dict when repository is empty"""
        result = repository.get_all()

        assert result == {}

    def test_returns_all_saved_readings(self, repository):
        """Test that get_all returns all readings that have been saved"""
        reading1 = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5},
            timestamp=datetime.now()
        )
        reading2 = MeterReading(
            meter_id=102,
            meter_type=MeterType.SDM630,
            meter_name="Main Panel",
            data={"Voltage/L1": 230.0, "Voltage/L2": 231.0, "Voltage/L3": 229.5},
            timestamp=datetime.now()
        )

        repository.save(reading1)
        repository.save(reading2)

        all_readings = repository.get_all()

        assert len(all_readings) == 2

    def test_get_all_includes_correct_meter_ids(self, repository):
        """Test that get_all returns readings keyed by their meter IDs"""
        reading1 = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5},
            timestamp=datetime.now()
        )
        reading2 = MeterReading(
            meter_id=102,
            meter_type=MeterType.SDM630,
            meter_name="Main Panel",
            data={"Voltage/L1": 230.0},
            timestamp=datetime.now()
        )

        repository.save(reading1)
        repository.save(reading2)

        all_readings = repository.get_all()

        assert 101 in all_readings and 102 in all_readings

    def test_get_all_returns_independent_copies(self, repository, sample_reading):
        """Test that get_all returns independent copies on each call"""
        repository.save(sample_reading)

        readings1 = repository.get_all()
        readings2 = repository.get_all()

        assert readings1 is not readings2
