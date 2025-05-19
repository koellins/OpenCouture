import cv2
import mediapipe as mp
import socket
import json

# **UDP Setup**
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# **MediaPipe Setup**
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# **Webcam-Start**
cap = cv2.VideoCapture(0)

print("🎥 Webcam gestartet... Tracking läuft!")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ Kein Bild von der Kamera erhalten.")
        break

    # **Bild spiegeln (optional)**
    frame = cv2.flip(frame, 1)

    # **Pose-Tracking**
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    # **Tracking-Daten sammeln**
    if results.pose_landmarks:
        tracking_data = {}
        for i, landmark in enumerate(results.pose_landmarks.landmark):
            tracking_data[f"point_{i}"] = [landmark.x, landmark.y, landmark.z]

        json_data = json.dumps(tracking_data)
        sock.sendto(f"JSON{json_data}".encode(), (UDP_IP, UDP_PORT))

    # **Zeichne Pose auf das Bild (zur Kontrolle)**
    mp.solutions.drawing_utils.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # **Zeige das Bild**
    cv2.imshow('Tracking', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
