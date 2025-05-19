import cv2
import mediapipe as mp
import numpy as np
import socket
import json
import threading
import pyvirtualcam

# **VirtualCamera1 Index**
CAMINDEX = 4

# **TCP Server Setup**
TCP_IP = "127.0.0.1"
TCP_PORT = 5005
BUFFER_SIZE = 1024

# # MediaPipe Selfie Segmentation-Modell initialisieren
# mp_selfie_segmentation = mp.solutions.selfie_segmentation
# selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)

# **MediaPipe Setup**
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, enable_segmentation = True)

# **Webcam-Start**
cap = cv2.VideoCapture(CAMINDEX)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# **Startet den TCP-Server**
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((TCP_IP, TCP_PORT))
    server.listen(1)
    print(f"🟢 Warten auf Verbindung auf {TCP_IP}:{TCP_PORT}...")

    conn, addr = server.accept()
    print(f"✅ Verbindung von {addr} hergestellt!")

    try:
        with pyvirtualcam.Camera(width=width, height=height, fps=20) as cam:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("❌ Kein Bild von der Kamera erhalten.")
                    break

                # **Bild spiegeln (optional)**
                # frame = cv2.flip(frame, 1)
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#mask
                # # Segmentierung durchführen
                # mask_result = selfie_segmentation.process(image_rgb)
                # # Maske erstellen (Maskenwert ist 0 oder 1)
                # mask = mask_result.segmentation_mask > 0.5
                # #maske auf webcam bild anwenden
                # masked_frame = cv2.bitwise_and(frame, frame, mask=mask.astype('uint8'))
#pose
                masked_frame = np.zeros((height, width, 3), dtype=np.uint8)
                # **Pose-Tracking**
                results = pose.process(image_rgb)
                if results.segmentation_mask is not None:
                    mask = cv2.cvtColor(results.segmentation_mask, cv2.COLOR_GRAY2RGB)
                    masked_frame = mask
                # **Tracking-Daten sammeln**
                if results.pose_landmarks:
                    tracking_data = {}
                    _s = 2
                    _e = 5
                    _z = 6
                    for i, landmark in enumerate(results.pose_landmarks.landmark):
                        tracking_data[f"{str(i).zfill(2)}"] = [str(landmark.x).ljust(6, '0')[_s:_e], str(landmark.y).ljust(6, '0')[_s:_e],str(landmark.z).ljust(6, '0')[:_z], str(landmark.visibility).ljust(6, '0')[_s:_e]]
                    json_data = json.dumps(tracking_data) + "\n"  # JSON mit Trennzeichen
                    conn.sendall(json_data.encode())  # Daten senden
                
                # **Pose auf das Bild zeichnen (zur Kontrolle)**
                # mp.solutions.drawing_utils.draw_landmarks(masked_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                    masked_frame = (masked_frame * 255).astype(np.uint8)
                    print(type(masked_frame))
                    cam.send(masked_frame)
                    cv2.imshow('FENSTER',masked_frame)

                # **Zeige das Bild**
                # cv2.imshow('Tracking', masked_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except (ConnectionResetError, BrokenPipeError):
        print("❌ Verbindung unterbrochen. Warte auf neuen Client...")
        conn.close()
        start_server()  # Server neu starten für neuen Client

    finally:
        print("❌ Verbindung unterbrochen. Warte auf neuen Client...")

        cap.release()
        conn.close()
        server.close()
        cv2.destroyAllWindows()
        print("✅ Verbindung geschlossen.")

# **Server als separaten Thread starten**
server_thread = threading.Thread(target=start_server)
server_thread.start()
