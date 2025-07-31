import cv2
import numpy as np
from keras.models import load_model
from keras.applications.mobilenet_v2 import preprocess_input
import os

# Load models
try:
    skin_model = load_model(os.path.join('model', 'my_skin_model.h5'))
    acne_model = load_model(os.path.join('model', 'my_acne_model.h5'))
    print("Models loaded successfully")
except Exception as e:
    print(f"Error loading models: {e}")
    skin_model = None
    acne_model = None

# Face detector (more permissive)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Class labels
skin_classes = ['dry', 'normal', 'oil']
acne_classes = ['no_acne', 'mild', 'moderate', 'severe', 'very_severe']

def is_likely_skin_image(image_region):
    try:
        hsv = cv2.cvtColor(image_region, cv2.COLOR_RGB2HSV)
        # Broader skin tone range
        lower_skin = np.array([0, 10, 60], dtype=np.uint8)
        upper_skin = np.array([40, 255, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_pixels = np.sum(skin_mask > 0)
        total_pixels = skin_mask.shape[0] * skin_mask.shape[1]
        skin_percentage = skin_pixels / total_pixels
        return skin_percentage > 0.08  # lowered threshold
    except Exception:
        return False


def ai_predict(image_path):
    try:
        if skin_model is None or acne_model is None:
            return {"error": "Models not loaded properly"}

        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Could not read image file"}

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use more flexible settings for face detection
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(30, 30)
        )
        face_detected = len(faces) > 0

        if face_detected:
            # Use largest detected face
            areas = [w * h for (x, y, w, h) in faces]
            x, y, w, h = faces[np.argmax(areas)]
            pad = int(0.2 * min(w, h))
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(image.shape[1], x + w + pad)
            y2 = min(image.shape[0], y + h + pad)
            region = image_rgb[y1:y2, x1:x2]
        else:
            # Use center crop and run skin check
            h, w, _ = image.shape
            if h < 100 or w < 100:
                return {"error": "Image too small for analysis"}
            ch, cw = int(h * 0.6), int(w * 0.6)
            sh, sw = (h - ch) // 2, (w - cw) // 2
            region = image_rgb[sh:sh+ch, sw:sw+cw]
            if not is_likely_skin_image(region):
                return {
                    "error": None,
                    "skin_type": "unknown",
                    "skin_confidence": 0.0,
                    "acne_type": "unknown",
                    "acne_confidence": 0.0,
                    "face_detected": False,
                    "message": "No face or valid skin detected. Please upload a clear image of your facial skin."
                }

        # Resize and preprocess for model
        region_resized = cv2.resize(region, (224, 224))
        region_normalized = region_resized.astype(np.float32) / 255.0
        region_preprocessed = preprocess_input(region_normalized * 255.0)
        region_expanded = np.expand_dims(region_preprocessed, axis=0)

        # Make predictions
        skin_preds = skin_model.predict(region_expanded, verbose=0)[0]
        acne_preds = acne_model.predict(region_expanded, verbose=0)[0]

        skin_conf = float(np.max(skin_preds))
        acne_conf = float(np.max(acne_preds))
        skin_type = skin_classes[np.argmax(skin_preds)]
        acne_type = acne_classes[np.argmax(acne_preds)]

        # Confidence thresholds
        if skin_conf < 0.3:
            skin_type = "uncertain"
        if acne_conf < 0.3 or (not face_detected and acne_conf < 0.6):
            acne_type = "no_acne"

        return {
            "error": None,
            "skin_type": skin_type,
            "skin_confidence": skin_conf,
            "acne_type": acne_type,
            "acne_confidence": acne_conf,
            "face_detected": face_detected
        }

    except Exception as e:
        return {"error": f"Unexpected error during prediction: {str(e)}"}

# Optional: test function
def test_prediction(image_path):
    result = ai_predict(image_path)
    for key, value in result.items():
        print(f"{key}: {value}")
