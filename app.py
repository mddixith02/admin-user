from flask import Flask, render_template, request, redirect, url_for, session, flash
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime  

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

FEEDBACK_FILE = 'feedback.xml'

def initialize_feedback_file():
    #Initialize the feedback XML file with root element if it doesn't exist or is empty
    if not os.path.exists(FEEDBACK_FILE) or os.path.getsize(FEEDBACK_FILE) == 0:
        root = ET.Element('feedbacks')
        tree = ET.ElementTree(root)
        tree.write(FEEDBACK_FILE, encoding='utf-8', xml_declaration=True)

def is_email_exists(email):
    #Check if email already exists in feedbacks
    feedbacks = get_feedbacks()
    return any(fb['email'].lower() == email.lower() for fb in feedbacks)

def is_valid_email(email):
    #Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def add_feedback(email, feedback):
    #Add a new feedback to the XML file
    initialize_feedback_file()
    
    try:
        tree = ET.parse(FEEDBACK_FILE)
        root = tree.getroot()
    except ET.ParseError:
        root = ET.Element('feedbacks')
        tree = ET.ElementTree(root)
    
    new_feedback = ET.SubElement(root, 'feedback')
    ET.SubElement(new_feedback, 'email').text = email
    ET.SubElement(new_feedback, 'content').text = feedback
    
    tree.write(FEEDBACK_FILE, encoding='utf-8', xml_declaration=True)

def delete_feedback(email):
    #Delete feedback by email
    try:
        tree = ET.parse(FEEDBACK_FILE)
        root = tree.getroot()
    except ET.ParseError:
        return False

    for feedback in root.findall('feedback'):
        if feedback.find('email').text == email:
            root.remove(feedback)
            tree.write(FEEDBACK_FILE, encoding='utf-8', xml_declaration=True)
            return True
    return False

def get_feedbacks():
    #Get all feedbacks from the XML fileS
    initialize_feedback_file()
    
    try:
        tree = ET.parse(FEEDBACK_FILE)
        root = tree.getroot()
    except ET.ParseError:
        return []
    
    feedbacks = []
    for feedback in root.findall('feedback'):
        email = feedback.find('email').text if feedback.find('email') is not None else ''
        content = feedback.find('content').text if feedback.find('content') is not None else ''
        feedbacks.append({
            'email': email,
            'content': content
        })
    
    return feedbacks

def add_feedback(email, feedback):
    #Add a new feedback to the XML file with timestamp
    initialize_feedback_file()
    
    try:
        tree = ET.parse(FEEDBACK_FILE)
        root = tree.getroot()
    except ET.ParseError:
        root = ET.Element('feedbacks')
        tree = ET.ElementTree(root)
    
    new_feedback = ET.SubElement(root, 'feedback')
    ET.SubElement(new_feedback, 'email').text = email
    ET.SubElement(new_feedback, 'content').text = feedback
    ET.SubElement(new_feedback, 'timestamp').text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    tree.write(FEEDBACK_FILE, encoding='utf-8', xml_declaration=True)

def get_feedbacks():
    #Get all feedbacks from the XML file with timestamp
    initialize_feedback_file()
    
    try:
        tree = ET.parse(FEEDBACK_FILE)
        root = tree.getroot()
    except ET.ParseError:
        return []
    
    feedbacks = []
    for feedback in root.findall('feedback'):
        email = feedback.find('email').text if feedback.find('email') is not None else ''
        content = feedback.find('content').text if feedback.find('content') is not None else ''
        timestamp = feedback.find('timestamp').text if feedback.find('timestamp') is not None else ''
        feedbacks.append({
            'email': email,
            'content': content,
            'timestamp': timestamp
        })
    
    # Sort feedbacks by timestamp (newest first)
    feedbacks.sort(key=lambda x: x['timestamp'], reverse=True)
    return feedbacks

users = {
    'user1': {'password': '123', 'role': 'user'},
    'user2': {'password': '123', 'role': 'user'},
    'admin': {'password': 'admin123', 'role': 'admin'}
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if username in users and users[username]['password'] == password:
            if (user_type == 'admin' and users[username]['role'] == 'admin') or \
               (user_type == 'user' and users[username]['role'] == 'user'):
                session['username'] = username
                session['role'] = users[username]['role']
                
                if users[username]['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
        
        flash("Invalid credentials or user type", "error")
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        email_to_delete = request.form.get('email_to_delete')
        if delete_feedback(email_to_delete):
            flash(f"Feedback from {email_to_delete} deleted successfully!", "success")
        else:
            flash(f"Failed to delete feedback from {email_to_delete}", "error")
        return redirect(url_for('admin_dashboard'))
    
    feedbacks = get_feedbacks()
    return render_template('admin_dashboard.html', username=session['username'], feedbacks=feedbacks)

@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'username' not in session or session['role'] != 'user':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        feedback = request.form.get('feedback')
        
        if not is_valid_email(email):
            flash("Please enter a valid email address", "error")
        elif is_email_exists(email):
            flash("This email has already submitted feedback", "error")
        else:
            add_feedback(email, feedback)
            flash("Feedback submitted successfully!", "success")
        
        return redirect(url_for('user_dashboard'))
    
    return render_template('user_dashboard.html', username=session['username'])

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        
        # Email is optional (will be None if not provided)
        email = data.get('email')  
        feedback_text = data.get('feedback')

        if not feedback_text:
            return jsonify({
                'status': 'error',
                'message': 'Feedback text is required'
            }), 400

        
        new_feedback = Feedback(
            content=feedback_text,
            email=email,  
            timestamp=datetime.utcnow()  
        )
        
        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Feedback submitted',
            'data': {
                'id': new_feedback.id,
                'timestamp': new_feedback.timestamp.isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.after_request
def prevent_back(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    initialize_feedback_file()
    app.run(debug=True)