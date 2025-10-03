"""
Tests for Modbus reader adapter
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import struct
from sdm_modbus_reader.domain.models import MeterType
from sdm_modbus_reader.adapters.modbus_reader import ModbusMeterReader


class TestModbusMeterReader:
    """Tests for ModbusMeterReader - testing behavior through the meter reader port"""

    @pytest.fixture
    def modbus_reader(self):
        """Create Modbus reader with mocked client"""
        with patch('sdm_modbus_reader.adapters.modbus_reader.ModbusSerialClient'):
            reader = ModbusMeterReader(
                port="/dev/ttyUSB0",
                baudrate=9600,
                parity="N",
                stopbits=1,
                bytesize=8
            )
            return reader

    def test_can_connect_to_modbus_device(self, modbus_reader):
        """Test that connection to Modbus device succeeds"""
        modbus_reader.client.connect.return_value = True

        result = modbus_reader.connect()

        assert result is True

    def test_returns_false_when_connection_fails(self, modbus_reader):
        """Test that connection failure is handled"""
        modbus_reader.client.connect.return_value = False

        result = modbus_reader.connect()

        assert result is False

    def test_can_read_valid_float32_value(self, modbus_reader):
        """Test that valid float32 values can be read from registers"""
        mock_response = Mock()
        mock_response.isError.return_value = False
        packed = struct.pack('>f', 230.5)
        high_word, low_word = struct.unpack('>HH', packed)
        mock_response.registers = [high_word, low_word]

        modbus_reader.client.read_input_registers.return_value = mock_response

        result = modbus_reader._read_float32(device_id=101, register=0x0000)

        assert result is not None

    def test_returns_none_on_modbus_error_response(self, modbus_reader):
        """Test that Modbus error responses return None"""
        mock_response = Mock()
        mock_response.isError.return_value = True

        modbus_reader.client.read_input_registers.return_value = mock_response

        result = modbus_reader._read_float32(device_id=101, register=0x0000)

        assert result is None

    def test_returns_none_on_communication_exception(self, modbus_reader):
        """Test that communication exceptions are handled gracefully"""
        modbus_reader.client.read_input_registers.side_effect = Exception("Communication error")

        result = modbus_reader._read_float32(device_id=101, register=0x0000)

        assert result is None

    @patch('sdm_modbus_reader.adapters.modbus_reader.time.sleep')
    def test_can_read_sdm120_meter_data(self, mock_sleep, modbus_reader):
        """Test that SDM120 meter can be read successfully"""
        def mock_read_float32(device_id, register):
            values = {
                0x0000: 230.5,
                0x0006: 1.2,
                0x000C: 276.6,
            }
            return values.get(register, 0.0)

        modbus_reader._read_float32 = Mock(side_effect=mock_read_float32)

        result = modbus_reader.read_meter(device_id=101, meter_type=MeterType.SDM120)

        assert result is not None

    @patch('sdm_modbus_reader.adapters.modbus_reader.time.sleep')
    def test_sdm120_data_includes_voltage_reading(self, mock_sleep, modbus_reader):
        """Test that SDM120 data includes voltage measurement"""
        def mock_read_float32(device_id, register):
            values = {0x0000: 230.5, 0x0006: 1.2, 0x000C: 276.6}
            return values.get(register, 0.0)

        modbus_reader._read_float32 = Mock(side_effect=mock_read_float32)

        result = modbus_reader.read_meter(device_id=101, meter_type=MeterType.SDM120)

        assert result.voltage is not None

    @patch('sdm_modbus_reader.adapters.modbus_reader.time.sleep')
    def test_can_read_sdm630_meter_data(self, mock_sleep, modbus_reader):
        """Test that SDM630 meter can be read successfully"""
        def mock_read_float32(device_id, register):
            values = {
                0x0000: 230.0,
                0x0002: 231.0,
                0x0004: 229.5,
            }
            return values.get(register, 0.0)

        modbus_reader._read_float32 = Mock(side_effect=mock_read_float32)

        result = modbus_reader.read_meter(device_id=100, meter_type=MeterType.SDM630)

        assert result is not None

    @patch('sdm_modbus_reader.adapters.modbus_reader.time.sleep')
    def test_sdm630_data_includes_phase_voltages(self, mock_sleep, modbus_reader):
        """Test that SDM630 data includes three-phase voltage measurements"""
        def mock_read_float32(device_id, register):
            values = {
                0x0000: 230.0,
                0x0002: 231.0,
                0x0004: 229.5,
            }
            return values.get(register, 0.0)

        modbus_reader._read_float32 = Mock(side_effect=mock_read_float32)

        result = modbus_reader.read_meter(device_id=100, meter_type=MeterType.SDM630)

        assert result.phase_l1 is not None
        assert result.phase_l2 is not None
        assert result.phase_l3 is not None
        assert result.phase_l1.voltage is not None
        assert result.phase_l2.voltage is not None
        assert result.phase_l3.voltage is not None

    @patch('sdm_modbus_reader.adapters.modbus_reader.time.sleep')
    def test_returns_none_when_all_registers_fail(self, mock_sleep, modbus_reader):
        """Test that None is returned when all register reads fail"""
        modbus_reader._read_float32 = Mock(return_value=None)

        result = modbus_reader.read_meter(device_id=101, meter_type=MeterType.SDM120)

        assert result is None

    @patch('sdm_modbus_reader.adapters.modbus_reader.time.sleep')
    def test_returns_partial_data_when_some_registers_succeed(self, mock_sleep, modbus_reader):
        """Test that partial data is returned when some registers succeed"""
        call_count = [0]

        def mock_read_float32(device_id, register):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return 230.5
            return None

        modbus_reader._read_float32 = Mock(side_effect=mock_read_float32)

        result = modbus_reader.read_meter(device_id=101, meter_type=MeterType.SDM120)

        assert result is not None

    @patch('sdm_modbus_reader.adapters.modbus_reader.time.sleep')
    def test_partial_data_includes_successful_readings(self, mock_sleep, modbus_reader):
        """Test that partial data includes the successful register reads"""
        call_count = [0]

        def mock_read_float32(device_id, register):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return 230.5
            return None

        modbus_reader._read_float32 = Mock(side_effect=mock_read_float32)

        result = modbus_reader.read_meter(device_id=101, meter_type=MeterType.SDM120)

        assert len(result.to_dict()) > 0
