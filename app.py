import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from textblob import TextBlob
import razorpay
from threading import Lock
from io import BytesIO
from reportlab.pdfgen import canvas
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, jsonify, request, send_file, make_response
from io import BytesIO
import json
import pygame
import threading
import time


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
        
data = read_flag_count()
india_flag_count = data.get("india", 0)

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
def play_music_from_97_seconds():
    """Function to play the music from the 15-second mark."""
    # Load the MP3 file
    pygame.mixer.init()
    pygame.mixer.music.load("song.mp3")
    
    # Set the position to 15 seconds and start playing
    pygame.mixer.music.play(start=97)
    # Wait for 15 seconds
    time.sleep(30)
    
    # Stop the music
    pygame.mixer.music.stop()

@app.route("/", methods=["GET", "POST"])
def index():
    # Default values
    background_color = session.pop("background_color", "linear-gradient(to bottom, #a0e1f2, #e0f7ff)")
    sentiment_label = session.pop("sentiment", "neutral")

    if request.method == "POST":
        user_input = request.form["user_input"]
        messages.append(user_input)  # Store the message

        # Remove the oldest message if the list exceeds the max size
        if len(messages) > MAX_MESSAGES:
            messages.pop(0)

        # Analyze sentiment
        blob = TextBlob(user_input)
        sentiment_score = blob.sentiment.polarity

        # Determine sentiment and background color with finer granularity
        if sentiment_score < -0.9:
            sentiment_label = "extremely negative"
            background_color = "linear-gradient(to bottom, #4b0000, #8b0000)"  # Dark maroon to dark red
        elif -0.9 <= sentiment_score < -0.7:
            sentiment_label = "very negative"
            background_color = "linear-gradient(to bottom, #8b0000, #ff0000)"  # Dark red to red
        elif -0.7 <= sentiment_score < -0.5:
            sentiment_label = "quite negative"
            background_color = "linear-gradient(to bottom, #ff3300, #ff6666)"  # Orange-red gradient
        elif -0.5 <= sentiment_score < -0.3:
            sentiment_label = "negative"
            background_color = "linear-gradient(to bottom, #ff416c, #ff4b2b)"  # Red gradient
        elif -0.3 <= sentiment_score < -0.1:
            sentiment_label = "slightly negative"
            background_color = "linear-gradient(to bottom, #ff8080, #ffc0c0)"  # Light red to pink
        elif -0.1 <= sentiment_score < 0.1:
            sentiment_label = "neutral"
            background_color = "linear-gradient(to bottom, #d4ffcc, #b0ff99)"  # Blue gradient
        elif 0.1 <= sentiment_score < 0.3:
            sentiment_label = "slightly positive"
            background_color = "linear-gradient(to bottom, #d4ffcc, #b0ff99)"  # Light green
        elif 0.3 <= sentiment_score < 0.5:
            sentiment_label = "positive"
            background_color = "linear-gradient(to bottom, #56ab2f, #a8e063)"  # Light green gradient
        elif 0.5 <= sentiment_score < 0.7:
            sentiment_label = "quite positive"
            background_color = "linear-gradient(to bottom, #32cd32, #7fff00)"  # Lime to chartreuse
        elif 0.7 <= sentiment_score < 0.9:
            sentiment_label = "very positive"
            background_color = "linear-gradient(to bottom, #006400, #32cd32)"  # Dark green to lime
        elif sentiment_score >= 0.9:
            sentiment_label = "extremely positive"
            background_color = "linear-gradient(to bottom, #003300, #009933)"  # Deep green


        # Store background and sentiment in session for redirection
        session["background_color"] = background_color
        session["sentiment"] = sentiment_label

        # Redirect to avoid form resubmission
        return redirect(url_for("index"))

    return render_template(
        "index.html",
        background_color=background_color,
        sentiment=sentiment_label,
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
        # Start the music in a background thread
    threading.Thread(target=play_music_from_97_seconds).start()

    return jsonify({"message": f"{country.capitalize()} flag raised!", "count": updated_data[country]})

@app.route('/download_certificate', methods=['GET'])
def download_certificate_png():
    """Endpoint to generate and download the certificate as PNG."""
    # Fetch the template image from the provided URL
    template_url = "https://i.pinimg.com/736x/d7/be/5c/d7be5cfaa6cc82cbf58bfe0c3369ab8a.jpg"
    
    try:
        response = requests.get(template_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))  # Open the template image
            img = img.resize((1080, 1080))  # Resize to Instagram post size (1080x1080)
        else:
            print("Unable to fetch template image!")
            return "Template image fetch failed"
    except Exception as e:
        print(f"Error fetching template image: {e}")
        return "Template image fetch failed"

    # Initialize drawing context
    draw = ImageDraw.Draw(img)

    # Fonts (adjust path if needed)
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        subtitle_font = ImageFont.truetype("arial.ttf", 40)
        text_font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        title_font = subtitle_font = text_font = ImageFont.load_default()

    # Add your customized text to the image
    draw.text((540, 200), "Congratulations on hosting the Digital Indian Flag!", fill="black", font=text_font, anchor="mm")
    draw.text((540, 270), f"Flag Host Count: {india_flag_count}", fill="black", font=text_font, anchor="mm")
    draw.text((540, 340), "This is our 76th Republic Day.", fill="black", font=text_font, anchor="mm")
    draw.text((540, 410), "#Digital Tiranga", fill="black", font=text_font, anchor="mm")

    # Save to BytesIO for download
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="certificate.png", mimetype="image/png")

@socketio.on('connect')
def handle_connect():
    """Send current flag count to the new connected client."""
    data = read_flag_count()
    emit('update_score', data)


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
