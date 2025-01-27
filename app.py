import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, session,send_from_directory,abort
from flask_socketio import SocketIO, emit
from textblob import TextBlob
from threading import Lock
from reportlab.pdfgen import canvas
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, jsonify, request, send_file, make_response
import json
import pygame
import threading
import time
import os
import sys
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) # Required for session handling
socketio = SocketIO(app)  # Initialize Flask-SocketIO

lock = Lock()

# Global list to store messages
messages = []

# Define the maximum size of the messages list
MAX_MESSAGES = 100


HOME_DIR = os.environ.get('HOME_DIR') # After setting Env. variable restart the computer
FILE_PATH = rf"{HOME_DIR}/flag_count.json"
certificate_path = rf"{HOME_DIR}/certificate.png"
SONG_FOLDER = 'static/'

def read_flag_count():
    """Reads flag count from JSON file."""
    try:
        with lock:
            with open(FILE_PATH, 'r') as file:
                return json.load(file)
    except Exception as e:
        app.logger.error(f"Error reading file: {e}")
        return {}

data = read_flag_count()
india_flag_count = data.get("india", 0)

def update_flag_count(country):
    """Updates flag count in JSON file."""
    try:
        # Read the flag count data from the file
        data = read_flag_count()
        
        # Check if the country exists in the data, otherwise set it to 0
        if country not in data:
            data[country] = 0
        
        # Increment the flag count for the given country
        data[country] += 1
        
        # Write the updated data back to the JSON file
        with lock:
            with open(FILE_PATH, 'w') as file:
                json.dump(data, file, indent=4)
        
        # Return the updated data
        return data
    
    except:
        app.logger.error(f"File not found: {FILE_PATH}")
        return {"error": "File not found."}


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

@app.route('/raise_flag', methods=['POST'])
def raise_flag():
    """API endpoint to raise a flag."""
    try:
        # Get the country from the request JSON
        country = request.json.get('country')

        # Validate if 'country' is provided in the request body
        if not country:
            return jsonify({"error": "Country is required!"}), 400
        
        # Update the flag count by calling the function
        updated_data = update_flag_count(country)

        # Emit the updated flag count to all clients via WebSocket
        socketio.emit('update_score', updated_data)

        # Return a success response with the updated count
        return jsonify({
            "message": f"{country.capitalize()} flag raised!", 
            "count": updated_data[country]
        })
    
    except KeyError as e:
        # Handle any KeyError and log it
        app.logger.error(f"KeyError: {e}")
        return jsonify({"error": f"Key error: {e}"}), 500
    
    except Exception as e:
        # Catch any other unexpected exceptions
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500



@app.route('/music/<filename>')
def play_music(filename):
    song_path = os.path.join(SONG_FOLDER, filename)
    if os.path.exists(song_path):
        return send_from_directory(SONG_FOLDER, filename)
    else:
        return abort(404)  # If the file is not found, return a 404 error

@app.route('/download_certificate', methods=['POST'])
def download_certificate_png():
    """Endpoint to generate and download the certificate as PNG."""
    # Get the user's name from the request body
    data = request.get_json()
    user_name = data.get('user_name', None)
    # certificate_path = "certificate.png"  # Path to your existing certificate template image

    # Validate input
    if not user_name:
        return jsonify({"error": "Name is required"}), 400

    # Check if the certificate template exists
    if not os.path.exists(certificate_path):
        return jsonify({"error": "Certificate template not found."}), 404

    # Open the existing certificate image
    img = Image.open(certificate_path)
    draw = ImageDraw.Draw(img)

    # Load font (adjust the path to the font file as needed)
    try:
        text_font = ImageFont.truetype("DejaVuSans.ttf", 90)
    except IOError:
        # Fallback to default font if specified font is not available
        print(IOError)
        text_font = ImageFont.load_default()

    # Calculate text position for the user's name (you can adjust the y position)
    text = f"{user_name}"
    
    # Using textbbox to calculate text dimensions
    bbox = draw.textbbox((0, 0), text, font=text_font)
    text_width = bbox[2] - bbox[0]  # Width of the text
    text_height = bbox[3] - bbox[1]  # Height of the text
    
    # Calculate the x position (center the text horizontally)
    x_pos = (img.width - text_width) // 2
    # Adjust the vertical position
    # y_pos = (img.height - text_height) // 2  # Center vertically
    y_pos = 1100  # You can adjust this value as needed

    # Add the user's name to the image
    draw.text((x_pos, y_pos), text, fill="black", font=text_font)

    # Save the modified image
    img.save("modified_certificate.png")

    # Serve the newly modified image
    return send_file("modified_certificate.png", as_attachment=True, download_name="certificate.png", mimetype="image/png")

@app.route("/about")
def about():
    return render_template("about.html")


@socketio.on('connect')
def handle_connect():
    """Send current flag count to the new connected client."""
    data = read_flag_count()
    emit('update_score', data)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, debug=True, allow_unsafe_werkzeug=True)
