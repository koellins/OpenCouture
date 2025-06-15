<img width="583" alt="oclogo_white" src="https://github.com/user-attachments/assets/6cceb923-3bfe-41ec-888a-9eff8796837a" />

# OpenCouture

**OpenCouture** is an open-source Augmented Reality (AR) tool built with Unreal Engine, aiming to revolutionize digital fashion design and visualization. By integrating procedural garment creation, real-time simulation, and AR capabilities, OpenCouture provides a platform for designers and technologists to explore the future of fashion.

## Project Overview

OpenCouture facilitates:

- **Procedural Garment Design**: Utilized in Blender. Ready to be modified.
- **Real-Time Simulation**: Leverage Unreal Engine's physics for dynamic garment behavior.
- **AR Integration**: Experience designs in augmented reality environments.
- **Modular Architecture**: Combine Python scripts, Blender assets, and Unreal Engine projects seamlessly.
- **Open Source Architecture**: Built from modular components – including Python scripts, avatar templates, and cloth simulation setups.

## Philosophy

OpenCouture is rooted in the belief that fashion can be reimagined as a cultural practice, not merely a commodity. It invites creators to rethink authorship, identity, and the role of materiality in dress. The project emphasizes:

- **Transparency**: Open-source approach encourages sharing and collaboration.
- **Accessibility**: Tools and assets are freely available for experimentation.
- **Experimentation**: Encourages pushing the boundaries of traditional fashion through technology.

## Application & Orientation

OpenCouture is designed for:

- **Digital Fashion Designers**: Craft and visualize garments in a virtual space.
- **AR Developers**: Integrate fashion elements into augmented reality applications.
- **Researchers & Educators**: Explore the intersection of fashion, technology, and culture.
- **Artists & Creatives**: Experiment with new forms of expression in digital fashion.

## Developers

- **Philipp Köll** www.philkoell.com
- **Markus Ahrendt**
  
---

## 🔧 Requirements

This project captures real-time human pose and segmentation mask data using a webcam and streams it via UDP to Unreal Engine 5.5.
Tested on Windows 11


### Software

- **Python 3.11**
- **Unreal Engine 5.5.0**

### Python Libraries

- `opencv-python`  # install with: `pip install opencv-python`
- `mediapipe`    # install with: `pip install mediapipe`
- `numpy`       # install with: `pip install numpy`

### Ports

Ensure these UDP ports match your setup in Unreal:

- `UDP_PORT_TRACKING = 5011`  – for pose landmark data
- `UDP_PORT_WEBCAM = 5012`    – for webcam image stream
- `UDP_PORT_MASK = 5013`      – for segmentation mask

---

## 🗂️ Code Overview

The script performs the following:
- Captures webcam video frames
- Uses MediaPipe to estimate human pose and segmentation masks
- Streams data asynchronously via UDP in separate threads
- Sends JSON-formatted pose data and JPEG-encoded images
- Dynamically adjusts webcam resolution if 1080p is not available

---

## ⚠️ Notes

- Run Python code before opening Unreal Engine
- Make sure, webcam is connected
- Webcam resolution targets 1920×1080; falls back to 1280×720 if unsupported.
- Pose data includes both 2D image coordinates and 3D world coordinates.
- The UDP image transmission uses chunking for large packets (max 60,000 bytes).


