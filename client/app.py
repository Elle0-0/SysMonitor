import sys
import os
from flask import Flask, jsonify, render_template
import logging
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import requests  # Import the requests module

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Session, DeviceMetric, ThirdPartyMetric, MetricType, Device

app = Flask(__name__)
dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')

@app.route('/api/report', methods=['GET'])
def report():
    session = Session()
    try:
        # Query the latest CPU and Memory usage metrics
        cpu_metrics = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 1).order_by(DeviceMetric.device_metric_id.desc()).limit(100).all()
        ram_metrics = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 2).order_by(DeviceMetric.device_metric_id.desc()).limit(100).all()

        # Query the latest Air Quality Index for all locations
        air_quality_metrics = session.query(ThirdPartyMetric).filter(ThirdPartyMetric.name == "Air Quality Index").order_by(ThirdPartyMetric.third_party_metric_id.desc()).all()

        air_quality_data = [
            {
                "latitude": metric.latitude,
                "longitude": metric.longitude,
                "air_quality_index": metric.value
            }
            for metric in air_quality_metrics
        ]

        return jsonify({
            "cpu_metrics": [metric.value for metric in cpu_metrics],
            "ram_metrics": [metric.value for metric in ram_metrics],
            "air_quality_data": air_quality_data
        })
    finally:
        session.close()

@app.route('/')
def index():
    return render_template('index.html')

# Dash layout
dash_app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    html.H1("SysMonitor Metrics Dashboard"),
    html.Div([
        html.Div([
            html.H2("CPU Usage"),
            dcc.Graph(id='cpu-usage-histogram')
        ], className="six columns"),
        html.Div([
            html.H2("Memory Usage"),
            dcc.Graph(id='memory-usage-histogram')
        ], className="six columns")
    ], className="row"),
    html.Div([
        html.H2("Air Quality Index"),
        html.P(id='air-quality-index', children="Loading..."),
        dcc.Graph(id='air-quality-map')
    ])
], className="container")

# Dash callbacks
@dash_app.callback(
    [Output('cpu-usage-histogram', 'figure'),
     Output('memory-usage-histogram', 'figure'),
     Output('air-quality-index', 'children'),
     Output('air-quality-map', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics(n):
    response = requests.get('http://localhost:5000/api/report')
    data = response.json()

    cpu_metrics = data['cpu_metrics']
    ram_metrics = data['ram_metrics']
    air_quality_data = data['air_quality_data']

    cpu_usage_histogram = {
        'data': [go.Histogram(x=cpu_metrics)],
        'layout': go.Layout(title='CPU Usage Distribution', xaxis={'title': 'CPU Usage (%)'}, yaxis={'title': 'Count'})
    }

    memory_usage_histogram = {
        'data': [go.Histogram(x=ram_metrics)],
        'layout': go.Layout(title='Memory Usage Distribution', xaxis={'title': 'Memory Usage (%)'}, yaxis={'title': 'Count'})
    }

    air_quality_map_figure = {
        'data': [go.Scattermapbox(
            lat=[d['latitude'] for d in air_quality_data],
            lon=[d['longitude'] for d in air_quality_data],
            mode='markers',
            marker=go.scattermapbox.Marker(size=14),
            text=[f"Air Quality Index: {d['air_quality_index']}" for d in air_quality_data]
        )],
        'layout': go.Layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(lat=53.349805, lon=-6.26031),  # Center on Dublin
                zoom=6
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )
    }

    return cpu_usage_histogram, memory_usage_histogram, f"Air Quality Index: {air_quality_data[0]['air_quality_index']}", air_quality_map_figure

if __name__ == '__main__':
    app.run(debug=True)