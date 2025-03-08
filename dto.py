class MetricsDTO:
    def __init__(self, device_id, cpu_usage, memory_usage, air_quality_index, latitude, longitude):
        self.device_id = device_id
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.air_quality_index = air_quality_index
        self.latitude = latitude
        self.longitude = longitude

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "air_quality_index": self.air_quality_index,
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    @staticmethod
    def from_dict(data):
        return MetricsDTO(
            device_id=data.get("device_id"),
            cpu_usage=data.get("cpu_usage"),
            memory_usage=data.get("memory_usage"),
            air_quality_index=data.get("air_quality_index"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude")
        )