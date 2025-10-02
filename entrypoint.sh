#!/bin/bash
set -e

# Run both the reader and API with all passed arguments
# Use -c to avoid -m being in sys.argv
exec python -c "from sdm_modbus_reader.run import main; main()" "$@"