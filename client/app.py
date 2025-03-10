import os
import sys
from flask import Flask, jsonify, render_template, request
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

@app.route('/')
def index():
    return render_template('index.html')

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
        # Get pagination parameters from the request
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = (page - 1) * limit

        # Query device metrics with pagination
        device_metrics = session.query(DeviceMetric).order_by(DeviceMetric.timestamp.desc()).offset(offset).limit(limit).all()
        third_party_metrics = session.query(ThirdParty).order_by(ThirdParty.timestamp.desc()).offset(offset).limit(limit).all()

        device_metrics_data = [
            {
                "device_id": metric.device_id,
                "metric_id": metric.metric_id,
                "value": metric.value,
                "timestamp": metric.timestamp
            }
            for metric in device_metrics
        ]
        
        third_party_metrics_data = [
            {
                "name": metric.name,
                "value": metric.value,
                "latitude": metric.third_party_type.latitude,
                "longitude": metric.third_party_type.longitude,
                "timestamp": metric.timestamp
            }
            for metric in third_party_metrics
        ]

        return jsonify({
            "device_metrics": device_metrics_data,
            "third_party_metrics": third_party_metrics_data,
            "page": page,
            "limit": limit
        })
    except Exception as e:
        logging.error(f"Error fetching metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# Dash layout and callback
dash_app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=15000, n_intervals=0),  # Update interval to 15000 milliseconds (15 seconds)
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
                        {'label': 'Air Quality Index', 'value': 'air_quality'}
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

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_metrics(page=1, limit=10):
    params = {'page': page, 'limit': limit}
    response = requests.get('https://michellevaz.pythonanywhere.com/api/metrics', params=params, timeout=120)  # Increase timeout to 120 seconds
    response.raise_for_status()
    return response.json()

@dash_app.callback(
    [Output('cpu-usage-graph', 'figure'),
     Output('ram-usage-graph', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('page-input', 'value'),
     Input('limit-input', 'value')]
)
def update_device_metrics(n, page, limit):
    try:
        data = fetch_metrics(page=page, limit=limit)  # Use dynamic page and limit values
    except requests.RequestException as e:
        logging.error(f"Error fetching device metrics: {e}")
        return {}, {}

    device_metrics = data['device_metrics']
    cpu_metrics = [metric for metric in device_metrics if metric['metric_id'] == 1]
    ram_metrics = [metric for metric in device_metrics if metric['metric_id'] == 2]

    cpu_figure = {
        'data': [
            go.Scatter(
                x=[metric['timestamp'] for metric in cpu_metrics],
                y=[metric['value'] for metric in cpu_metrics],
                mode='lines+markers',
                name='CPU Usage'
            )
        ],
        'layout': go.Layout(
            title='CPU Usage Over Time',
            xaxis={'title': 'Timestamp'},
            yaxis={'title': 'CPU Usage (%)'}
        )
    }

    ram_figure = {
        'data': [
            go.Scatter(
                x=[metric['timestamp'] for metric in ram_metrics],
                y=[metric['value'] for metric in ram_metrics],
                mode='lines+markers',
                name='RAM Usage'
            )
        ],
        'layout': go.Layout(
            title='RAM Usage Over Time',
            xaxis={'title': 'Timestamp'},
            yaxis={'title': 'RAM Usage (%)'}
        )
    }

    return cpu_figure, ram_figure

@dash_app.callback(
    Output('weather-map', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('metric-dropdown', 'value'),
     Input('page-input-weather', 'value'),
     Input('limit-input-weather', 'value')]
)
def update_weather_map(n, selected_metric, page, limit):
    try:
        data = fetch_metrics(page=page, limit=limit)  # Use dynamic page and limit values
    except requests.RequestException as e:
        logging.error(f"Error fetching weather metrics: {e}")
        return {}

    third_party_metrics = data['third_party_metrics']
    metric_values = {
        'temp': [d['value'] for d in third_party_metrics if d['name'].endswith('Temperature')],
        'humidity': [d['value'] for d in third_party_metrics if d['name'].endswith('Humidity')],
        'wind_speed': [d['value'] for d in third_party_metrics if d['name'].endswith('Wind Speed')],
        'air_quality': [d['value'] for d in third_party_metrics if d['name'].endswith('Air Quality Index')]
    }

    values_to_plot = metric_values.get(selected_metric, [])
    latitudes = [d['latitude'] for d in third_party_metrics]
    longitudes = [d['longitude'] for d in third_party_metrics]
    locations = [d['name'] for d in third_party_metrics]

    map_figure = {
        'data': [
            go.Scattermapbox(
                lat=latitudes,
                lon=longitudes,
                mode='markers',
                marker=go.scattermapbox.Marker(size=9, color=values_to_plot, colorscale="Viridis", colorbar={'title': selected_metric}),
                text=locations,
            )
        ],
        'layout': go.Layout(
            mapbox={'style': "carto-positron", 'center': {'lat': 53.3498, 'lon': -6.2603}, 'zoom': 8},
            margin={'r': 0, 't': 0, 'b': 0, 'l': 0},
            title="Real-Time Metrics Map"
        )
    }
    return map_figure

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)  # Enable threading
