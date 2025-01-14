from flask import Flask, render_template, jsonify, request, send_file, make_response
from flask_socketio import SocketIO, emit
from textblob import TextBlob
from threading import Lock
from io import BytesIO
from reportlab.pdfgen import canvas
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, jsonify, request, send_file, make_response
from io import BytesIO
import json

app = Flask(__name__)
socketio = SocketIO(app)
lock = Lock()

# Global list to store messages
messages = []

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
        messages.append(user_input)  # Store the message

        # Analyze sentiment
        blob = TextBlob(user_input)
        sentiment_score = blob.sentiment.polarity

        if sentiment_score >= 0:
            sentiment = "positive"
            background_color = "linear-gradient(to bottom, #56ab2f, #a8e063)"  # Green gradient
        else:
            sentiment = "negative"
            background_color = "linear-gradient(to bottom, #ff416c, #ff4b2b)"  # Red gradient

    flag_count = read_flag_count()
    return render_template(
        "index.html",
        background_color=background_color,
        sentiment=sentiment,
        messages=messages,
        flag_count=flag_count
    )

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

from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from flask import send_file

@app.route('/download_certificate', methods=['GET'])
def download_certificate_png():
    """Endpoint to generate and download the certificate as PNG."""
    # Fetch the template image from the provided URL
    template_url = "https://www.canva.com/design/DAGcMnAFKcY/9aG9he3EP79Sp775xkx06w/view?utm_content=DAGcMnAFKcY&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h9450dd3aaa.png"
    
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
    draw.text((540, 270), f"Flag Host Count: 1500", fill="black", font=text_font, anchor="mm")
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
