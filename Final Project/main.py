from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import threading
import cv2
from deepface import DeepFace
import requests
import webbrowser
import openai
import pyttsx3
import speech_recognition as sr
import time
from playsound import playsound
from gtts import gTTS

# Initialize OpenAI API
openai.api_key = "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"
# Initialize the text to speech engine 
engine=pyttsx3.init()
app = Flask(__name__, template_folder='.')
socketio = SocketIO(app)

def transcribe_audio_to_text(filename):
    recogizer = sr.Recognizer()
    with sr.AudioFile(filename)as source:
        audio=recogizer.record(source) 
    try:
        return recogizer.recognize_google(audio)
    except:
        print("skipping unkown error")

def generate_response(prompt):
    response= openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=4000,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response ["choices"][0]["text"]

def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# def main():
#     while True:
#         #Waith for user say "genius"
#         print("Say 'Over' to start recording your question")
#         with sr.Microphone() as source:
#             recognizer = sr.Recognizer()
#             audio=recognizer.listen(source)
#             try:
#                 transcription = recognizer.recognize_google(audio)
#                 if transcription.lower()=="over":
#                     #record audio
#                     filename ="input.wav"
#                     print("Say your question")
#                     with sr.Microphone() as source:
#                         recognizer=sr.Recognizer()
#                         source.pause_threshold=1
#                         audio=recognizer.listen(source,phrase_time_limit=None,timeout=None)
#                         with open(filename,"wb")as f:
#                             f.write(audio.get_wav_data())
                
#                     #transcript audio to test 
#                     text=transcribe_audio_to_text(filename)
#                     if text:
#                         print(f"you said {text}")  
#                         socketio.emit('voice_text', {'text': text}, namespace='/login')               
#                         #Generate the response
#                         response = generate_response(text)
#                         print(f"chat gpt 3 say {response}")
#                         socketio.emit('bot_response', {'response': response}, namespace='/login')
#                         tts = gTTS(text=response, lang='en')
#                         tts.save("sample.mp3")
#                         #read resopnse using GPT3
#                         speak_text(response)
#             except Exception as e:               
#                 print("An error ocurred : {}".format(e))

cap = cv2.VideoCapture(0)
capture_camera = False

# Route to start the camera
@app.route('/start_camera')
def start_camera():
    global capture_camera
    capture_camera = True
    return 'Camera started.'

# Define the voice_thread as a global variable
voice_thread = None

def voice_thread_function():
    #Waith for user say "Over"
    print("Say 'Over' to start recording your question")
    #socketio.start_background_task(socketio.emit, 'Q_Text', {'text': "Say Over to start recording your question"}, namespace='/login')
    speak_text("Say Over to start recording your question")
    with sr.Microphone() as source:
        recognizer = sr.Recognizer()
        audio=recognizer.listen(source)
        try:
            transcription = recognizer.recognize_google(audio)
            if transcription.lower()=="over":
                #record audio
                filename ="input.wav"
                print("Say your question")
                #socketio.start_background_task(socketio.emit, 'Q_Text', {'text': "Say your question"}, namespace='/login')
                speak_text("Say your question")
                with sr.Microphone() as source:
                    recognizer=sr.Recognizer()
                    source.pause_threshold=1
                    audio=recognizer.listen(source,phrase_time_limit=None,timeout=None)
                    with open(filename,"wb")as f:
                        f.write(audio.get_wav_data())
                
                #transcript audio to test 
                text=transcribe_audio_to_text(filename)
                if text:
                    print(f"you said {text}")               
                    #Generate the response
                    response = generate_response(text)
                    print(f"chat gpt 3 say {response}")
                    socketio.start_background_task(socketio.emit, 'voice_text', {'text': text, 'response': response}, namespace='/login')
                    tts = gTTS(text=response, lang='en')
                    tts.save("sample.mp3")
                    #read resopnse using GPT3
                    speak_text(response)
        except Exception as e:               
            print("An error ocurred : {}".format(e))
            #socketio.start_background_task(socketio.emit, 'Q_Text', {'text': "An error occurred: {}".format(e)}, namespace='/login')
            speak_text("An error ocurred : {}".format(e))

@app.route('/start_voice', methods=['GET'])
def start_voice():
    global voice_thread
    if voice_thread is None or not voice_thread.is_alive():
        # Only start a new voice_thread if it does not exist or has completed
        voice_thread = threading.Thread(target=voice_thread_function)
        voice_thread.start()
        return 'Voice recognition and chatbot logic started.'
    else:
        return 'Voice recognition and chatbot logic already running.'

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

                    # Make login request to Node.js server with recognized face information as query parameters
                    response = requests.get('http://localhost:4000/Home.html')

                    # Check response from server
                    if response.status_code == 200:
                        print("Login successful!")
                        username = "Loc Pham"
                        # Do something with the logged-in status, e.g., open a web page
                        # webbrowser.open(f'http://localhost:4000/Home.html?username={username}')

                        # Emit face recognition result to client using Flask-SocketIO
                        #socketio.emit('face_recognized', {'result': True}, namespace='/login')
                        socketio.start_background_task(socketio.emit, 'face_recognized', {'result': True}, namespace='/login')
                        break
                    else:
                        print("Login failed!")
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
def handle_face_recognized(data):
    face_recognized = data['result']

@socketio.on('Q_Text', namespace='/login')
def handle_QText(data):
    voice_text = data['text']

@socketio.on('voice_text', namespace='/login')
def handle_combined_event(data):
    voice_text = data['text']
    bot_response = data['response']

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
