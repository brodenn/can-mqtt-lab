from flask import Flask, request, jsonify, render_template
from data_store import data_store
import os

app = Flask(__name__, template_folder='frontend')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    data_store[data['id']] = data['payload']
    return '', 204

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(data_store)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
