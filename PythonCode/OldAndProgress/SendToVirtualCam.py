import cv2
import pyvirtualcam
import numpy as np

# Öffne die Webcam oder ein Video
cap = cv2.VideoCapture(2)  # 0 für die erste Kamera

# Überprüfe, ob die Kamera geöffnet wurde
if not cap.isOpened():
    print("Fehler: Kamera konnte nicht geöffnet werden.")
    exit()

# Hole die Auflösung der Kamera
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Erstelle eine virtuelle Kamera mit pyvirtualcam
with pyvirtualcam.Camera(width=width, height=height, fps=20) as cam:
    print(f"Streaming auf virtuelle Kamera: {cam.device}")

    while True:
        # Lese ein Frame von der Kamera
        ret, frame = cap.read()
        if not ret:
            print("Fehler: Frame konnte nicht gelesen werden.")
            break

        # Konvertiere das Frame von BGR zu RGB (pyvirtualcam erwartet RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Sende das Frame an die virtuelle Kamera
        cam.send(frame_rgb)

        # Zeige das Frame in einem Fenster an (optional)
        cv2.imshow('Webcam', frame)

        # Warte auf eine Tasteneingabe (1 ms) und beende die Schleife, wenn 'q' gedrückt wird
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Schließe die Kamera und alle Fenster
cap.release()
cv2.destroyAllWindows()