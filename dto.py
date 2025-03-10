class MetricsDTO:
    def __init__(self, device_id, device_name, cpu_usage, ram_usage, weather_and_air_quality_data):
        self.device_id = device_id
        self.device_name = device_name
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.weather_and_air_quality_data = weather_and_air_quality_data  # List of third-party data

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "cpu_usage": self.cpu_usage,
            "ram_usage": self.ram_usage,
            "weather_and_air_quality_data": self.weather_and_air_quality_data  # Include third-party data
        }

    @staticmethod
    def from_dict(data):
        return MetricsDTO(
            device_id=data.get("device_id"),
            device_name=data.get("device_name"),
            cpu_usage=data.get("cpu_usage"),
            ram_usage=data.get("ram_usage"),
            weather_and_air_quality_data=data.get("weather_and_air_quality_data", [])  # Default to empty list
        )

