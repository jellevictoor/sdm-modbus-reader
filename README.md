# SDM Modbus Reader

A Python application for reading data from SDM energy meters (SDM120, SDM220, SDM230, SDM630) via Modbus RTU and publishing to MQTT with a web dashboard.

## Features

- 📊 **Multi-meter support** - Monitor multiple SDM120/SDM630 meters simultaneously
- 🌐 **Web dashboard** - Real-time visualization of energy metrics
- 📡 **MQTT publishing** - Publish meter data to MQTT broker
- 🔄 **Auto-polling** - Configurable polling intervals
- 🐳 **Docker support** - Easy deployment with Docker Compose
- ⚡ **Fast API** - REST API for meter data access

## Supported Meters

- SDM120 (Single-phase)
- SDM220 (Single-phase)
- SDM230 (Single-phase)
- SDM630 (Three-phase)

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sdm-modbus-reader.git
cd sdm-modbus-reader
```

2. Configure your setup in `docker-compose.yml`:
```yaml
command: >
  python -m sdm_modbus_reader.sdm_modbus_reader
  --device SDM630:100:"Main Panel"
  --device SDM120:101:Kitchen
  --mqtt-broker 192.168.1.5
  --mqtt-topic-prefix home/energy/sdm
```

3. Start the container:
```bash
docker-compose up -d
```

4. Access the web dashboard:
```
http://localhost:8000
```

### Manual Installation

1. Install Python 3.12 or higher

2. Install dependencies:
```bash
pip install -e .
```

3. Run the application:
```bash
python -m sdm_modbus_reader.sdm_modbus_reader \
  --device SDM120:101:Kitchen \
  --device SDM630:100:"Main Panel" \
  --mqtt-broker 192.168.1.5
```

## Configuration

### Command Line Arguments

```bash
python -m sdm_modbus_reader.sdm_modbus_reader --help
```

#### Required Arguments

- `--device, -d` - Meter specification in format `TYPE:ADDRESS:NAME`
  - Example: `SDM120:101:Kitchen` or `SDM630:100:"Main Panel"`
  - Can be specified multiple times for multiple meters

#### Serial Configuration

- `--serial-port` - Serial port device (default: `/dev/ttyUSB0`)
- `--baudrate` - Serial baudrate (default: `9600`)
- `--parity` - Serial parity: N/E/O (default: `N`)
- `--stopbits` - Serial stop bits: 1/2 (default: `1`)
- `--bytesize` - Serial byte size: 7/8 (default: `8`)

#### MQTT Configuration

- `--mqtt-broker` - MQTT broker hostname or IP (default: `localhost`)
- `--mqtt-port` - MQTT broker port (default: `1883`)
- `--mqtt-user` - MQTT username (optional)
- `--mqtt-password` - MQTT password (optional)
- `--mqtt-topic-prefix` - MQTT topic prefix (default: `home/energy/sdm`)

#### Other Options

- `--poll-interval` - Poll interval in seconds (default: `10`)
- `--api-port` - Web API port (default: `8000`)

### Device Specification Format

Devices are specified in the format: `TYPE:ADDRESS:DISPLAY_NAME`

- **TYPE**: Meter model (SDM120, SDM220, SDM230, SDM630)
- **ADDRESS**: Modbus address (1-247)
- **DISPLAY_NAME**: Human-readable name (will be slugified for MQTT topics)

Examples:
```bash
--device SDM120:101:Kitchen
--device SDM630:100:"Main Panel"
--device SDM120:102:"Living Room"
```

The display name "Main Panel" will be slugified to `main-panel` for MQTT topics.

## Usage Examples

### Basic Usage

```bash
python -m sdm_modbus_reader.sdm_modbus_reader \
  --device SDM120:101:Kitchen \
  --device SDM630:100:"Main Panel"
```

### With MQTT Authentication

```bash
python -m sdm_modbus_reader.sdm_modbus_reader \
  --device SDM120:101:Kitchen \
  --mqtt-broker 192.168.1.5 \
  --mqtt-user admin \
  --mqtt-password secret \
  --mqtt-topic-prefix home/energy
```

### Custom Serial Configuration

```bash
python -m sdm_modbus_reader.sdm_modbus_reader \
  --device SDM120:101:Kitchen \
  --serial-port /dev/ttyUSB1 \
  --baudrate 19200 \
  --parity E
```

### Full Configuration Example

```bash
python -m sdm_modbus_reader.sdm_modbus_reader \
  --device SDM630:100:"Main Panel" \
  --device SDM120:101:Kitchen \
  --device SDM120:102:"Living Room" \
  --serial-port /dev/ttyUSB0 \
  --baudrate 9600 \
  --mqtt-broker 192.168.1.5 \
  --mqtt-port 1883 \
  --mqtt-topic-prefix klskmp/metering/sdm \
  --poll-interval 10
```

## MQTT Topics

Data is published to MQTT topics in the following format:

```
{prefix}/{meter-slug}/{metric}
```

Examples:
```
home/energy/sdm/main-panel/Voltage
home/energy/sdm/main-panel/Current
home/energy/sdm/main-panel/Power
home/energy/sdm/kitchen/Voltage
home/energy/sdm/kitchen/Power/L1
home/energy/sdm/kitchen/Power/L2
home/energy/sdm/kitchen/Power/L3
```

### Available Metrics

**Single-phase meters (SDM120/SDM220/SDM230):**
- Voltage, Current, Power, ApparentPower, ReactivePower
- Cosphi (Power Factor), PhaseAngle, Frequency
- Import, Export, Sum (Energy counters)

**Three-phase meters (SDM630):**
- All single-phase metrics, plus:
- Per-phase metrics (e.g., `Voltage/L1`, `Current/L2`, `Power/L3`)
- Line-to-line voltages, Neutral current
- Total Harmonic Distortion (THD) for voltage and current

## Web Dashboard

Access the web dashboard at `http://localhost:8000`

Features:
- Real-time data updates (every 5 seconds)
- Separate sections for single-phase and three-phase meters
- Compact card layout with icons
- Responsive grid design
- Thousand separators for readability
- Color-coded metrics

## API Endpoints

### Get All Meters

```bash
curl http://localhost:8000/api/meters
```

Returns data for all configured meters.

### Get Specific Meter

```bash
curl http://localhost:8000/api/meters/101
```

Returns data for meter at address 101.

## Docker Deployment

### Using docker-compose.yml

1. Edit `docker-compose.yml` with your configuration
2. Start the service:
```bash
docker-compose up -d
```

### Using Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```env
MQTT_BROKER=192.168.1.5
MQTT_USER=admin
MQTT_PASSWORD=secret
```

3. Start using the example compose file:
```bash
docker-compose -f docker-compose.example.yml up -d
```

### View Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Rebuild After Changes

```bash
docker-compose up -d --build
```

## Hardware Setup

### Wiring

Connect your SDM meters to an RS485-to-USB adapter:

```
SDM Meter    RS485 Adapter
---------    -------------
A+       →   A+ (or D+)
B-       → ��  B- (or D-)
GND      →   GND (optional)
```

For multiple meters, connect them in parallel (daisy-chain):

```
RS485 ── Meter 1 ── Meter 2 ── Meter 3 ── ...
         (addr:100) (addr:101) (addr:102)
```

### Meter Configuration

Each SDM meter must have a unique Modbus address (1-247). Refer to your meter's manual for address configuration.

Common default settings:
- Baudrate: 9600
- Parity: None
- Data bits: 8
- Stop bits: 1

## Troubleshooting

### Serial Port Permission Denied

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or change device permissions
sudo chmod 666 /dev/ttyUSB0
```

### No Data from Meters

1. Check serial port connection: `ls -la /dev/ttyUSB*`
2. Verify baudrate matches meter configuration
3. Check Modbus addresses are correct
4. Ensure RS485 A+/B- wiring is correct
5. Check for proper termination resistors (120Ω) on long cable runs

### MQTT Connection Failed

1. Verify MQTT broker is running: `mosquitto -v`
2. Check broker IP address and port
3. Test with mosquitto_pub: `mosquitto_pub -h 192.168.1.5 -t test -m "hello"`
4. Verify username/password if authentication is enabled

### Docker Container Won't Start

```bash
# Check logs
docker-compose logs

# Verify serial device exists
ls -la /dev/ttyUSB0

# Check device permissions
docker run --rm --device=/dev/ttyUSB0 alpine ls -la /dev/ttyUSB0
```

## Development

### Running Locally

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e .

# Run the application
python -m sdm_modbus_reader.sdm_modbus_reader --device SDM120:101:Test
```

### Project Structure

```
sdm-modbus-reader/
├── sdm_modbus_reader/
│   ├── __init__.py
│   ├── sdm_modbus_reader.py  # Main application
│   ├── api.py                # FastAPI web interface
│   ├── data_store.py         # In-memory data storage
│   └── run.py                # Concurrent runner
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Jelle Victoor - jelle@victoor.io

## Acknowledgments

- Built with [pymodbus](https://github.com/pymodbus-dev/pymodbus)
- Web framework: [FastAPI](https://fastapi.tiangolo.com/)
- CLI: [Typer](https://typer.tiangolo.com/)
- MQTT: [paho-mqtt](https://www.eclipse.org/paho/)