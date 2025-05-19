import cv2
import socket
import struct

# Ziel-IP und Port für Unreal
UDP_IP = "127.0.0.1"  # Unreal Engine PC
UDP_PORT = 5006        # Muss in Unreal übereinstimmen

# Starte die Webcam
cap = cv2.VideoCapture(0)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("❌ Kein Bild erhalten!")
        break

    # Bild komprimieren
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    
    # Länge des Buffers senden
    size = len(buffer)
    sock.sendto(struct.pack(">I", size), (UDP_IP, UDP_PORT))
    
    # Bilddaten senden
    sock.sendto(buffer, (UDP_IP, UDP_PORT))

    # Vorschau anzeigen
    cv2.imshow("Webcam", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()
