import sqlite3
import cv2
import threading
import time
import os
import glob
import numpy as np
from flask import Flask, Response, render_template, jsonify, request, redirect, url_for, flash
from datetime import datetime, timedelta
from extract_text import setup_gemini, process_image
from database import init_db, save_reading, get_readings
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# Flask application secret key for session security. Replace with a secure value in production.

# Returns the number of alerts for a specific user from the database.
# Used to display alert badges in the UI.
def get_alert_count_for_user(user_id):
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM alerts WHERE user_id = ?', (user_id,))
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"Error getting alert count: {e}")
        return 0

# Flask context processor: makes alert_count and user_name available in all templates for dynamic UI updates.
from flask_login import current_user
@app.context_processor
def inject_alert_count():
    alert_count = 0
    user_name = "User"
    if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        alert_count = get_alert_count_for_user(current_user.id)
        # Try to get the user's name if available, else fallback to id
        user_name = getattr(current_user, 'name', None) or getattr(current_user, 'username', None) or str(current_user.id)
    return dict(alert_count=alert_count, user_name=user_name)

# Creates additional tables (user_settings, alerts) if they do not exist. Called at app startup.
def init_extended_db():
    conn = sqlite3.connect('readings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  daily_cost_limit REAL)''')
    
    # Create alerts table
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  message TEXT,
                  type TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  is_read INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()
init_extended_db()

# Set up Flask-Login for user authentication and session management.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login. Represents a logged-in user session.
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Demo credentials for login. Replace with a secure system for real deployments.
VALID_EMAIL = "admin"
VALID_PASSWORD = "1234"

# Application-wide state variables used for readings, billing, camera, and process control.
last_reading = "No reading yet"
last_reading_time = None
last_bill_amount = 0  # Holds the latest bill amount from Selenium
daily_cost_limit = 0  # Default cost limit
camera = None
capture_thread = None
process_thread = None
stop_capture = True   # Initially stopped; only starts when user clicks Start Process
debug_info = "Not started"
initial_reading_value = None  # Holds the first valid reading
current_phase = "single"      # "single" or "three" based on the HTML selection
capture_interval = 35  # seconds (increased delay by 35 seconds)
next_capture_timestamp = None  # Next capture time
process_started = False         # To ensure we only start once

# Define a function to get the camera
def get_camera():
    """
    Opens the camera only if the process is running. Tries camera 1, then camera 0 if unavailable.
    """
    global camera, debug_info
    if not process_started:
        return None
    if camera is None:
        camera = cv2.VideoCapture(1)
        if not camera.isOpened():
            debug_info = "Failed to open camera 1, trying camera 0..."
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                debug_info = "No cameras available!"
                return None
    return camera

# Define a function to enhance the image
def enhance_image(frame):
    """
    Improves captured image quality for better text recognition by the AI model.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    denoised = cv2.fastNlMeansDenoising(enhanced)
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    height, width = sharpened.shape
    scaled = cv2.resize(sharpened, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
    return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)

# Define a function to get the bill from the site
def get_bill_from_site(consumption, phase):
    """
    Uses Selenium to fetch the actual electricity bill from the KSEB portal based on consumption and phase.
    This simulates a real-world bill calculation using the official website.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.get("https://bills.kseb.in")
        if phase != 1:
            phase_element = driver.find_element(By.ID, "phase3")
            phase_element.click()
        reading_str = str(int(consumption))
        input_element = driver.find_element(By.ID, "unit")
        input_element.clear()
        input_element.send_keys(reading_str + Keys.ENTER)
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".total.blue-tail")))
        text_value = element.text.strip()
        clean_value = ''.join(filter(str.isdigit, text_value))
        val = int(clean_value) if clean_value else 0
        amount = val / 100
        time.sleep(2)
        return amount
    except Exception as e:
        print("Error in get_bill_from_site:", e)
        return None
    finally:
        driver.quit()

# Define a function to capture images
def capture_images():
    """
    Continuously captures images from the camera and saves both the original and enhanced versions to disk at regular intervals.
    """
    global debug_info, next_capture_timestamp, stop_capture
    os.makedirs('input', exist_ok=True)
    while not stop_capture:
        now = datetime.now()
        next_capture_timestamp = now + timedelta(seconds=capture_interval)
        cam = get_camera()
        if cam is None:
            time.sleep(5)
            continue
        ret, frame = cam.read()
        if not ret:
            debug_info = "Failed to capture frame"
            time.sleep(1)
            continue
        enhanced_frame = enhance_image(frame)
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        original_path = f'input/original_{timestamp}.jpg'
        enhanced_path = f'input/enhanced_{timestamp}.jpg'
        cv2.imwrite(original_path, frame)
        cv2.imwrite(enhanced_path, enhanced_frame)
        debug_info = f"Saved images at {timestamp}"
        time.sleep(capture_interval)
    # When stopped, clear next capture time
    next_capture_timestamp = None

# Define a function to process saved images
def process_saved_images():
    """
    Continuously processes the latest captured images to extract meter readings using AI.
    Sets the initial reading, then tracks consumption changes and triggers billing logic.
    """
    global last_reading, last_reading_time, debug_info, initial_reading_value, current_phase, last_bill_amount
    model = setup_gemini()
    debug_info = "Model initialized"
    
    # Add 5-second delay before taking first reading
    if initial_reading_value is None:
        debug_info = "Waiting 5 seconds before taking first reading..."
        time.sleep(5)
        debug_info = "Ready to take first reading"
    
    while not stop_capture:
        try:
            enhanced_files = glob.glob('input/enhanced_*.jpg')
            if not enhanced_files:
                time.sleep(1)
                continue
            latest_enhanced = max(enhanced_files)
            latest_original = latest_enhanced.replace('enhanced_', 'original_')
            reading = process_image(model, latest_enhanced)
            if not reading or reading == "No KWh readings found":
                reading = process_image(model, latest_original)
            if reading and reading != "No KWh readings found":
                import re
                numbers = re.findall(r'\d+\.?\d*', reading)
                if not numbers:
                    raise ValueError("No numbers found in reading")
                current_units = float(numbers[0])
                print(f"Extracted units: {current_units}")
                
                if initial_reading_value is None:
                    initial_reading_value = current_units
                    debug_info = f"Initial reading set: {initial_reading_value} KWh"
                    continue
                
                if current_units == initial_reading_value:
                    debug_info = f"Current: {current_units} KWh | Initial: {initial_reading_value} KWh | No change detected"
                    continue
                
                difference_units = current_units - initial_reading_value
                new_reading = f"{difference_units:.0f} KWh (Δ)"
                if new_reading == last_reading:
                    debug_info = f"Current: {current_units} KWh | Initial: {initial_reading_value} KWh | Difference: {difference_units:.1f} KWh | Duplicate reading; skipping"
                    continue
                
                phase_num = 1 if current_phase == "single" else 3
                bill_amount = get_bill_from_site(difference_units, phase_num)
                if bill_amount is None:
                    debug_info = f"Current: {current_units} KWh | Initial: {initial_reading_value} KWh | Difference: {difference_units:.1f} KWh | Error obtaining bill amount"
                    bill_amount = 0
                last_bill_amount = round(bill_amount, 2)
                print(f"Bill amount: Rs.{last_bill_amount}")
                last_reading = new_reading
                last_reading_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                bill_details = {
                    'final': last_bill_amount,
                    'fixed_charge': 0,
                    'energy_charge': 0,
                    'tod_charge': 0,
                    'duty': 0,
                    'subsidy': 0
                }
                save_reading(last_reading, latest_enhanced, bill_details)
                debug_info = f"Current: {current_units} KWh | Initial: {initial_reading_value} KWh | Difference: {difference_units:.1f} KWh | Bill: Rs.{last_bill_amount}"
        except Exception as e:
            debug_info = f"Error processing images: {str(e)}"
            print(debug_info)
        time.sleep(1)

# Define a route to get the status
@app.route('/get_status')
def get_status():
    """
    Returns the time left for the next capture and its time.
    """
    global initial_reading_value, debug_info
    
    # Handles the special case when the system is waiting to take the very first reading after startup.
    if initial_reading_value is None and "Waiting 5 seconds" in debug_info:
        # Calculate remaining time from debug_info timestamp
        try:
            return jsonify({
                'next_capture_in': 5,
                'next_capture_time': (datetime.now() + timedelta(seconds=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'is_initial_delay': True
            })
        except Exception as e:
            print(f"Error calculating initial delay: {e}")
    
    # Handles the normal periodic image capture interval for ongoing meter monitoring.
    if next_capture_timestamp:
        now = datetime.now()
        remaining = int((next_capture_timestamp - now).total_seconds())
        capture_time = next_capture_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            'next_capture_in': remaining,
            'next_capture_time': capture_time,
            'is_initial_delay': False
        })
    
    return jsonify({
        'next_capture_in': "N/A",
        'next_capture_time': "N/A",
        'is_initial_delay': False
    })

# Define a route to start the process
@app.route('/start_process', methods=['POST'])
def start_process():
    """
    Starts the threads that handle camera image capture and meter reading processing.
    Ensures only one set of threads runs at a time.
    """
    global stop_capture, process_started, capture_thread, process_thread, debug_info, initial_reading_value
    if not process_started:
        # Reset initial reading when starting afresh
        initial_reading_value = None
        stop_capture = False
        capture_thread = threading.Thread(target=capture_images)
        capture_thread.daemon = True
        capture_thread.start()
        process_thread = threading.Thread(target=process_saved_images)
        process_thread.daemon = True
        process_thread.start()
        process_started = True
        debug_info = "Process started"
        return "Process started", 200
    else:
        return "Process already running", 200

# Define a route to stop the process
@app.route('/stop_process', methods=['POST'])
def stop_process():
    """
    Stops the background threads for image capture and processing.
    Releases camera resources.
    """
    global stop_capture, process_started, debug_info, camera
    stop_capture = True
    process_started = False
    debug_info = "Process stopped"
    if camera is not None:
        camera.release()
        camera = None
    return "Process stopped", 200

# Define a route to get the reading
@app.route('/get_reading')
def get_reading():
    """
    Returns the latest meter reading, bill amount, and debug information as a JSON response for the frontend.
    """
    return jsonify({
        'reading': last_reading,
        'timestamp': last_reading_time,
        'bill_amount': last_bill_amount,
        'debug_info': debug_info,
        'initial_reading': initial_reading_value
    })

# Define a route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login with demo credentials.
    Always redirects after form submission for security.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == VALID_EMAIL and password == VALID_PASSWORD:
            user = User(email)
            login_user(user)
            return redirect(url_for('index'))  # Always redirect after login
        else:
            flash('Invalid email or password')
            return redirect(url_for('login', email=email))  # Redirect after failed login, preserve username
    return render_template('Login.html')

# Define a route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('login'))

# Define a route for the index
@app.route('/')
def index():
    """
    Redirects users to the login page if they are not authenticated.
    Otherwise, shows the main index page.
    """
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')

# Define a route for the dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """
    Renders the main dashboard/profile/alerts page for the logged-in user.
    """
    return render_template('dashboard.html')

# Define a route for the profile
@app.route('/profile')
@login_required
def profile():
    """
    Renders the main dashboard/profile/alerts page for the logged-in user.
    """
    return render_template('profile.html')

# Define a route for alerts
@app.route('/alerts')
@login_required
def alerts():
    """
    Renders the main dashboard/profile/alerts page for the logged-in user.
    """
    return render_template('alerts.html')

# Define a route for video feed
@app.route('/video_feed')
def video_feed():
    """
    Streams live camera frames to the browser using multipart JPEG streaming.
    """
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Define a route to get readings
@app.route('/get_readings')
def get_readings_route():
    """
    Retrieves all meter readings and related billing data from the database for display or analysis.
    """
    readings = get_readings()
    return jsonify([{
        'reading': r[0],
        'timestamp': r[1],
        'image_path': r[2],
        'fixed_charge': r[3],
        'energy_charge': r[4],
        'tod_charge': r[5],
        'duty': r[6],
        'subsidy': r[7],
        'total_amount': r[8]
    } for r in readings])

# Define a route to clear readings
@app.route('/clear_readings', methods=['POST'])
def clear_readings():
    """
    Deletes all readings from the database but retains the user's cost limit setting.
    """
    global initial_reading_value, last_reading, last_reading_time, last_bill_amount, debug_info
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        # Clear only readings, not user settings
        c.execute('DELETE FROM readings')
        conn.commit()
        conn.close()

        # Reset global variables
        initial_reading_value = None
        last_reading = "No reading yet"
        last_reading_time = None
        last_bill_amount = 0
        debug_info = "All readings cleared"

        return jsonify({
            "success": True,
            "message": "All readings cleared successfully"
        })
    except Exception as e:
        print(f"Error clearing readings: {e}")
        return jsonify({
            "success": False,
            "message": f"Failed to clear readings: {str(e)}"
        })

# Define a route to clear all
@app.route('/clear_all', methods=['POST'])
@login_required
def clear_all():
    """
    Deletes all meter readings and user settings (including cost limit) from the database.
    """
    global initial_reading_value, last_reading, last_reading_time, last_bill_amount
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        # Clear readings
        c.execute('DELETE FROM readings')
        # Clear user settings (including cost limit)
        c.execute('DELETE FROM user_settings WHERE user_id = ?', (current_user.id,))
        conn.commit()
        conn.close()
        
        # Reset global variables
        initial_reading_value = None
        last_reading = "No reading yet"
        last_reading_time = None
        last_bill_amount = 0
        
        return jsonify({
            "success": True,
            "message": "All data cleared successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error clearing data: {str(e)}"
        })

# Define a route to get dashboard data
@app.route('/get_dashboard_data')
@login_required
def get_dashboard_data():
    """
    Gathers all data needed for the dashboard: current reading, average usage, cost limit, alerts, and usage trends.
    """
    try:
        # Get all readings from history
        readings = get_readings()
        
        # Use the logged-in user's ID for all queries
        user_id = current_user.id
        
        # Get user's cost limit first
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        c.execute('SELECT daily_cost_limit FROM user_settings WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        cost_limit = float(result[0]) if result else 0
        conn.close()
        
        print(f"Retrieved cost limit: {cost_limit}")  # Debug print
        
        if readings:
            # Get the latest reading for current consumption
            latest_reading = readings[0]  # First reading since we order by DESC
            # Extract numeric value from reading (remove 'KWh' and '(Δ)')
            reading_value = latest_reading[0].split()[0]
            current_reading = latest_reading[0]  # Use the full reading text
            current_bill = float(latest_reading[8])  # Total amount from the last reading
            
            # Calculate average daily usage from all readings
            total_units = sum(float(r[0].split()[0]) for r in readings if r[0].split()[0].replace('.','').isdigit())
            avg_daily = total_units / len(readings)
            
            # Get consumption trend data
            trend_readings = readings[-30:]  # Get last 30 readings for trend
            consumption_data = []
            consumption_labels = []
            
            # Initialize peak hours data
            peak_hours_data = [0] * 8  # 8 time slots (12AM, 3AM, 6AM, 9AM, 12PM, 3PM, 6PM, 9PM)
            peak_hours_counts = [0] * 8  # Count readings in each slot for averaging
            
            for reading in trend_readings:
                try:
                    value = float(reading[0].split()[0])  # Extract numeric value from reading
                    consumption_data.append(value)
                    # Format timestamp for label
                    time_str = reading[1]  # Timestamp from reading
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    consumption_labels.append(dt.strftime('%d/%m %H:%M'))
                    
                    # Calculate peak hours data
                    hour = dt.hour
                    slot = hour // 3  # Divide day into 8 3-hour slots
                    peak_hours_data[slot] += value
                    peak_hours_counts[slot] += 1
                    
                except (ValueError, IndexError) as e:
                    print(f"Error processing reading: {e}")
                    continue
            
            # Calculate averages for peak hours
            peak_hours_data = [
                round(peak_hours_data[i] / peak_hours_counts[i], 2) if peak_hours_counts[i] > 0 else 0 
                for i in range(8)
            ]
            
        else:
            # No readings in history
            current_reading = "0 KWh"
            current_bill = 0
            avg_daily = 0
            consumption_data = []
            consumption_labels = []
            peak_hours_data = [0] * 8

        # Calculate limit usage percentage based on latest bill amount
        limit_used_percent = (current_bill / cost_limit * 100) if cost_limit > 0 else 0
        limit_remaining_percent = max(0, 100 - limit_used_percent)

        # Generate alerts based on latest bill amount
        if cost_limit > 0 and readings:
            save_limit_alert(user_id, current_bill, cost_limit, limit_used_percent)

        response_data = {
            "current_reading": current_reading,
            "average_daily": f"{avg_daily:.1f}",
            "current_bill": current_bill,
            "cost_limit": cost_limit,
            "limit_used_percent": limit_used_percent,
            "limit_remaining_percent": limit_remaining_percent,
            "has_readings": bool(readings),
            "consumption_data": consumption_data,
            "consumption_labels": consumption_labels,
            "peak_hours_data": peak_hours_data
        }
        print(f"Sending dashboard data: {response_data}")  # Debug print
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in get_dashboard_data: {str(e)}")
        return jsonify({"error": str(e)})

# Define a function to generate frames
def gen_frames():
    """
    Continuously generates camera frames for live video streaming to the browser.
    If camera is off, shows a placeholder image.
    """
    import numpy as np
    # Create a placeholder frame (black with text) if camera is off
    placeholder_frame = np.zeros((480,640,3), dtype=np.uint8)
    cv2.putText(placeholder_frame, "Camera Off", (50,240),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                
    while True:
        if not process_started:
            ret, buffer = cv2.imencode('.jpg', placeholder_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(1)
            continue
            
        cam = get_camera()
        if cam is None:
            time.sleep(1)
            continue
        ret, frame = cam.read()
        if not ret:
            continue
        if last_reading:
            cv2.putText(frame, f"Last Reading: {last_reading}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if last_reading_time:
                cv2.putText(frame, f"Time: {last_reading_time}",
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Status: {debug_info}",
                    (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Define a function to clean up resources and log out users
def cleanup():
    """
    Releases camera resources and logs out all users.
    Used for safe shutdown and cleanup.
    """
    global stop_capture, camera
    stop_capture = True
    try:
        if camera:
            camera.release()
    except Exception as e:
        print("Error releasing camera:", e)
    cv2.destroyAllWindows()
    
    # Clear all user sessions
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        c.execute('DELETE FROM user_settings')  # Clear user settings
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error clearing user sessions:", e)

# Define a function to save an alert
def save_alert(user_id, message, alert_type):
    """
    Saves a new alert in the database for the user, avoiding duplicates.
    """
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        # Checks if an identical alert is already present to prevent duplicate notifications.
        c.execute("SELECT 1 FROM alerts WHERE user_id = ? AND message = ? AND type = ?", (user_id, message, alert_type))
        exists = c.fetchone()

        # Inserts a new alert into the database if it is not a duplicate.
        if not exists:
            c.execute('INSERT INTO alerts (user_id, message, type) VALUES (?, ?, ?)',
                      (user_id, message, alert_type))
            conn.commit()

        conn.close()
    except Exception as e:
        print(f"Error saving alert: {e}")

# Define a route to get alerts
@app.route('/get_alerts')
@login_required
def get_alerts():
    """
    Retrieves all alerts for the currently logged-in user for display in the UI.
    """
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        c.execute('SELECT id, message, type, timestamp, is_read FROM alerts WHERE user_id = ? ORDER BY timestamp DESC',
                 (current_user.id,))
        alerts = c.fetchall()
        conn.close()
        
        return jsonify([{
            'id': alert[0],
            'message': alert[1],
            'type': alert[2],
            'timestamp': alert[3],
            'is_read': alert[4]
        } for alert in alerts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Define a route to mark an alert as read
@app.route('/mark_alert_read/<int:alert_id>', methods=['POST'])
@login_required
def mark_alert_read(alert_id):
    """
    Marks the specified alert as read in the database.
    """
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        c.execute('UPDATE alerts SET is_read = 1 WHERE id = ? AND user_id = ?',
                 (alert_id, current_user.id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Define a route to clear alerts
@app.route('/clear_alerts', methods=['POST'])
@login_required
def clear_alerts():
    """
    Deletes all alerts for the current user from the database.
    """
    try:
        conn = sqlite3.connect('readings.db')
        c = conn.cursor()
        c.execute('DELETE FROM alerts WHERE user_id = ?', (current_user.id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper for dashboard: saves alerts if cost limit is exceeded or nearly reached.
def save_limit_alert(user_id, current_bill, cost_limit, limit_used_percent):
    if limit_used_percent >= 100:
        message = f"Alert: Daily cost limit exceeded! Current bill: ₹{current_bill:.2f}, Limit: ₹{cost_limit}"
        save_alert(user_id, message, "danger")
    elif limit_used_percent >= 90:
        remaining = cost_limit - current_bill
        message = f"Warning: Approaching daily limit! Used: {limit_used_percent:.1f}%, Remaining: ₹{remaining:.2f}"
        save_alert(user_id, message, "warning")

# Entry point for running the Flask application.
# This block runs only if the script is executed directly (not imported as a module).
if __name__ == '__main__':
    # Ensure the input directory exists for saving images
    os.makedirs('input', exist_ok=True)
    try:
        # Start the Flask development server on all interfaces, port 5000
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        # Gracefully handle Ctrl+C interruption
        print("KeyboardInterrupt received.")
    except Exception as e:
        # Print any unexpected errors
        print(f"Error occurred: {e}")
    finally:
        # Always clean up resources and log out users on shutdown
        print("Cleaning up and logging out all users...")
        cleanup()
        print("Cleanup complete. All users logged out.")
