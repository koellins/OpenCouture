import cv2
import mediapipe as mp
import socket
import json
import threading
import pyvirtualcam

# **VirtualCamera1 Index**
CAMINDEX = 2

# **TCP Server Setup**
TCP_IP = "127.0.0.1"
TCP_PORT = 5005
BUFFER_SIZE = 1024

# **MediaPipe Setup**
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# **Webcam-Start**
cap = cv2.VideoCapture(CAMINDEX)

# **Startet den TCP-Server**
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((TCP_IP, TCP_PORT))
    server.listen(1)
    print(f"🟢 Warten auf Verbindung auf {TCP_IP}:{TCP_PORT}...")

    conn, addr = server.accept()
    print(f"✅ Verbindung von {addr} hergestellt!")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=20) as cam:
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

                    json_data = json.dumps(tracking_data) + "\n"  # JSON mit Trennzeichen
                    conn.sendall(json_data.encode())  # Daten senden
                
                # **Pose auf das Bild zeichnen (zur Kontrolle)**
                mp.solutions.drawing_utils.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # **Zeige das Bild**
                cv2.imshow('Tracking', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except (ConnectionResetError, BrokenPipeError):
        print("❌ Verbindung unterbrochen. Warte auf neuen Client...")
        conn.close()
        start_server()  # Server neu starten für neuen Client

    finally:
        cap.release()
        conn.close()
        server.close()
        cv2.destroyAllWindows()
        print("✅ Verbindung geschlossen.")

# **Server als separaten Thread starten**
server_thread = threading.Thread(target=start_server)
server_thread.start()
