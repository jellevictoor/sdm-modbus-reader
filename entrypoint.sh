#!/bin/bash
set -e

# Run both the reader and API with all passed arguments
exec python -m sdm_modbus_reader.run "$@"