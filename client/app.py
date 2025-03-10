import os
import sys
from flask import Flask, jsonify, render_template, request
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import logging
import requests
logging.basicConfig(level=logging.DEBUG)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto import MetricsDTO
from models import Session, DeviceMetric, ThirdParty
from lib_database.update_database import update_database

# Flask App
app = Flask(__name__)

# Dash App
dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update_metrics', methods=['POST'])
def update_metrics():
    logging.info("Received request to update metrics")
    
    try:
        # Get data from the incoming request (e.g., JSON data)
        metrics_data = request.get_json()
        logging.debug(f"Metrics data received: {metrics_data}")
        
        # Create a DTO (data transfer object) to pass to the update_database function
        metrics_dto = MetricsDTO.from_dict(metrics_data)
        logging.debug(f"MetricsDTO created: {metrics_dto}")

        # Call the update_database function with the metrics DTO
        update_database(metrics_dto)
        
        logging.info("Metrics successfully updated in the database")
        # Respond with success
        return jsonify({"message": "Metrics updated successfully!"}), 200
        
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    session = Session()
    try:
        # Fetch the most recent 5 device metrics from the database
        device_metrics = session.query(DeviceMetric).order_by(DeviceMetric.timestamp.desc()).limit(5).all()
        
        # Fetch the most recent 5 third-party metrics from the database
        third_party_metrics = session.query(ThirdParty).order_by(ThirdParty.timestamp.desc()).limit(5).all()

        # Prepare the device metrics data
        device_metrics_data = [
            {
                "metric_id": metric.metric_id, 
                "cpu_usage": metric.value if metric.metric.name == "cpu_usage" else None,
                "ram_usage": metric.value if metric.metric.name == "ram_usage" else None
            }
            for metric in device_metrics
        ]
        
        # Prepare the third-party metrics data
        third_party_metrics_data = [
            {
                "location": metric.name,
                "temperature": metric.temp,
                "humidity": metric.humidity,
                "wind_speed": metric.wind_speed,
                "pressure": metric.pressure,
                "air_quality_index": metric.air_quality_index,
                "precipitation": metric.precipitation,
                "uv_index": metric.uv_index,
                "timestamp": metric.timestamp
            }
            for metric in third_party_metrics
        ]

        # Return the data as JSON
        return jsonify({
            "device_metrics": device_metrics_data,
            "third_party_metrics": third_party_metrics_data
        })
    except Exception as e:
        logging.error(f"Error fetching metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# Dash layout and callback
dash_app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    html.H1("SysMonitor Metrics Dashboard"),
    
    # Dropdown to select metric to display
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
            value='temp',  # Default value
        ),
    ], style={'width': '25%', 'padding': '10px'}),

    # Map displaying the selected weather metric
    html.Div([
        dcc.Graph(id='weather-map', style={'height': '600px'})
    ]),
])

@dash_app.callback(
    Output('weather-map', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('metric-dropdown', 'value')]
)
def update_weather_map(n, selected_metric):
    response = requests.get('https://michellevaz.pythonanywhere.com/api/metrics')
    data = response.json()

    air_quality_data = data['third_party_metrics']
    metric_values = {
        'temp': [d['value'] for d in air_quality_data], 
        'humidity': [d['value'] for d in air_quality_data],
        'wind_speed': [d['value'] for d in air_quality_data],
        'air_quality': [d['value'] for d in air_quality_data]
    }

    values_to_plot = metric_values.get(selected_metric, [])
    latitudes = [d['latitude'] for d in air_quality_data]
    longitudes = [d['longitude'] for d in air_quality_data]
    locations = [d['name'] for d in air_quality_data]

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
    app.run(debug=True, host='0.0.0.0', port=5000)
