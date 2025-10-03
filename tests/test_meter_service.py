"""
Tests for meter application service
"""
import pytest
from datetime import datetime
from unittest.mock import Mock
from sdm_modbus_reader.domain.models import MeterType, MeterConfig, MeterReading
from sdm_modbus_reader.application.meter_service import MeterService


class TestMeterService:
    """Tests for MeterService - testing application behavior through service interface"""

    @pytest.fixture
    def mock_meter_reader(self):
        """Create mock meter reader"""
        return Mock()

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository"""
        return Mock()

    @pytest.fixture
    def mock_publisher(self):
        """Create mock MQTT publisher"""
        return Mock()

    @pytest.fixture
    def meter_config(self):
        """Create sample meter configuration"""
        return MeterConfig(
            meter_type=MeterType.SDM120,
            address=101,
            display_name="Kitchen Meter",
            slug="kitchen-meter"
        )

    @pytest.fixture
    def meter_service(self, mock_meter_reader, mock_repository, mock_publisher):
        """Create meter service with mocked dependencies"""
        return MeterService(
            meter_reader=mock_meter_reader,
            reading_repository=mock_repository,
            message_publisher=mock_publisher
        )

    def test_returns_reading_when_meter_read_succeeds(self, meter_service, meter_config, mock_meter_reader):
        """Test that service returns a MeterReading when read succeeds"""
        meter_data = {"Voltage": 230.5, "Current": 1.2, "Power": 276.6}
        mock_meter_reader.read_meter.return_value = meter_data

        result = meter_service.read_and_store_meter(meter_config)

        assert result is not None

    def test_reading_has_correct_meter_id(self, meter_service, meter_config, mock_meter_reader):
        """Test that returned reading contains correct meter ID"""
        meter_data = {"Voltage": 230.5}
        mock_meter_reader.read_meter.return_value = meter_data

        result = meter_service.read_and_store_meter(meter_config)

        assert result.meter_id == 101

    def test_reading_has_correct_meter_name(self, meter_service, meter_config, mock_meter_reader):
        """Test that returned reading contains correct meter name"""
        meter_data = {"Voltage": 230.5}
        mock_meter_reader.read_meter.return_value = meter_data

        result = meter_service.read_and_store_meter(meter_config)

        assert result.meter_name == "Kitchen Meter"

    def test_stores_reading_in_repository(self, meter_service, meter_config, mock_meter_reader, mock_repository):
        """Test that successful reading is stored in repository"""
        meter_data = {"Voltage": 230.5}
        mock_meter_reader.read_meter.return_value = meter_data

        meter_service.read_and_store_meter(meter_config)

        mock_repository.save.assert_called_once()

    def test_publishes_reading_to_mqtt(self, meter_service, meter_config, mock_meter_reader, mock_publisher):
        """Test that successful reading is published via MQTT"""
        meter_data = {"Voltage": 230.5}
        mock_meter_reader.read_meter.return_value = meter_data

        meter_service.read_and_store_meter(meter_config)

        mock_publisher.publish_meter_data.assert_called_once()

    def test_publishes_with_correct_slug(self, meter_service, meter_config, mock_meter_reader, mock_publisher):
        """Test that MQTT publish uses the meter slug"""
        meter_data = {"Voltage": 230.5}
        mock_meter_reader.read_meter.return_value = meter_data

        meter_service.read_and_store_meter(meter_config)

        call_args = mock_publisher.publish_meter_data.call_args[0]
        assert call_args[0] == "kitchen-meter"

    def test_returns_none_when_read_fails(self, meter_service, meter_config, mock_meter_reader):
        """Test that None is returned when meter read fails"""
        mock_meter_reader.read_meter.return_value = None

        result = meter_service.read_and_store_meter(meter_config)

        assert result is None

    def test_does_not_store_failed_reading(self, meter_service, meter_config, mock_meter_reader, mock_repository):
        """Test that failed readings are not stored"""
        mock_meter_reader.read_meter.return_value = None

        meter_service.read_and_store_meter(meter_config)

        mock_repository.save.assert_not_called()

    def test_does_not_publish_failed_reading(self, meter_service, meter_config, mock_meter_reader, mock_publisher):
        """Test that failed readings are not published"""
        mock_meter_reader.read_meter.return_value = None

        meter_service.read_and_store_meter(meter_config)

        mock_publisher.publish_meter_data.assert_not_called()

    def test_works_without_publisher(self, mock_meter_reader, mock_repository, meter_config):
        """Test that service works when no publisher is configured"""
        meter_data = {"Voltage": 230.5}
        mock_meter_reader.read_meter.return_value = meter_data

        service = MeterService(
            meter_reader=mock_meter_reader,
            reading_repository=mock_repository,
            message_publisher=None
        )

        result = service.read_and_store_meter(meter_config)

        assert result is not None

    def test_can_retrieve_stored_reading(self, meter_service, mock_repository):
        """Test that stored readings can be retrieved by meter ID"""
        expected_reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5},
            timestamp=datetime.now()
        )
        mock_repository.get_by_meter_id.return_value = expected_reading

        result = meter_service.get_meter_reading(101)

        assert result == expected_reading

    def test_returns_none_for_nonexistent_meter(self, meter_service, mock_repository):
        """Test that None is returned for non-existent meter"""
        mock_repository.get_by_meter_id.return_value = None

        result = meter_service.get_meter_reading(999)

        assert result is None

    def test_can_retrieve_all_readings(self, meter_service, mock_repository):
        """Test that all stored readings can be retrieved"""
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
        expected_readings = {101: reading1, 102: reading2}
        mock_repository.get_all.return_value = expected_readings

        result = meter_service.get_all_readings()

        assert result == expected_readings

    def test_returns_empty_dict_when_no_readings_stored(self, meter_service, mock_repository):
        """Test that empty dict is returned when no readings exist"""
        mock_repository.get_all.return_value = {}

        result = meter_service.get_all_readings()

        assert result == {}

    def test_reading_timestamp_is_current(self, meter_service, meter_config, mock_meter_reader):
        """Test that reading timestamp is set to current time"""
        meter_data = {"Voltage": 230.5}
        mock_meter_reader.read_meter.return_value = meter_data
        before = datetime.now()

        result = meter_service.read_and_store_meter(meter_config)

        after = datetime.now()
        assert before <= result.timestamp <= after

    def test_preserves_meter_data_without_modification(self, meter_service, meter_config, mock_meter_reader):
        """Test that service doesn't modify the meter data"""
        original_data = {
            "Voltage": 230.5,
            "Current": 1.234,
            "Power": 276.6,
            "Cosphi": 0.95
        }
        mock_meter_reader.read_meter.return_value = original_data

        result = meter_service.read_and_store_meter(meter_config)

        assert result.data == original_data
