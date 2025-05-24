import cv2
import socket
import struct
import json
import mediapipe as mp
import numpy as np
import time
import threading
import queue

# Ziel-IP und Port für Unreal
UDP_IP = "127.0.0.1"  # Unreal Engine PC
UDP_PORT_TRACKING = 5011        # TrackingDataPort in Unreal übereinstimmen
UDP_PORT_WEBCAM = 5012        # WebcamPort in Unreal übereinstimmen
UDP_PORT_MASK = 5013        # MaskPort in Unreal übereinstimmen
MAX_PACKET_SIZE = 60000

sendID = 0; 

global latest_frame_for_pose    # last frame safe for processing
latest_frame_for_pose = None
result_queue = queue.Queue(maxsize = 2)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5, enable_segmentation = True)


# Starte die Webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
if(not int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))==1920):
    print('no 1080p cam!')
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
if(not int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))==1280):
    print('no 720p cam!')
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print (width)
print ('^width')
print (height)
print ('^height')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def pose_worker():
    with mp_pose.Pose(model_complexity=1,min_detection_confidence=0.5,min_tracking_confidence=0.5,enable_segmentation=True) as pose:
        while True:
            if latest_frame_for_pose is None:
                time.sleep(.001)
                continue
            frame_copy = latest_frame_for_pose.copy()
            image_rgb = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
            result = pose.process(image_rgb)
            result_queue.put((result, frame))      # do processing in other thread
            time.sleep(.0001)

def send_image_async(image, send_id, udp_port): # Send image in other thread to not block program
    threading.Thread(
        target=send_image_in_chunks,
        args=(image, send_id, udp_port),
        daemon=True  # Thread wird beendet, wenn das Programm stoppt
    ).start()

def send_image_in_chunks(image, send_id, udp_port):
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    data = buffer.tobytes()

    image_id = np.random.randint(0, 2**31 - 1, dtype=np.int32)  # uint32
    num_packets = (len(data) + MAX_PACKET_SIZE - 1) // MAX_PACKET_SIZE

    for i in range(num_packets):
        start = i * MAX_PACKET_SIZE
        end = min(start + MAX_PACKET_SIZE, len(data))
        chunk = data[start:end]
        payload_size = len(chunk)

        # Header: [ID (1) | Index (2) | Total (2) | PayloadSize (2)]
        header = struct.pack("<IHHH", image_id, i, num_packets, payload_size)
        sock.sendto(header + chunk, (UDP_IP, udp_port))

def log_time(label, start_time):
    elapsed = (time.time() - start_time) * 1000  # ms
    # print(f"[⏱️ {label}] {elapsed:.2f} ms")

#start pose estimation thread
pose_thread = threading.Thread(target=pose_worker, daemon=True)
pose_thread.start()

while cap.isOpened():
    total_start = time.time()
    step_start = time.time()
    ret, frame = cap.read()

    latest_frame_for_pose = frame
    log_time("Frame read", step_start)

    results = None
    if not ret:
        print("❌ Kein Bild erhalten!")
        break

    step_start = time.time()
    send_image_async(frame,2,UDP_PORT_WEBCAM)
    log_time("SendWebcam", step_start)

    if not result_queue.empty():
        results, frame_with_pose = result_queue.get_nowait()
    
    #pose
    masked_frame = np.zeros((height,width), dtype=np.uint8)

    if results is not None and results.pose_landmarks:
        tracking_data = {}
        tracking_dataWorldCoor = {}
        _s = 2
        _e = 5
        _z = 6
        for i, landmark in enumerate(results.pose_landmarks.landmark):
            _vis = str(landmark.visibility).ljust(6, '0')[_s:_e]
            if(landmark.x >= 1 or landmark.x <= 0 or landmark.y >= 1 or landmark.y <= 0):
                _vis = "0.0"
            tracking_data[f"{str(i).zfill(2)}"] = [str(landmark.x).ljust(6, '0')[_s:_e], str(landmark.y).ljust(6, '0')[_s:_e],str(landmark.z).ljust(6, '0')[:_z], _vis]
            # if(i == 17):
            #     print(f"vis: {landmark.visibility}  x: {landmark.x}  y: {landmark.y}")
            # if (i == 0):
            #    print( _vis)
        
        for i, landmarkW in enumerate(results.pose_world_landmarks.landmark):
            tracking_dataWorldCoor[f"{str(i)}"] = [str(landmarkW.x)[0:8], str(landmarkW.y)[0:8],str(landmarkW.z)[0:_z], str(landmarkW.visibility)[0:_e]]
            # if(i == 0):
            #     print( str(landmarkW.visibility)[0:_e])
#Send ImageCoordinates  combined!
        combined_tracking_data = {"tracking":tracking_data, "world":tracking_dataWorldCoor}
        json_dataC = json.dumps(combined_tracking_data) + "\n"  # JSON mit Trennzeichen
        json_bufferC = json_dataC.encode('utf-8')
        size_jsonC = len(json_bufferC)
        sendID = 1 # trackingData
        sock.sendto(struct.pack(">BI", sendID, size_jsonC), (UDP_IP, UDP_PORT_TRACKING))
        sock.sendto(json_bufferC, (UDP_IP, UDP_PORT_TRACKING))

    log_time("Build and sent tracking_data", step_start)
    if results is not None and results.segmentation_mask is not None:
        mask = results.segmentation_mask  # Float32 Werte von 0.0 - 1.0
        mask = (mask * 255).astype(np.uint8)  # Skaliert auf 0 - 255
        masked_frame = mask

    if results is None:
        print("No result!")

    step_start = time.time()
    send_image_async(masked_frame, 3, UDP_PORT_MASK)
    log_time("Send Mask", step_start)

    step_start = time.time()
    # send_image_async(frame, 2, UDP_PORT_WEBCAM)
    log_time("Send Webcam", step_start)

    # Vorschau anzeigen
    step_start = time.time()
    cv2.imshow("Webcam", frame)
    log_time("Display Mask", step_start)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()
