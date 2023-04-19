import threading
import cv2
from deepface import DeepFace

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

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

while True:
    ret, frame = cap.read()

    if ret:
        if counter % 30 == 0:
            try:
                threading.Thread(target=face_check, args=(frame.copy(),)).start()
            except ValueError:
                pass
        counter += 1

        if face_match:
            cv2.putText(frame, "Recognized!", (20, 450), cv2.FONT_HERSHEY_COMPLEX, 2, (102, 255, 102), 3)
        else:
            cv2.putText(frame, "Unrecognized!", (20, 450), cv2.FONT_HERSHEY_COMPLEX, 2, (102, 102, 255), 3)

        cv2.imshow("video", frame)

    key = cv2.waitKey(1)
    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
