import os
import sys
from flask import Flask, jsonify, render_template, request, redirect
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import logging
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(level=logging.DEBUG)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto import MetricsDTO
from models import Session, DeviceMetric, ThirdParty
from lib_database.update_database import update_database

# Flask App
app = Flask(__name__)

# Enable threading
app.config['THREADS_PER_PAGE'] = 2

# Dash App
dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')
dash_app.title = "SysMonitor Dashboard"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard/')
def dashboard_redirect():
    return redirect('/dashboard/')

@app.route('/api/update_metrics', methods=['POST'])
def update_metrics():
    logging.info("Received request to update metrics")
    
    try:
        metrics_data = request.get_json()
        logging.debug(f"Metrics data received: {metrics_data}")
        
        metrics_dto = MetricsDTO.from_dict(metrics_data)
        logging.debug(f"MetricsDTO created: {metrics_dto}")

        update_database(metrics_dto)
        
        logging.info("Metrics successfully updated in the database")
        return jsonify({"message": "Metrics updated successfully!"}), 200
        
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_device_metrics(session, offset, limit):
    return session.query(DeviceMetric).order_by(DeviceMetric.timestamp.desc()).offset(offset).limit(limit).all()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_third_party_metrics(session, offset, limit):
    return session.query(ThirdParty).order_by(ThirdParty.timestamp.desc()).offset(offset).limit(limit).all()

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    session = Session()
    try:
        page = request.args.get('page', 1, type=int) or 1
        limit = request.args.get('limit', 10, type=int) or 10
        offset = (page - 1) * limit

        device_metrics = session.query(DeviceMetric).order_by(DeviceMetric.timestamp.desc()).offset(offset).limit(limit).all()
        third_party_metrics = session.query(ThirdParty).order_by(ThirdParty.timestamp.desc()).offset(offset).limit(limit).all()

        if not device_metrics and not third_party_metrics:
            logging.warning("No metrics data found.")
            
        return jsonify({
            "device_metrics": [{
                "device_id": metric.device_id,
                "metric_id": metric.metric_id,
                "value": metric.value,
                "timestamp": metric.timestamp
            } for metric in device_metrics],
            "third_party_metrics": [{
                "name": metric.name,
                "value": metric.value,
                "latitude": metric.third_party_type.latitude,
                "longitude": metric.third_party_type.longitude,
                "timestamp": metric.timestamp
            } for metric in third_party_metrics],
            "page": page,
            "limit": limit
        })
    except Exception as e:
        logging.error(f"Error fetching metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_metrics(page=1, limit=10):
    params = {'page': page, 'limit': limit}
    response = requests.get('https://michellevaz.pythonanywhere.com/api/metrics', params=params, timeout=120)
    response.raise_for_status()
    return response.json()

dash_app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=15000, n_intervals=0),
    html.H1("SysMonitor Metrics Dashboard"),
    
    dcc.Tabs([
        dcc.Tab(label='Device Metrics', children=[
            html.Div([
                dcc.Graph(id='cpu-usage-graph'),
                dcc.Graph(id='ram-usage-graph'),
                html.Label("Page:"),
                dcc.Input(id='page-input', type='number', value=1, min=1),
                html.Label("Limit:"),
                dcc.Input(id='limit-input', type='number', value=10, min=1)
            ])
        ]),
        dcc.Tab(label='Third Party Metrics', children=[
            html.Div([
                html.Label("Select Metric:"),
                dcc.Dropdown(
                    id='metric-dropdown',
                    options=[
                        {'label': 'Temperature', 'value': 'temp'},
                        {'label': 'Humidity', 'value': 'humidity'},
                        {'label': 'Wind Speed', 'value': 'wind_speed'},
                        {'label': 'Pressure', 'value': 'pressure'},
                        {'label': 'Air Quality Index', 'value': 'air_quality'},
                        {'label': 'Precipitation', 'value': 'precipitation'},
                        {'label': 'UV Index', 'value': 'uv_index'}
                    ],
                    value='temp',
                ),
                dcc.Graph(id='weather-map', style={'height': '600px'}),
                html.Label("Page:"),
                dcc.Input(id='page-input-weather', type='number', value=1, min=1),
                html.Label("Limit:"),
                dcc.Input(id='limit-input-weather', type='number', value=10, min=1)
            ])
        ])
    ])
])

@dash_app.callback(
    Output('cpu-usage-graph', 'figure'),
    Output('ram-usage-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('page-input', 'value'),
    Input('limit-input', 'value')
)
def update_device_metrics(n_intervals, page, limit):
    metrics = fetch_metrics(page, limit)
    device_metrics = metrics['device_metrics']

    cpu_usage_data = [metric for metric in device_metrics if metric['metric_id'] == 'cpu_usage']
    ram_usage_data = [metric for metric in device_metrics if metric['metric_id'] == 'ram_usage']

    cpu_usage_fig = go.Figure(data=[
        go.Scatter(x=[metric['timestamp'] for metric in cpu_usage_data],
                   y=[metric['value'] for metric in cpu_usage_data],
                   mode='lines+markers')
    ])
    cpu_usage_fig.update_layout(title='CPU Usage Over Time')

    ram_usage_fig = go.Figure(data=[
        go.Scatter(x=[metric['timestamp'] for metric in ram_usage_data],
                   y=[metric['value'] for metric in ram_usage_data],
                   mode='lines+markers')
    ])
    ram_usage_fig.update_layout(title='RAM Usage Over Time')

    return cpu_usage_fig, ram_usage_fig

@dash_app.callback(
    Output('weather-map', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('metric-dropdown', 'value'),
    Input('page-input-weather', 'value'),
    Input('limit-input-weather', 'value')
)
def update_weather_map(n_intervals, selected_metric, page, limit):
    metrics = fetch_metrics(page, limit)
    third_party_metrics = metrics['third_party_metrics']

    metric_map = {
        'temp': 'Temperature',
        'humidity': 'Humidity',
        'wind_speed': 'Wind Speed',
        'pressure': 'Pressure',
        'air_quality': 'Air Quality Index',
        'precipitation': 'Precipitation',
        'uv_index': 'UV Index'
    }

    selected_metric_name = metric_map[selected_metric]
    filtered_metrics = [metric for metric in third_party_metrics if metric['name'].endswith(selected_metric_name)]

    weather_map_fig = go.Figure(data=[
        go.Scattergeo(
            lon=[metric['longitude'] for metric in filtered_metrics],
            lat=[metric['latitude'] for metric in filtered_metrics],
            text=[f"{metric['name']}: {metric['value']}" for metric in filtered_metrics],
            mode='markers',
            marker=dict(
                size=8,
                color='blue',
                symbol='circle'
            )
        )
    ])
    weather_map_fig.update_layout(
        title=f'{selected_metric_name} Across Locations',
        geo=dict(
            scope='world',
            projection_type='equirectangular',
            showland=True,
            landcolor='rgb(217, 217, 217)',
            subunitwidth=1,
            countrywidth=1,
            subunitcolor='rgb(255, 255, 255)',
            countrycolor='rgb(255, 255, 255)'
        )
    )

    return weather_map_fig

if __name__ == '__main__':
    logging.info("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
