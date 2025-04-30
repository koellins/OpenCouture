import cv2
import socket
import struct
import json
import mediapipe as mp
import numpy as np

# Ziel-IP und Port für Unreal
UDP_IP = "127.0.0.1"  # Unreal Engine PC
UDP_PORT = 5006        # Muss in Unreal übereinstimmen

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, enable_segmentation = True)


# Starte die Webcam
cap = cv2.VideoCapture(0)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ Kein Bild erhalten!")
        break

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #pose
    masked_frame = np.zeros((height, width, 3), dtype=np.uint8)
    # **Pose-Tracking**
    results = pose.process(image_rgb)
    if results.segmentation_mask is not None:
        mask = results.segmentation_mask
        masked_frame = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
              

    # Bild komprimieren
    _, buffer = cv2.imencode('.jpg', masked_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # Länge des Buffers senden
    size = len(buffer)
    sock.sendto(struct.pack(">I", size), (UDP_IP, UDP_PORT))
    
    # Bilddaten senden
    sock.sendto(buffer, (UDP_IP, UDP_PORT))

    # Vorschau anzeigen
    cv2.imshow("Webcam", masked_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()
