
"""
Tests for domain models
"""
import pytest
from datetime import datetime
from sdm_modbus_reader.domain.models import MeterType, MeterConfig, MeterReading


class TestMeterType:
    """Tests for MeterType enum"""

    def test_sdm120_has_correct_value(self):
        """Test that SDM120 meter type has correct value"""
        assert MeterType.SDM120.value == "SDM120"

    def test_sdm220_has_correct_value(self):
        """Test that SDM220 meter type has correct value"""
        assert MeterType.SDM220.value == "SDM220"

    def test_sdm230_has_correct_value(self):
        """Test that SDM230 meter type has correct value"""
        assert MeterType.SDM230.value == "SDM230"

    def test_sdm630_has_correct_value(self):
        """Test that SDM630 meter type has correct value"""
        assert MeterType.SDM630.value == "SDM630"


class TestMeterConfig:
    """Tests for MeterConfig dataclass"""

    def test_can_create_valid_configuration(self):
        """Test creating a valid meter configuration"""
        config = MeterConfig(
            meter_type=MeterType.SDM120,
            address=101,
            display_name="Kitchen Meter",
            slug="kitchen-meter"
        )

        assert config is not None

    def test_rejects_address_below_minimum(self):
        """Test that address below 1 is rejected"""
        with pytest.raises(ValueError, match="Address must be between 1 and 247"):
            MeterConfig(
                meter_type=MeterType.SDM120,
                address=0,
                display_name="Test",
                slug="test"
            )

    def test_rejects_address_above_maximum(self):
        """Test that address above 247 is rejected"""
        with pytest.raises(ValueError, match="Address must be between 1 and 247"):
            MeterConfig(
                meter_type=MeterType.SDM120,
                address=248,
                display_name="Test",
                slug="test"
            )

    def test_accepts_minimum_address(self):
        """Test that minimum address 1 is accepted"""
        config = MeterConfig(
            meter_type=MeterType.SDM120,
            address=1,
            display_name="Min",
            slug="min"
        )

        assert config.address == 1

    def test_accepts_maximum_address(self):
        """Test that maximum address 247 is accepted"""
        config = MeterConfig(
            meter_type=MeterType.SDM120,
            address=247,
            display_name="Max",
            slug="max"
        )

        assert config.address == 247


class TestMeterReading:
    """Tests for MeterReading dataclass"""

    def test_can_create_reading(self):
        """Test creating a meter reading"""
        now = datetime.now()
        data = {"Voltage": 230.5, "Current": 1.2, "Power": 276.6}

        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data=data,
            timestamp=now
        )

        assert reading is not None

    def test_to_dict_includes_meter_id(self):
        """Test that to_dict includes meter ID"""
        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5},
            timestamp=datetime.now()
        )

        result = reading.to_dict()

        assert result["meter_id"] == 101

    def test_to_dict_includes_meter_type_as_string(self):
        """Test that to_dict converts meter type to string"""
        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5},
            timestamp=datetime.now()
        )

        result = reading.to_dict()

        assert result["meter_type"] == "SDM120"

    def test_to_dict_includes_meter_name(self):
        """Test that to_dict includes meter name"""
        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5},
            timestamp=datetime.now()
        )

        result = reading.to_dict()

        assert result["meter_name"] == "Kitchen"

    def test_to_dict_includes_data(self):
        """Test that to_dict includes meter data"""
        data = {"Voltage": 230.5, "Current": 1.2}
        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data=data,
            timestamp=datetime.now()
        )

        result = reading.to_dict()

        assert result["data"] == data

    def test_to_dict_converts_timestamp_to_isoformat(self):
        """Test that to_dict converts timestamp to ISO format string"""
        now = datetime.now()
        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Kitchen",
            data={"Voltage": 230.5},
            timestamp=now
        )

        result = reading.to_dict()

        assert result["timestamp"] == now.isoformat()

    def test_can_create_reading_with_empty_data(self):
        """Test creating a reading with empty data dictionary"""
        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Test",
            data={},
            timestamp=datetime.now()
        )

        assert reading.data == {}

    def test_to_dict_handles_empty_data(self):
        """Test that to_dict correctly handles empty data"""
        reading = MeterReading(
            meter_id=101,
            meter_type=MeterType.SDM120,
            meter_name="Test",
            data={},
            timestamp=datetime.now()
        )

        result = reading.to_dict()

        assert result["data"] == {}
