from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import threading
import cv2
from deepface import DeepFace
import requests
import asyncio
import openai
import pyttsx3
import speech_recognition as sr
import time
from playsound import playsound
from gtts import gTTS
import whisper
from EdgeGPT import Chatbot, ConversationStyle
import json
import eventlet
eventlet.monkey_patch()

# Initialize OpenAI API
openai.api_key = "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"
# Initialize the text to speech engine 
app = Flask(__name__, template_folder='.')
socketio = SocketIO(app, async_mode='eventlet')
recognizer = sr.Recognizer()
engine = pyttsx3.init()

GPT_WAKE_WORD = "go"

def get_wake_word(phrase):
    if GPT_WAKE_WORD in phrase.lower():
        return GPT_WAKE_WORD
    else:
        return None

def speak_text(text):
    engine.say(text)
    engine.runAndWait()

cap = cv2.VideoCapture(0)
capture_camera = False

async def get_openai_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input},
        ],
        temperature=0.5,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        n=1,
        stop=["\nUser:"],
    )
    bot_response = response["choices"][0]["message"]["content"]
    return bot_response
    
async def main():
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print(f"Say 'Go' to wake me up")
            eventlet.spawn(socketio.emit, 'Q_Text', {'text': 'Say "Go" to wake me up'}, namespace='/login')
            speak_text("Say go to wake me up")
            while True:
                audio = recognizer.listen(source)
                try:
                    with open("audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    # Use the preloaded tiny_model
                    model = whisper.load_model("base")
                    result = model.transcribe("audio.wav")
                    phrase = result["text"]
                    print(f"You said: {phrase}")

                    wake_word = get_wake_word(phrase)
                    if wake_word is not None:
                        break
                    else:
                        print("Not a wake word. Try again.")
                        speak_text("Not a wake word, Try again")
                        eventlet.spawn(socketio.emit, 'Q_Text', {'text': 'Not a wake word. Try again.'}, namespace='/login')
                except Exception as e:
                    print("Error transcribing audio: {0}".format(e))
                    continue

            print("Speak a prompt...")
            print("What can I help you with?")
            eventlet.spawn(socketio.emit, 'Q_Text', {'text': 'What can I help you with?'}, namespace='/login')
            speak_text("What can I help you with?")
            audio = recognizer.listen(source)

            try:
                with open("audio_prompt.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                model = whisper.load_model("base")
                result = model.transcribe("audio_prompt.wav")
                user_input = result["text"]
                print(f"You said: {user_input}")
                eventlet.spawn(socketio.emit, 'My_text', {'text': user_input}, namespace='/login')
            except Exception as e:
                print("Error transcribing audio: {0}".format(e))

            if wake_word == GPT_WAKE_WORD:
                # Send prompt to GPT-3.5-turbo API
                print("almost there")
                bot_response = await get_openai_response(user_input)

            print(f"Bot: {bot_response}")
            await eventlet.spawn(socketio.emit, 'Q_Text', {'text': bot_response}, namespace='/login')
            speak_text(bot_response)
            await eventlet.spawn(socketio.emit, 'AcButton', {'result': True}, namespace='/login')

# Route to start the camera
@app.route('/start_camera')
def start_camera():
    global capture_camera
    capture_camera = True
    return 'Camera started.'

@app.route('/start_voice', methods=['POST'])
def start_voice():
    asyncio.run(main())
    return "Voice started!"

def generate_frames():
    global counter
    global face_match

    counter = 0
    face_match = False

    # Load the image during initialization
    image = cv2.imread("./avatar.jpg")

    # Preload the face recognition model weights
    DeepFace.verify(image, image)

    def face_check(frame):
        global face_match
        try:
            if DeepFace.verify(frame, image.copy())['verified']:
                face_match = True
            else:
                face_match = False
        except ValueError:
            face_match = False

    global capture_camera
    #Detect the face until the face is recognized
    while True:
        if capture_camera:
            ret, frame = cap.read()

            if not ret:
                break
            else:
                if counter % 30 == 0:
                    try:
                        threading.Thread(target=face_check, args=(frame.copy(),)).start()
                    except ValueError:
                        pass
                counter += 1

                #If face is matched, display the message and send request to node.js server
                if face_match:
                    cv2.putText(frame, "Recognized!", (20, 450), cv2.FONT_HERSHEY_COMPLEX, 2, (102, 255, 102), 3)

                    print("Login successful!")
                    eventlet.spawn(socketio.emit, 'face_recognized', {'result': True}, namespace='/login')
                    break
                else:
                    cv2.putText(frame, "Unrecognized!", (20, 450), cv2.FONT_HERSHEY_COMPLEX, 2, (102, 102, 255), 3)

            # Perform face recognition on the frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            #Perform appropriate conversion for image frames for video feed
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            print("Login request failed!")


# SocketIO event handler
@socketio.on('face_recognized', namespace='/login')
async def handle_face_recognized(data):
     face_recognized = data['result']

@socketio.on('Q_Text', namespace='/login')
async def handle_QText(data):
    voice_text = data['text']

@socketio.on('AcButton', namespace='/login')
async def handle_AcBtn(data):
    voice_text = data['result']

@socketio.on('My_text', namespace='/login')
async def handle_My_event(data):
    voice_text = data['text']

#Route for Login.html page
@app.route('/')
def index():
    return render_template('Login.html')

#Route for the video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
