import json
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from textblob import TextBlob

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


@app.route("/", methods=["GET", "POST"])
def index():
    background_color = "linear-gradient(to bottom, #a0e1f2, #e0f7ff)"
    sentiment = "neutral"  # Default sentiment
    
    if request.method == "POST":
        user_input = request.form["user_input"]
        
        # Analyze the sentiment of the user's input
        blob = TextBlob(user_input)
        sentiment_score = blob.sentiment.polarity
        
        if sentiment_score > 0:
            sentiment = "positive"
            background_color = "lightgreen"  # Positive sentiment
        elif sentiment_score < 0:
            sentiment = "negative"
            background_color = "lightcoral"  # Negative sentiment
        else:
            sentiment = "neutral"
            background_color = "lightgray"  # Neutral sentiment

    return render_template("index.html", background_color=background_color, sentiment=sentiment)


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
