"""
Shared data store for meter readings
"""
from typing import Dict, Optional
from datetime import datetime
import threading

class MeterDataStore:
    """Thread-safe store for latest meter readings"""

    def __init__(self):
        self._data: Dict[int, Dict] = {}
        self._lock = threading.Lock()

    def update_meter(self, meter_id: int, meter_type: str, meter_name: str, data: Dict):
        """Update data for a specific meter"""
        with self._lock:
            self._data[meter_id] = {
                "meter_id": meter_id,
                "meter_type": meter_type,
                "meter_name": meter_name,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

    def get_meter(self, meter_id: int) -> Optional[Dict]:
        """Get data for a specific meter"""
        with self._lock:
            return self._data.get(meter_id)

    def get_all_meters(self) -> Dict[int, Dict]:
        """Get data for all meters"""
        with self._lock:
            return self._data.copy()

# Global instance
meter_store = MeterDataStore()