import cv2
import socket
import struct
import json
import mediapipe as mp
import numpy as np

# Ziel-IP und Port für Unreal
UDP_IP = "127.0.0.1"  # Unreal Engine PC
UDP_PORT_TRACKING = 5011        # TrackingDataPort in Unreal übereinstimmen
UDP_PORT_WEBCAM = 5012        # WebcamPort in Unreal übereinstimmen
UDP_PORT_MASK = 5013        # MaskPort in Unreal übereinstimmen

sendID = 0; 

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5, enable_segmentation = True)


# Starte die Webcam
cap = cv2.VideoCapture(1)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print (width)
print ('^width')
print (height)
print ('^height')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ Kein Bild erhalten!")
        break

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #pose
    masked_frame = np.zeros((height, width), dtype=np.uint8)
    # **Pose-Tracking**
    results = pose.process(image_rgb)
    if results.pose_landmarks:
        tracking_data = {}
        tracking_dataWorldCoor = {}
        _s = 2
        _e = 5
        _z = 6
        for i, landmark in enumerate(results.pose_landmarks.landmark):
            _vis = str(landmark.visibility).ljust(6, '0')[_s:_e]
            if(landmark.x > 1 or landmark.x < 0 or landmark.y > 1 or landmark.y < 0):
                _vis = "0.0"
            tracking_data[f"{str(i).zfill(2)}"] = [str(landmark.x).ljust(6, '0')[_s:_e], str(landmark.y).ljust(6, '0')[_s:_e],str(landmark.z).ljust(6, '0')[:_z], _vis]
            # if(i == 17):
            #     print(f"vis: {landmark.visibility}  x: {landmark.x}  y: {landmark.y}")
        
        for i, landmarkW in enumerate(results.pose_world_landmarks.landmark):
            tracking_dataWorldCoor[f"{str(i)}"] = [str(landmarkW.x)[0:8], str(landmarkW.y)[0:8],str(landmarkW.z)[0:_z], str(landmarkW.visibility)[0:_e]]
#Send ImageCoordinates
        json_data = json.dumps(tracking_data) + "\n"  # JSON mit Trennzeichen
        json_buffer = json_data.encode('utf-8')
        size_json = len(json_buffer)
        sendID = 1 # trackingData
        sock.sendto(struct.pack(">BI", sendID, size_json), (UDP_IP, UDP_PORT_TRACKING))
        sock.sendto(json_buffer, (UDP_IP, UDP_PORT_TRACKING))
#Send World Coordinates
        json_dataW = json.dumps(tracking_dataWorldCoor) + "\n"  # JSON mit Trennzeichen
        json_bufferW = json_dataW.encode('utf-8')
        size_json = len(json_bufferW)
        sendID = 4 # trackingData
        sock.sendto(struct.pack(">BI", sendID, size_json), (UDP_IP, UDP_PORT_TRACKING))
        sock.sendto(json_bufferW, (UDP_IP, UDP_PORT_TRACKING))
    
    if results.segmentation_mask is not None:
        mask = results.segmentation_mask  # Float32 Werte von 0.0 - 1.0
        mask = (mask * 255).astype(np.uint8)  # Skaliert auf 0 - 255
        masked_frame = mask
    #   masked_frame = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)  # Graustufen in 3-Kanal-Bild umwandeln

    # Bild komprimieren
    _, buffer = cv2.imencode('.jpg', masked_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # Länge des Buffers senden
    size = len(buffer)
    sendID = 3 #mask = 3
    sock.sendto(struct.pack(">BI", sendID, size), (UDP_IP, UDP_PORT_MASK))
    # Bilddaten senden
    sock.sendto(buffer, (UDP_IP, UDP_PORT_MASK))

    #webcam
    _, bufferWeb = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    sizeWeb = len(bufferWeb)
    sendID = 2 # webcam stream
    sock.sendto(struct.pack(">BI", sendID, sizeWeb), (UDP_IP, UDP_PORT_WEBCAM))
    sock.sendto(bufferWeb, (UDP_IP, UDP_PORT_WEBCAM))
    

    # Vorschau anzeigen
    cv2.imshow("Webcam", masked_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()
