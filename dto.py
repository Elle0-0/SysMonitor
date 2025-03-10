class MetricsDTO:
    def __init__(self, device_id, cpu_usage, memory_usage, weather_and_air_quality_data, latitude, longitude):
        self.device_id = device_id
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.weather_and_air_quality_data = weather_and_air_quality_data  # List of third-party data
        self.latitude = latitude
        self.longitude = longitude

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "weather_and_air_quality_data": self.weather_and_air_quality_data,  # Include third-party data
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    @staticmethod
    def from_dict(data):
        return MetricsDTO(
            device_id=data.get("device_id"),
            cpu_usage=data.get("cpu_usage"),
            memory_usage=data.get("memory_usage"),
            weather_and_air_quality_data=data.get("weather_and_air_quality_data", []),  # Default to empty list
            latitude=data.get("latitude"),
            longitude=data.get("longitude")
        )
