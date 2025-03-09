import os
import logging
from flask import Flask, jsonify, render_template
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import requests
from models import Session, DeviceMetric, ThirdPartyMetric

# Flask App
app = Flask(__name__)

# Dash App
dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    session = Session()
    try:
        device_metrics = session.query(DeviceMetric).order_by(DeviceMetric.timestamp.desc()).limit(5).all()
        third_party_metrics = session.query(ThirdPartyMetric).order_by(ThirdPartyMetric.timestamp.desc()).limit(5).all()

        device_metrics_data = [
            {"device_id": metric.device_id, "metric_type_id": metric.metric_type_id, "value": metric.value, "timestamp": metric.timestamp}
            for metric in device_metrics
        ]
        third_party_metrics_data = [
            {"name": metric.name, "value": metric.value, "latitude": metric.latitude, "longitude": metric.longitude, "timestamp": metric.timestamp}
            for metric in third_party_metrics
        ]

        return jsonify({
            "device_metrics": device_metrics_data,
            "third_party_metrics": third_party_metrics_data
        })
    finally:
        session.close()

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
        dcc.Graph(id='air-quality-map')
    ])
])

@dash_app.callback(
    [Output('cpu-usage-histogram', 'figure'),
     Output('memory-usage-histogram', 'figure'),
     Output('air-quality-map', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics(n):
    response = requests.get('http://localhost:5000/api/metrics')
    data = response.json()

    cpu_metrics = [m['value'] for m in data['device_metrics'] if m['metric_type_id'] == 1]
    ram_metrics = [m['value'] for m in data['device_metrics'] if m['metric_type_id'] == 2]
    air_quality_data = data['third_party_metrics']

    cpu_usage_histogram = {
        'data': [go.Histogram(x=cpu_metrics)],
        'layout': go.Layout(title='CPU Usage Distribution')
    }
    memory_usage_histogram = {
        'data': [go.Histogram(x=ram_metrics)],
        'layout': go.Layout(title='Memory Usage Distribution')
    }
    air_quality_map_figure = {
        'data': [go.Scattermapbox(
            lat=[d['latitude'] for d in air_quality_data],
            lon=[d['longitude'] for d in air_quality_data],
            mode='markers',
            marker=go.scattermapbox.Marker(size=10),
            text=[f"Air Quality Index: {d['value']}" for d in air_quality_data]
        )],
        'layout': go.Layout(mapbox_style="open-street-map", zoom=6)
    }

    return cpu_usage_histogram, memory_usage_histogram, air_quality_map_figure

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
