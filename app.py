from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_mail import Mail, Message
import os
import dotenv
import uuid
import random
import threading
import crud
from models import User, Invitation
from db import SessionLocal
from flask_cors import CORS
import pandas as pd

dotenv.load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})
app.secret_key = os.urandom(24)

# Mail configuration
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv("DEL_EMAIL")
app.config['MAIL_PASSWORD'] = os.getenv("PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Background email sender
def send_email_async(msg):
    with app.app_context():
        mail.send(msg)

# DISABLED ROLL NUMBERS
disabledRollNumber = []

STUDENT_LIST_PATH = "List of Students (IIT Mandi)_new.xlsx"
students = []

# Read Excel file
df = pd.read_excel(STUDENT_LIST_PATH, engine="openpyxl")
df.columns = [col.strip() for col in df.columns]

for _, row in df.iterrows():
    students.append({
        "name": str(row["Name"]).strip().upper(),
        "roll": str(row["Employee No"]).strip().lower(),
        "gender": str(row.get("Gender", "")).strip().lower()
    })

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/disableEmail')
def disableEmail():
    d = request.args.get('roll_no').strip().lower()
    disabledRollNumber.append(d)
    return render_template('disableEmail.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/resubscribe')
def resubscribe():
    d = request.args.get('roll_no').strip().lower()
    if d in disabledRollNumber:
        disabledRollNumber.remove(d)
    return "<h1>Resubscribe</h1><p>You have successfully resubscribed to the email list.</p>"

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    roll_no = request.form['roll_no'].strip().lower()
    rec_roll = request.form["prom's_roll_no"].strip().lower()
    if rec_roll in disabledRollNumber:
        return redirect(url_for('privacy'))

    subject = "🎉 Hey !! Wanna Go Prom ?"
    REC_EMAIL = rec_roll + '@students.iitmandi.ac.in'
    token = str(uuid.uuid4())
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(sender_name=name, sender_roll=roll_no).first()
        if not user:
            crud.create_user(db, sender_name=name, sender_roll=roll_no, recipient_roll=rec_roll)

        invitation = Invitation(
            token=token,
            sender_roll=roll_no,
            sender_name=name,
            recipient_roll=rec_roll,
            status='pending',
        )
        db.add(invitation)
        db.commit()
    finally:
        db.close()

    viewer_link = url_for('viewer', token=token, _external=True)
    disable_Link = url_for('disableEmail', roll_no=roll_no, _external=True)

    msg_html = f"""<!DOCTYPE html>
<html>... <!-- your existing HTML here, use {viewer_link} and {disable_Link} as placeholders -->
</html>
"""
    msg = Message(subject, sender=os.getenv('DEL_EMAIL'), recipients=[REC_EMAIL])
    msg.html = msg_html
    msg.extra_headers = {
        'List-Unsubscribe': disable_Link,
        'X-Mailer-Tag': 'prom_invitation',
        'X-Mailer': 'Flask-Mail'
    }

    # send email in background
    threading.Thread(target=send_email_async, args=(msg,)).start()
    return redirect(url_for('success'))

@app.route('/viewer')
def viewer():
    token = request.args.get('token')
    db = SessionLocal()
    try:
        invitation = db.query(Invitation).filter_by(token=token).first()
        if not token or not invitation:
            return "Invalid or expired invitation.", 400

        sender_roll = invitation.sender_roll.strip().lower()
        sender_info = next((s for s in students if s['roll'] == sender_roll), None)
        if not sender_info:
            return "Sender not found", 404

        sender_gender = sender_info['gender'].strip().lower()

        if token not in session:
            sender_prefix = sender_roll[:3]
            same_batch_gender_choices = [
                s for s in students
                if s['roll'] != sender_roll
                and s['gender'] == sender_gender
                and s['roll'][:3] == sender_prefix
            ]
            dummy_choices = random.sample(same_batch_gender_choices, k=min(4, len(same_batch_gender_choices)))
            options = dummy_choices + [sender_info, {"name": "DON'T WANNA GO", "roll": "😭"}]
            random.shuffle(options)
            session[token] = options
        else:
            options = session[token]

        return render_template('viewer.html', token=token, options=options, correct_roll=sender_info['roll'])
    finally:
        db.close()

@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    data = request.get_json()
    token = data.get('token')
    selected_roll = data.get('selected_roll')
    db = SessionLocal()
    try:
        invitation = db.query(Invitation).filter_by(token=token).first()
        if not invitation:
            return jsonify({"success": False, "message": "Invalid or expired token"}), 400

        sender_roll = invitation.sender_roll
        sender_name = invitation.sender_name
        recipient_roll = invitation.recipient_roll

        invitation.status = 'matched' if selected_roll.strip().lower() == sender_roll.strip().lower() else 'failed'
        db.add(invitation)
        db.commit()
    finally:
        db.close()

    sender_email = sender_roll + '@students.iitmandi.ac.in'

    subject = "🎉 It's a PROM MATCH!" if selected_roll.strip().lower() == sender_roll.strip().lower() else "😢 Better Luck Next Time"
    html_body = f"""<html><body>... your HTML here ...</body></html>"""
    msg = Message(subject, sender=os.getenv('DEL_EMAIL'), recipients=[sender_email])
    msg.html = html_body

    threading.Thread(target=send_email_async, args=(msg,)).start()
    session.pop(token, None)
    return jsonify({"success": True, "match": selected_roll.strip().lower() == sender_roll.strip().lower()})

if __name__ == '__main__':
    app.run(debug=True, port=8080)



