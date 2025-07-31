from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import sqlite3
from predict import ai_predict

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# --- Database setup ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            salon_name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user' in session:
        return render_template('index.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        salon_name = request.form['salonName']

        if not all([username, email, password, salon_name]):
            flash('All fields are required.', 'error')
            return render_template('register.html')

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, email, password, salon_name) VALUES (?, ?, ?, ?)", 
                     (username, email, password, salon_name))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
            conn.close()
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('login.html')

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user'] = user[0]  # Store username in session
            session['email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/analyzer', methods=['GET', 'POST'])
def analyzer():
    if 'user' not in session:
        flash('Please login to access the analyzer.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Check if image was uploaded
        if 'image' not in request.files:
            flash('No image uploaded.', 'error')
            return render_template('analyzer.html')

        image = request.files['image']
        customer_name = request.form.get('customerName', '').strip()

        if not customer_name:
            flash('Please enter your name.', 'error')
            return render_template('analyzer.html')

        if image.filename == '':
            flash('No image selected.', 'error')
            return render_template('analyzer.html')
        
        session.pop('quiz_responses', None)
        # Save uploaded image
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        try:
            prediction_result = ai_predict(filepath)

            # Check for error or message from prediction
            if prediction_result.get("error") or prediction_result.get("message"):
                error_msg = prediction_result.get("error") or prediction_result.get("message")
                flash(f'Error processing image: {error_msg}', 'error')

                # Clean session to avoid old results being shown
                session.pop('skin_type', None)
                session.pop('acne', None)
                session.pop('skin_confidence', None)
                session.pop('acne_confidence', None)
                session.pop('face_detected', None)
                session.pop('quiz_responses', None)
                if os.path.exists(filepath):
                    os.remove(filepath)
                return render_template('analyzer.html')

            # Store prediction results in session
            session['customer_name'] = customer_name
            session['skin_type'] = prediction_result['skin_type']
            session['acne'] = prediction_result['acne_type']
            session['face_detected'] = prediction_result['face_detected']
            session['skin_confidence'] = prediction_result['skin_confidence']
            session['acne_confidence'] = prediction_result['acne_confidence']

            if os.path.exists(filepath):
                os.remove(filepath)

            return redirect(url_for('result'))

        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'error')

            session.pop('skin_type', None)
            session.pop('acne', None)
            session.pop('skin_confidence', None)
            session.pop('acne_confidence', None)
            session.pop('face_detected', None)

            if os.path.exists(filepath):
                os.remove(filepath)

            return render_template('analyzer.html')

    return render_template('analyzer.html')

@app.route('/result')
def result():
    if 'user' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    if 'skin_type' not in session or 'acne' not in session:
        flash('Please analyze your skin first.', 'error')
        return redirect(url_for('analyzer'))

    return render_template('result.html',
                           customer_name=session.get('customer_name', 'User'),
                           skin_type=session['skin_type'],
                           acne=session['acne'],
                           face_detected='yes' if session.get('face_detected', False) else 'no',
                           skin_confidence=session.get('skin_confidence', 0),
                           acne_confidence=session.get('acne_confidence', 0))



@app.route('/suggestions')
def suggestions():
    if 'user' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    if 'skin_type' not in session or 'acne' not in session:
        flash('Please analyze your skin first.', 'error')
        return redirect(url_for('analyzer'))

    return render_template('suggestions.html', 
                         customer_name=session.get('customer_name', 'User'),
                         skin_type=session['skin_type'],
                         acne=session['acne'],
                         face_detected='yes' if session.get('face_detected', False) else 'no',
                         skin_confidence=session.get('skin_confidence', 0),
                         acne_confidence=session.get('acne_confidence', 0))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    if 'skin_type' not in session or 'acne' not in session:
        flash('Please analyze your skin first.', 'error')
        return redirect(url_for('analyzer'))

    if request.method == 'POST':
        # Process quiz responses (you can store these in database if needed)
        quiz_responses = {}
        for key, value in request.form.items():
            quiz_responses[key] = value
        
        session['quiz_responses'] = quiz_responses
        flash('Quiz completed successfully!', 'success')
        return redirect(url_for('suggestions'))

    return render_template('quiz.html', 
                         skin_type=session['skin_type'], 
                         acne=session['acne'],
                         customer_name=session.get('customer_name', 'User'))

if __name__ == '__main__':
    app.run(debug=True)