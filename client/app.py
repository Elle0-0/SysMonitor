import sys
import os
import logging
from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from flask_caching import Cache
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lib_utils.blocktimer import BlockTimer
from lib_database.update_database import update_database
from dto import MetricsDTO
from models import DeviceMetric, ThirdParty, Metric, Device, ThirdPartyType

class Application:
    def __init__(self):
        """Initialize the application with required configuration and logging."""
        self.config = self.load_config()
        self.logger = logging.getLogger(__name__)
        self.flask_app = Flask(__name__)
        self.cache = Cache(self.flask_app, config={'CACHE_TYPE': 'simple'})
        self.setup_routes()
        self.engine = create_engine(os.getenv('DATABASE_URL'))
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.weather_data_cache = {}
        self.device_metrics_cache = []
        self.last_updated_time = None

    def load_config(self):
        """Load configuration from a file."""
        import json
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.json'))
        print(f"Loading configuration from: {config_path}")
        with open(config_path, 'r') as config_file:
            return json.load(config_file)

    def setup_routes(self):
        """Setup the routes for the Flask application."""
        @self.flask_app.route('/')
        def index():
            try:
                logging.info("Fetching weather data...")
                self.fetch_weather_data()
                logging.info("Fetching device metrics...")
                self.fetch_device_metrics(page=1, limit=5)  # Fetch initial data with pagination
                logging.info("Rendering template...")
                return render_template('index.html', weather_data=self.weather_data_cache, device_metrics=self.device_metrics_cache, last_updated_time=self.last_updated_time, current_page=1, limit=5)
            except Exception as e:
                logging.error(f"Error loading data: {str(e)}")
                return render_template('index.html', weather_data={}, device_metrics=[], last_updated_time="N/A", current_page=1, limit=5)

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

        @self.flask_app.route('/api/device_metrics', methods=['GET'])
        def get_device_metrics():
            session = self.SessionLocal()
            try:
                page = request.args.get('page', 1, type=int) or 1
                limit = request.args.get('limit', 5, type=int) or 5
                offset = (page - 1) * limit

                device_metrics = session.query(DeviceMetric).order_by(DeviceMetric.timestamp.desc()).offset(offset).limit(limit).all()

                if not device_metrics:
                    logging.warning("No device metrics data found.")
                    
                return jsonify({
                    "device_metrics": [{
                        "device_id": metric.device_id,
                        "metric_id": metric.metric_id,
                        "value": metric.value,
                        "timestamp": metric.timestamp
                    } for metric in device_metrics],
                    "page": page,
                    "limit": limit
                })
            except Exception as e:
                logging.error(f"Error fetching device metrics: {str(e)}")
                return jsonify({"error": str(e)}), 500
            finally:
                session.close()

        @self.flask_app.route('/api/weather_data', methods=['GET'])
        def get_weather_data():
            session = self.SessionLocal()
            try:
                page = request.args.get('page', 1, type=int) or 1
                limit = request.args.get('limit', 10, type=int) or 10
                offset = (page - 1) * limit

                third_party_metrics = session.query(ThirdParty).order_by(ThirdParty.timestamp.desc()).offset(offset).limit(limit).all()

                if not third_party_metrics:
                    logging.warning("No weather data found.")
                    
                return jsonify({
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
                logging.error(f"Error fetching weather data: {str(e)}")
                return jsonify({"error": str(e)}), 500
            finally:
                session.close()

        @self.flask_app.route('/update_device_metrics')
        def update_device_metrics():
            self.fetch_device_metrics()
            return jsonify(device_metrics=self.device_metrics_cache, last_updated_time=self.last_updated_time)

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def fetch_metrics(endpoint, params=None):
        response = requests.get(endpoint, params=params, timeout=10)  # Set a timeout of 10 seconds
        response.raise_for_status()
        return response.json()

    def fetch_weather_data(self):
        try:
            logging.info("Requesting weather data from API...")
            start_time = time.time()
            data = self.fetch_metrics(f"{self.config['server_url']}/api/weather_data")
            self.weather_data_cache = {
                'AirQuality': [metric for metric in data['third_party_metrics'] if 'Air Quality Index' in metric['name']],
                'Humidity': [metric for metric in data['third_party_metrics'] if 'Humidity' in metric['name']],
                'Precipitation': [metric for metric in data['third_party_metrics'] if 'Precipitation' in metric['name']],
                'Pressure': [metric for metric in data['third_party_metrics'] if 'Pressure' in metric['name']],
                'Temperature': [metric for metric in data['third_party_metrics'] if 'Temperature' in metric['name']],
                'UVIndex': [metric for metric in data['third_party_metrics'] if 'UV Index' in metric['name']],
                'WindSpeed': [metric for metric in data['third_party_metrics'] if 'Wind Speed' in metric['name']]
            }
            self.last_updated_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            end_time = time.time()
            logging.info(f"Weather data fetched successfully in {end_time - start_time} seconds.")
        except Exception as e:
            logging.error(f"Error fetching weather data: {str(e)}")
            self.weather_data_cache = {}
            self.last_updated_time = "N/A"

    def fetch_device_metrics(self, page=1, limit=5):
        try:
            logging.info("Requesting device metrics from API...")
            start_time = time.time()
            data = self.fetch_metrics(f"{self.config['server_url']}/api/device_metrics", params={'page': page, 'limit': limit})
            self.device_metrics_cache = data['device_metrics']
            end_time = time.time()
            logging.info(f"Device metrics fetched successfully in {end_time - start_time} seconds.")
        except Exception as e:
            logging.error(f"Error fetching device metrics: {str(e)}")
            self.device_metrics_cache = []

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
