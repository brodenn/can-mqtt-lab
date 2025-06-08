from flask import Flask, request, jsonify, render_template
from data_store import update_data, get_data, get_latest_per_id
import threading
import json
import time
import paho.mqtt.client as mqtt
import logging

app = Flask(__name__, template_folder='frontend')

try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    can_id = data.get('id')
    payload = data.get('payload')
    timestamp = data.get('timestamp') or time.time()
    extended = data.get('extended', False)
    print(f"POSTED DATA: {data}")

    if not can_id or not isinstance(payload, list):
        print("❌ Invalid CAN message in HTTP POST:", data)
        return jsonify({'error': 'Invalid CAN message'}), 400

    update_data(can_id, payload, timestamp=timestamp, extended=extended)
    print(f"📡 HTTP POST: {can_id} → {payload}")
    return '', 204

@app.route('/api/data', methods=['GET'])
def send_data():
    print(f"📤 HTTP GET: Sending latest per CAN ID")
    return jsonify(get_latest_per_id())

# 🚦 DEBUG: Show ALL message history per CAN ID
@app.route('/api/raw', methods=['GET'])
def raw_data():
    return jsonify(get_data())

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT connected.")
        client.subscribe("can/messages")
    else:
        print(f"❌ MQTT connect failed: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        can_id = data.get('id')
        payload = data.get('payload')
        timestamp = data.get('timestamp') or time.time()
        extended = data.get('extended', False)
        print(f"MQTT DATA: {data}")

        if can_id and isinstance(payload, list):
            update_data(can_id, payload, timestamp=timestamp, extended=extended)
            print(f"📥 MQTT: {can_id} → {payload}")
    except Exception as e:
        print("❌ MQTT message error:", e)

def mqtt_thread():
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    while True:
        try:
            client.connect("mqtt-broker", 1883, 60)
            client.loop_forever()
            break
        except Exception as e:
            print(f"⏳ MQTT reconnecting... {e}")
            time.sleep(2)

threading.Thread(target=mqtt_thread, daemon=True).start()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000)
