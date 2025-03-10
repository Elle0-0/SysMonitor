import os
import sys
from flask import Flask, jsonify, render_template
# from dash import Dash, dcc, html  # Commented out Dash import
# from dash.dependencies import Input, Output  # Commented out Dash import
# import plotly.graph_objs as go  # Commented out Plotly import
import logging
logging.basicConfig(level=logging.DEBUG)


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto import MetricsDTO
from models import Session, DeviceMetric, ThirdParty 
from lib_database.update_database import update_database

# Flask App
app = Flask(__name__)

# Dash App (Commented out)
# dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')

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
            {"device_id": metric.device_id, "cpu_usage": metric.cpu_usage, "memory_usage": metric.memory_usage,
             "air_quality_index": metric.air_quality_index, "latitude": metric.latitude, "longitude": metric.longitude}
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


# Commented out Dash layout and callback
# dash_app.layout = html.Div([
#     dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
#     html.H1("SysMonitor Metrics Dashboard"),
    
#     # Dropdown to select metric to display
#     html.Div([
#         html.Label("Select Metric:"),
#         dcc.Dropdown(
#             id='metric-dropdown',
#             options=[
#                 {'label': 'Temperature', 'value': 'temp'},
#                 {'label': 'Humidity', 'value': 'humidity'},
#                 {'label': 'Wind Speed', 'value': 'wind_speed'},
#                 {'label': 'Air Quality Index', 'value': 'air_quality'}
#             ],
#             value='temp',  # Default value
#         ),
#     ], style={'width': '25%', 'padding': '10px'}),

#     # Map displaying the selected weather metric
#     html.Div([
#         dcc.Graph(id='weather-map', style={'height': '600px'})
#     ]),
# ])

# Commented out Dash callback
# @dash_app.callback(
#     Output('weather-map', 'figure'),
#     [Input('interval-component', 'n_intervals'),
#      Input('metric-dropdown', 'value')]
# )
# def update_weather_map(n, selected_metric):
#     # Fetch the latest data from the Flask API endpoint
#     response = requests.get('http://localhost:5000/api/metrics')
#     data = response.json()

#     # Process third-party metrics (weather and air quality data)
#     air_quality_data = data['third_party_metrics']

#     # Determine values based on selected metric
#     metric_values = {
#         'temp': [d['value'] for d in air_quality_data if d['name'].startswith('Weather Data')],  # Temperature data
#         'humidity': [d['value'] for d in air_quality_data if d['name'].startswith('Weather Data')],  # Humidity data (assumed)
#         'wind_speed': [d['value'] for d in air_quality_data if d['name'].startswith('Weather Data')],  # Wind Speed data (assumed)
#         'air_quality': [d['value'] for d in air_quality_data if d['name'].startswith('Air Quality Index')]  # Air Quality data
#     }

#     # Set the values to plot based on selected metric
#     values_to_plot = metric_values.get(selected_metric, [])

#     # Get latitude and longitude for all locations
#     latitudes = [d['latitude'] for d in air_quality_data]
#     longitudes = [d['longitude'] for d in air_quality_data]
#     locations = [d['name'] for d in air_quality_data]

#     # Create map figure
#     map_figure = {
#         'data': [
#             go.Scattermapbox(
#                 lat=latitudes,
#                 lon=longitudes,
#                 mode='markers',
#                 marker=go.scattermapbox.Marker(size=10, color=values_to_plot, colorscale='Viridis', showscale=True),
#                 text=[f"{loc}: {val}" for loc, val in zip(locations, values_to_plot)],
#                 hoverinfo='text'
#             )
#         ],
#         'layout': go.Layout(
#             title=f'{selected_metric.capitalize()} Distribution',
#             mapbox_style="open-street-map",
#             zoom=6,
#             margin={'l': 0, 'r': 0, 't': 40, 'b': 0}
#         )
#     }

#     return map_figure

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
