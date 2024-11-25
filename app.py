import json
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)  # Initialize Flask-SocketIO
from threading import Lock
lock = Lock()

# File path for flag count storage
FILE_PATH = 'flag_count.json'


def read_flag_count():
    """Reads flag count from JSON file."""
    with lock:
        with open(FILE_PATH, 'r') as file:
            return json.load(file)

def update_flag_count(country):
    """Updates flag count in JSON file."""
    data = read_flag_count()
    if country not in data:
        data[country] = 0
    data[country] += 1
    with lock:
        with open(FILE_PATH, 'w') as file:
            json.dump(data, file, indent=4)
        return data


@app.route('/')
def index():
    """Serves the index page."""
    return render_template('index.html')


@app.route('/raise_flag', methods=['POST'])
def raise_flag():
    """API endpoint to raise a flag."""
    country = request.json.get('country')
    if country not in ['india']:
        return jsonify({"error": "Invalid country"}), 400

    # Update the flag count
    updated_data = update_flag_count(country)

    # Emit the updated flag count to all clients via WebSocket
    socketio.emit('update_score', updated_data)

    return jsonify({"message": f"{country.capitalize()} flag raised!", "count": updated_data[country]})


@socketio.on('connect')
def handle_connect():
    """Send current flag count to the new connected client."""
    data = read_flag_count()
    emit('update_score', data)


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
