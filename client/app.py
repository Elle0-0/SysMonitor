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

@dash_app.callback(
    [Output('cpu-usage-graph', 'figure'),
     Output('ram-usage-graph', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('page-input', 'value'),
     Input('limit-input', 'value')]
)
def update_device_metrics(n, page, limit):
    page = page or 1
    limit = limit or 10
    
    try:
        data = fetch_metrics(page=page, limit=limit)
    except requests.RequestException as e:
        logging.error(f"Error fetching device metrics: {e}")
        return {}, {}

    device_metrics = data.get('device_metrics', [])
    if not device_metrics:
        logging.warning("No device metrics received.")
        return {}, {}

    cpu_metrics = [metric for metric in device_metrics if metric['metric_id'] == 'a96727f1-e90a-4965-831b-af1fd162cfca']
    ram_metrics = [metric for metric in device_metrics if metric['metric_id'] == '2c368bee-acbc-45b3-91f8-02fa27b22434']

    return {
        'data': [go.Scatter(x=[m['timestamp'] for m in cpu_metrics], y=[m['value'] for m in cpu_metrics], mode='lines+markers', name='CPU Usage')],
        'layout': go.Layout(title='CPU Usage Over Time', xaxis={'title': 'Timestamp'}, yaxis={'title': 'CPU Usage (%)'})
    }, {
        'data': [go.Scatter(x=[m['timestamp'] for m in ram_metrics], y=[m['value'] for m in ram_metrics], mode='lines+markers', name='RAM Usage')],
        'layout': go.Layout(title='RAM Usage Over Time', xaxis={'title': 'Timestamp'}, yaxis={'title': 'RAM Usage (%)'})
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
