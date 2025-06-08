from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from data_store import update_data, get_data, get_latest_per_id
import threading
import json
import time
import paho.mqtt.client as mqtt
import logging
import os

# === Flask App Setup ===
app = Flask(__name__, template_folder='frontend')
socketio = SocketIO(app, cors_allowed_origins="*")

# Optional CORS Support
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# === Configuration ===
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "can/messages"

# === HTTP Routes ===

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print("❌ JSON decode error:", e)
        return jsonify({'error': 'Invalid JSON'}), 400
    return process_can_message(data, source="HTTP")

@app.route('/api/data', methods=['GET'])
def send_data():
    latest = get_latest_per_id()

    # Decode next stop name for frontend
    NEXT_STOP_ID = "0x103"
    if NEXT_STOP_ID in latest:
        payload = latest[NEXT_STOP_ID].get("payload", [])
        try:
            stop_name = bytes(payload).decode("utf-8", errors="replace").strip("\x00")
            latest[NEXT_STOP_ID]["decoded"] = stop_name
        except Exception:
            latest[NEXT_STOP_ID]["decoded"] = ""

    return jsonify(latest)

@app.route('/api/raw', methods=['GET'])
def raw_data():
    return jsonify(get_data())

# === CAN Message Handler ===

def process_can_message(data, source="MQTT"):
    can_id = data.get('id')
    payload = data.get('payload')
    timestamp = data.get('timestamp') or time.time()
    extended = data.get('extended', False)

    if not can_id or not isinstance(payload, list):
        print(f"❌ Invalid {source} CAN message:", data)
        return jsonify({'error': 'Invalid CAN message'}), 400

    update_data(can_id, payload, timestamp=timestamp, extended=extended)

    socketio.emit("can_update", {can_id: {
        "payload": payload,
        "timestamp": timestamp,
        "extended": extended
    }})

    print(f"📡 {source}: {can_id} → {payload}")
    return ('', 204) if source == "HTTP" else None

# === MQTT Setup ===

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ MQTT connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        process_can_message(data, source="MQTT")
    except Exception as e:
        print(f"❌ MQTT processing error: {e} | Raw: {msg.payload}")

def mqtt_thread():
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            print(f"⏳ MQTT reconnecting in 2s... {e}")
            time.sleep(2)

# === Start App ===

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    threading.Thread(target=mqtt_thread, daemon=True).start()

    # Don't use `threaded=True` here with eventlet!
    socketio.run(app, host='0.0.0.0', port=5000)
