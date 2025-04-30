import cv2
import mediapipe as mp
import pyvirtualcam
import numpy as np

# MediaPipe Selfie Segmentation-Modell initialisieren
mp_selfie_segmentation = mp.solutions.selfie_segmentation
selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)

# Webcam initialisieren
cap = cv2.VideoCapture(2)       # edit this number to fit the virtual cam 1 (propably between 1&3)

# Variablen für den Hintergrund
background = None
use_webcam_background = True  # Setze dies auf False, um keinen Hintergrund zu verwenden

# Hole die Auflösung der Kamera
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

with pyvirtualcam.Camera(width=width, height=height, fps=20) as cam:
    print(f"Streaming auf virtuelle Kamera: {cam.device}")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Bild in RGB konvertieren (MediaPipe erwartet RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Segmentierung durchführen
        results = selfie_segmentation.process(rgb_frame)

        # Maske erstellen (Maskenwert ist 0 oder 1)
        mask = results.segmentation_mask > 0.5

        # Maske auf das Originalbild anwenden
        masked_frame = cv2.bitwise_and(frame, frame, mask=mask.astype('uint8'))

        # Hintergrund aus der Webcam nehmen
        if use_webcam_background:
            if background is None:
                # Speichere das erste Frame als Hintergrund
                background = frame.copy()
            else:
                # Verwende den gespeicherten Hintergrund
                background_resized = cv2.resize(background, (frame.shape[1], frame.shape[0]))
                background_masked = cv2.bitwise_and(background_resized, background_resized, mask=~mask.astype('uint8'))
                final_frame = cv2.add(masked_frame, background_masked)
        else:
            # Kein Hintergrund, zeige nur die freigestellte Person
            final_frame = masked_frame

        # Ergebnis anzeigen
        cv2.imshow('Freigestellte Person', masked_frame)

        cam.send(masked_frame)

        # Beenden mit der 'q'-Taste
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break
        elif key & 0xFF == ord('b'):
            # Speichere das aktuelle Frame als neuen Hintergrund
            background = frame.copy()
            print("Neuer Hintergrund gespeichert!")

# Ressourcen freigeben
cap.release()
cv2.destroyAllWindows()