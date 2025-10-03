"""
Domain - SDM Meter Register Maps

Register addresses for different SDM meter types.
These are Modbus register addresses for reading IEEE754 float32 values.
"""

SDM120_REGISTERS = {
    "Voltage": 0x0000,          # 30001
    "Current": 0x0006,          # 30007
    "Power": 0x000C,            # 30013
    "ApparentPower": 0x0012,    # 30019
    "ReactivePower": 0x0018,    # 30025
    "Cosphi": 0x001E,           # 30031
    "PhaseAngle": 0x0024,       # 30037
    "Frequency": 0x0046,        # 30071
    "Import": 0x0048,           # 30073 - Import active energy
    "Export": 0x004A,           # 30075 - Export active energy
    "ReactiveImport": 0x004C,   # 30077 - Import reactive energy
    "ReactiveExport": 0x004E,   # 30079 - Export reactive energy
    "Sum": 0x0156,              # 30343 - Total active energy
    "ReactiveSum": 0x0158,      # 30345 - Total reactive energy
}

SDM630_REGISTERS = {
    "Voltage/L1": 0x0000,
    "Voltage/L2": 0x0002,
    "Voltage/L3": 0x0004,
    "Voltage": 0x002A,
    "Current/L1": 0x0006,
    "Current/L2": 0x0008,
    "Current/L3": 0x000A,
    "Current": 0x0030,
    "Power/L1": 0x000C,
    "Power/L2": 0x000E,
    "Power/L3": 0x0010,
    "Power": 0x0034,
    "ApparentPower/L1": 0x0012,
    "ApparentPower/L2": 0x0014,
    "ApparentPower/L3": 0x0016,
    "ApparentPower": 0x0038,
    "ReactivePower/L1": 0x0018,
    "ReactivePower/L2": 0x001A,
    "ReactivePower/L3": 0x001C,
    "ReactivePower": 0x003C,
    "Cosphi/L1": 0x001E,
    "Cosphi/L2": 0x0020,
    "Cosphi/L3": 0x0022,
    "Cosphi": 0x003E,
    "PhaseAngle/L1": 0x0024,
    "PhaseAngle/L2": 0x0026,
    "PhaseAngle/L3": 0x0028,
    "Frequency": 0x0046,
    "Import": 0x0156,
    "Export": 0x0160,
    "ReactiveImport": 0x0158,
    "ReactiveExport": 0x0162,
    "Sum": 0x0156,
    "ReactiveSum": 0x0158,
    "Voltage/L1-L2": 0x00C8,
    "Voltage/L2-L3": 0x00CA,
    "Voltage/L3-L1": 0x00CC,
    "Current/N": 0x00E0,
    "THD/VoltageL1": 0x00EA,
    "THD/VoltageL2": 0x00EC,
    "THD/VoltageL3": 0x00EE,
    "THD/CurrentL1": 0x00F0,
    "THD/CurrentL2": 0x00F2,
    "THD/CurrentL3": 0x00F4,
    "THD/VoltageAvg": 0x00F8,
    "THD/CurrentAvg": 0x00FA,
}
