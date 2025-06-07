from flask import Flask, request, jsonify, render_template
from data_store import update_data, get_data
import threading
import json
import time
import os
import paho.mqtt.client as mqtt

app = Flask(__name__, template_folder='frontend')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    can_id = data.get('id')
    payload = data.get('payload')

    if not can_id or not isinstance(payload, list):
        return jsonify({'error': 'Invalid CAN message'}), 400

    update_data(can_id, payload)
    return '', 204

@app.route('/api/data', methods=['GET'])
def send_data():
    # Convert deque objects to lists before JSON serialization
    raw_data = get_data()
    json_data = {
        can_id: {
            'payload': entry['payload'],
            'timestamp': entry['timestamp']
        } for can_id, entries in raw_data.items() for entry in [entries[-1]]
    }
    return jsonify(json_data)

# MQTT Setup
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe("canbus/data")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        can_id = data.get('id')
        payload = data.get('payload')
        if can_id and isinstance(payload, list):
            update_data(can_id, payload)
    except Exception as e:
        print("MQTT message error:", e)

def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("mqtt-broker", 1883, 60)
    client.loop_forever()

# Start MQTT thread
threading.Thread(target=mqtt_thread, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
