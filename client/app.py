import sys
import os
import logging
from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from flask_caching import Cache

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lib_utils.blocktimer import BlockTimer
from lib_database.update_database import update_database
from dto import MetricsDTO
from models import DeviceMetric, ThirdParty, Metric, Device

class Application:
    def __init__(self):
        """Initialize the application with required configuration and logging."""
        self.config = self.load_config()
        self.logger = logging.getLogger(__name__)
        self.flask_app = Flask(__name__)
        self.dash_app = Dash(__name__, server=self.flask_app, url_base_pathname='/dash/')
        self.cache = Cache(self.flask_app, config={'CACHE_TYPE': 'simple'})
        self.setup_routes()
        self.setup_dash()
        self.engine = create_engine(os.getenv('DATABASE_URL'))
        self.SessionLocal = sessionmaker(bind=self.engine)

    def load_config(self):
        """Load configuration from a file."""
        import json
        with open('config.json') as config_file:
            return json.load(config_file)

    def setup_routes(self):
        """Setup the routes for the Flask application."""
        @self.flask_app.route('/')
        def index():
            return render_template('index.html')

        @self.flask_app.route('/api/update_metrics', methods=['POST'])
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

        @self.flask_app.route('/api/metrics', methods=['GET'])
        def get_metrics():
            session = self.SessionLocal()
            try:
                page = request.args.get('page', 1, type=int)
                limit = request.args.get('limit', 10, type=int)
                offset = (page - 1) * limit

                device_metrics = session.query(DeviceMetric).offset(offset).limit(limit).all()
                third_party_metrics = session.query(ThirdParty).offset(offset).limit(limit).all()

                return jsonify({
                    "device_metrics": [metric.to_dict() for metric in device_metrics],
                    "third_party_metrics": [metric.to_dict() for metric in third_party_metrics]
                })
            except Exception as e:
                logging.error(f"Error fetching metrics: {str(e)}")
                return jsonify({"error": str(e)}), 500
            finally:
                session.close()

    def setup_dash(self):
        """Setup the Dash application."""
        self.dash_app.layout = html.Div([
            dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
            dcc.Dropdown(id='metric-dropdown', options=[
                {'label': 'Temperature', 'value': 'temp'},
                {'label': 'Humidity', 'value': 'humidity'},
                {'label': 'Wind Speed', 'value': 'wind_speed'},
                {'label': 'Pressure', 'value': 'pressure'},
                {'label': 'Air Quality Index', 'value': 'air_quality'},
                {'label': 'Precipitation', 'value': 'precipitation'},
                {'label': 'UV Index', 'value': 'uv_index'}
            ], value='temp'),
            dcc.Input(id='page-input-weather', type='number', value=1),
            dcc.Input(id='limit-input-weather', type='number', value=10),
            dcc.Graph(id='weather-map'),
            dcc.Input(id='page-input', type='number', value=1),
            dcc.Input(id='limit-input', type='number', value=10),
            dcc.Graph(id='cpu-usage-gauge'),
            dcc.Graph(id='ram-usage-gauge'),
            dcc.Graph(id='cpu-usage-histogram'),
            dcc.Graph(id='ram-usage-histogram')
        ])

        @self.dash_app.callback(
            Output('cpu-usage-gauge', 'figure'),
            Output('ram-usage-gauge', 'figure'),
            Output('cpu-usage-histogram', 'figure'),
            Output('ram-usage-histogram', 'figure'),
            Input('interval-component', 'n_intervals'),
            Input('page-input', 'value'),
            Input('limit-input', 'value')
        )
        def update_device_metrics(n_intervals, page, limit):
            metrics = self.fetch_metrics(page, limit)
            device_metrics = metrics['device_metrics']

            cpu_usage_data = [metric for metric in device_metrics if metric['metric_id'] == 'cpu_usage']
            ram_usage_data = [metric for metric in device_metrics if metric['metric_id'] == 'ram_usage']

            cpu_usage_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=cpu_usage_data[-1]['value'] if cpu_usage_data else 0,
                title={'text': "CPU Usage"},
                gauge={'axis': {'range': [None, 100]}}
            ))

            ram_usage_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=ram_usage_data[-1]['value'] if ram_usage_data else 0,
                title={'text': "RAM Usage"},
                gauge={'axis': {'range': [None, 100]}}
            ))

            cpu_usage_histogram = go.Figure(go.Histogram(
                x=[metric['value'] for metric in cpu_usage_data],
                nbinsx=20
            ))
            cpu_usage_histogram.update_layout(title='CPU Usage Distribution')

            ram_usage_histogram = go.Figure(go.Histogram(
                x=[metric['value'] for metric in ram_usage_data],
                nbinsx=20
            ))
            ram_usage_histogram.update_layout(title='RAM Usage Distribution')

            return cpu_usage_gauge, ram_usage_gauge, cpu_usage_histogram, ram_usage_histogram

        @self.dash_app.callback(
            Output('weather-map', 'figure'),
            Input('interval-component', 'n_intervals'),
            Input('metric-dropdown', 'value'),
            Input('page-input-weather', 'value'),
            Input('limit-input-weather', 'value')
        )
        def update_weather_map(n_intervals, selected_metric, page, limit):
            metrics = self.fetch_metrics(page, limit)
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

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def fetch_metrics(page=1, limit=10):
        params = {'page': page, 'limit': limit}
        response = requests.get('https://michellevaz.pythonanywhere.com/api/metrics', params=params, timeout=300)  # Increase timeout to 300 seconds
        response.raise_for_status()
        return response.json()

    def run(self) -> int:
        """Main application logic."""
        try:
            self.logger.info("Starting Flask application...")
            self.flask_app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
            self.logger.info("Application completed successfully")
            return 0
        except Exception as e:
            self.logger.exception("Application failed with error: %s", str(e))
            return 1

def main() -> int:
    """Entry point for the application."""
    app = Application()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
else:
    """
    If this isn't the main entry point, assume we're hosted on a WSGI
    Web Server and hence create the app object pointing to our Flask
    instance so that the calling WSGI config file has what it needs.
    """
    appForWSGI = Application()
    app = appForWSGI.flask_app
