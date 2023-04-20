from flask import Flask, render_template, Response
import threading
import cv2
from deepface import DeepFace
import requests
import webbrowser

app = Flask(__name__, template_folder='.')
cap = cv2.VideoCapture(0)

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

    #Detect the face until the face is recognized
    while True:
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
                    webbrowser.open(f'http://localhost:4000/Home.html?username={username}')  # Open home page in a web browser
                    return "<script>window.close();</script>"
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
