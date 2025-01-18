import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from textblob import TextBlob
import razorpay

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session handling
socketio = SocketIO(app)  # Initialize Flask-SocketIO
from threading import Lock
lock = Lock()

# Global list to store messages
messages = []

# Define the maximum size of the messages list
MAX_MESSAGES = 100


# File path for flag count storage
FILE_PATH = 'flag_count.json'

RAZORPAY_KEY_ID = ""
RAZORPAY_KEY_SECRET = ""

# Razorpay client initialization
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


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
     # Default values
    background_color = session.pop("background_color", "linear-gradient(to bottom, #a0e1f2, #e0f7ff)")
    sentiment = session.pop("sentiment", "neutral")

    if request.method == "POST":
        user_input = request.form["user_input"]
        messages.append(user_input)  # Store the message

        # Remove the oldest message if the list exceeds the max size
        if len(messages) > MAX_MESSAGES:
            messages.pop(0)  # Remove the first (oldest) message

        # Analyze sentiment
        blob = TextBlob(user_input)
        sentiment_score = blob.sentiment.polarity

        if sentiment_score >= 0:
            sentiment = "positive"
            background_color = "linear-gradient(to bottom, #56ab2f, #a8e063)"  # Green gradient
        else:
            sentiment = "negative"
            background_color = "linear-gradient(to bottom, #ff416c, #ff4b2b)"  # Red gradient

        # Store background and sentiment in session for redirection
        session["background_color"] = background_color
        session["sentiment"] = sentiment

        # Redirect to avoid form resubmission
        return redirect(url_for("index"))

    return render_template(
        "index.html",
        background_color=background_color,
        sentiment=sentiment,
        messages=messages,
    )

@app.route('/support')
def support_page():
    return render_template("support.html", razorpay_key=RAZORPAY_KEY_ID)

@app.route('/create-order', methods=['POST'])
def create_order():
    try:
        amount = int(float(request.json['amount']) * 100)  # Convert to paise
        payment_order = razorpay_client.order.create({
            "amount": amount,  # Amount in paise
            "currency": "INR",
            "payment_capture": "1"
        })
        return jsonify({"order_id": payment_order['id']})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/payment-success', methods=['POST'])
def payment_success():
    payment_id = request.form['razorpay_payment_id']
    order_id = request.form['razorpay_order_id']
    signature = request.form['razorpay_signature']
    
    try:
        # Verifying payment signature
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
        return "Payment successful! Thank you for the coffee! 😊", 200
    except razorpay.errors.SignatureVerificationError:
        return "Payment verification failed. Please try again.", 400

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
