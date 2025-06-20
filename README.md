# DermaSoul – Smart Skin Analysis Tool 

DermaSoul is an AI-powered skin analysis tool designed to help users detect common skin conditions like **acne**, **oiliness**, and **UV sensitivity** using image processing and machine learning techniques. This application aims to assist individuals, dermatologists, and skincare enthusiasts in analyzing skin health more efficiently and accurately.

---

## Features

- Real-time skin image input via webcam or uploaded photo
- Detects:  
   Acne  
   Skin Type 
   Skin Tone
- Visual feedback and suggestions based on the analysis

---

##  Technologies Used

- Python, TensorFlow, Keras
- OpenCV for image processing
- Streamlit for frontend/web interface
- Matplotlib, NumPy, Pandas, Scikit-learn

---

##  Installation

Install the required libraries:
pip install tensorflow keras numpy pandas scikit-learn matplotlib opencv-python streamlit

---
## How to USE
1.Clone the repository
git clone https://github.com/smiling621/DermaSoul.git
cd DermaSoul

2.Activate Virtual Environment
python3 -m venv venv
source venv/bin/activate

3.Install Dependencies 
pip install -r requirements.txt

4.Run the app
streamlit run app.py

---
## Model Architecture
The AI model is based on Convolutional Neural Networks (CNNs) consisting of:
Multiple convolutional and max-pooling layers

Dropout layers for regularization

Fully connected dense layers

Trained using Adam optimizer and binary cross-entropy loss

---
## Dataset:
The model was trained on a dataset of labeled skin images, organized into folders:

/train – for model training
/valid – for validation
/test – for performance evaluation

 Dataset includes images for acne, skin type, and skin tone
 Due to file size limitations, dataset is not included in this repo
---
## Results:
Results achieved ~60% accuracy on the test set (baseline model).Performance depends on the image quality and lighting conditions
---
Contact
For questions or collaboration:
📧 kusum072815@gmail.com
🔗 GitHub: smiling621




