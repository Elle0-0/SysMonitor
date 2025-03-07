import psutil
import random

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    return psutil.virtual_memory().percent

def get_air_quality_index():
    # Simulate air quality index for demonstration purposes
    return random.uniform(0, 500)