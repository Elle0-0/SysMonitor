import sys
import os
from flask import Flask, request, jsonify, render_template
import logging
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import requests  # Import the requests module

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Session, DeviceMetric, ThirdPartyMetric, MetricType, Device
from dto import MetricsDTO

app = Flask(__name__)
dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')

@app.route('/api/aggregate', methods=['POST'])
def aggregate():
    session = Session()
    try:
        data = request.json
        metrics_dto = MetricsDTO.from_dict(data)

        # Insert CPU Usage and Memory Usage into the database
        device = session.query(Device).filter(Device.name == 'PC').first()
        if device is None:
            return jsonify({"error": "Device 'PC' not found in the database."}), 404

        metric_type_cpu = session.query(MetricType).filter(MetricType.name == "CPU Usage").first()
        metric_type_ram = session.query(MetricType).filter(MetricType.name == "RAM Usage").first()

        if metric_type_cpu is None or metric_type_ram is None:
            return jsonify({"error": "Metric types 'CPU Usage' or 'RAM Usage' not found in the database."}), 404

        device_metric_cpu = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_cpu.metric_type_id, value=metrics_dto.cpu_usage)
        device_metric_ram = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_ram.metric_type_id, value=metrics_dto.memory_usage)

        session.add(device_metric_cpu)
        session.add(device_metric_ram)

        # Insert Air Quality Index into the database
        third_party_metric_air_quality = ThirdPartyMetric(name="Air Quality Index", value=metrics_dto.air_quality_index, source="OpenWeatherMap")
        session.add(third_party_metric_air_quality)

        session.commit()
        return jsonify({"message": "Metrics collected and stored successfully."}), 200
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/report', methods=['GET'])
def report():
    session = Session()
    try:
        # Query the latest CPU and Memory usage metrics
        cpu_metric = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 1).order_by(DeviceMetric.device_metric_id.desc()).first()
        ram_metric = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 2).order_by(DeviceMetric.device_metric_id.desc()).first()

        # Query the latest Air Quality Index
        air_quality_metric = session.query(ThirdPartyMetric).filter(ThirdPartyMetric.name == "Air Quality Index").order_by(ThirdPartyMetric.third_party_metric_id.desc()).first()

        return jsonify({
            "cpu_usage": cpu_metric.value if cpu_metric else None,
            "memory_usage": ram_metric.value if ram_metric else None,
            "air_quality_index": air_quality_metric.value if air_quality_metric else None
        })
    finally:
        session.close()

@app.route('/')
def index():
    return render_template('index.html')

# Dash layout
dash_app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    html.H1("SysMonitor Metrics"),
    html.H2("CPU Usage"),
    html.P(id='cpu-usage', children="Loading..."),
    html.H2("Memory Usage"),
    html.P(id='memory-usage', children="Loading..."),
    html.H2("Air Quality Index"),
    html.P(id='air-quality-index', children="Loading...")
])

# Dash callbacks
@dash_app.callback(
    [Output('cpu-usage', 'children'),
     Output('memory-usage', 'children'),
     Output('air-quality-index', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics(n):
    response = requests.get('http://localhost:5000/api/report')
    data = response.json()
    return f"{data['cpu_usage']}%", f"{data['memory_usage']}%", data['air_quality_index']

if __name__ == '__main__':
    app.run(debug=True)