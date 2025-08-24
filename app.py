from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_mail import Mail, Message
import os
import dotenv
import uuid
import csv
import random
from flask_cors import CORS

dotenv.load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})
app.secret_key = os.urandom(24)  # Secret key for session management

# Mail configuration
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv("DEL_EMAIL")
app.config['MAIL_PASSWORD'] = os.getenv("PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)
invitations = {}

# Load student list from CSV
STUDENT_LIST_PATH = "./data.csv"
students = []

# DISABLED ROLL NUMBERS ----->
disabledRollNumber = []

with open(STUDENT_LIST_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    reader.fieldnames = [field.strip() for field in reader.fieldnames]
    for row in reader:
        row = {k.strip(): v.strip() for k, v in row.items()}
        students.append({
            'name': row['Name'].upper(),
            'roll': row['Roll No.'].strip().lower(),
            'gender': row.get('Gender', '').strip().lower()
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
    subject = "🎉 Hey !! Wanna Go Prom ?"
    REC_EMAIL = rec_roll + '@students.iitmandi.ac.in'
    token = str(uuid.uuid4())

    invitations[token] = {
        'sender_roll': roll_no,
        'sender_name': name,
        'recipient_roll': rec_roll
    }

    viewer_link = url_for('viewer', token=token, _external=True)
    disable_Link = url_for('disableEmail', roll_no=roll_no, _external=True)
    # Check if the sender's roll number is in the disabled list
    if rec_roll in disabledRollNumber:
        return redirect(url_for('privacy'))
         

    msgtmp2 = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Prom Night Invitation</title>
</head>
<body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Segoe UI', sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; min-height: 100vh; padding: 40px 0;">
    <tr>
      <td align="center">
        <!-- Inner box with updated gradient background (blue-green style) -->
        <table width="600" cellpadding="20" cellspacing="0" style="background: linear-gradient(to bottom right, #00c9a7, #0052d4); border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
          <tr>
            <td align="center" style="padding-top: 30px;">
              <!-- Heart SVG -->
              <svg width="60" height="60" viewBox="0 0 24 24" fill="#ffffff" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 
                         2 5.42 4.42 3 7.5 3c1.74 0 3.41 0.81 
                         4.5 2.09C13.09 3.81 14.76 3 16.5 3 
                         19.58 3 22 5.42 22 8.5c0 3.78-3.4 
                         6.86-8.55 11.54L12 21.35z"/>
              </svg>
              <h1 style="color: #ffffff; font-size: 28px; margin-top: 10px;">You're Invited to PROM NIGHT 💃🕺</h1>
            </td>
          </tr>
          <tr>
            <td style="color: #fff; font-size: 16px; line-height: 1.6; text-align: center;">
              <p>Hi dear,</p>
              <p>Someone special has invited you to the most magical night of the year... <strong style="color: #ffe6f9;">PROM NIGHT</strong>!</p>
              <p>Can you guess who it is from the options?</p>
              <p>It’s a mystery worth solving—and don’t worry, it’s completely safe to check 💌</p>
            </td>
          </tr>
          <tr>
            <td align="center">
              <a href="{viewer_link}" style="background-color:#157347; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">
                Reveal the Secret 💘
              </a>
            </td>
          </tr>
          <tr>
            <td align="center">
              <a href="{disable_Link}" style="background-color:black; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">
                Don't want to go? Click here to disable your email.
              </a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-top: 30px;">
              <img src="https://i.imgur.com/Twvo7Er.gif" alt="Prom Couple" style="width: 100%; max-width: 500px; border-radius: 8px;">
            </td>
          </tr>
          <tr>
            <td style="text-align: center; font-size: 14px; color: #fbe6f9;">
              <p style="margin-top: 30px;">This night might just change everything 💫</p>
              <p>See you on the dance floor 💃🕺</p>
            </td>
          </tr>
        </table>
        <p style="font-size: 12px; color: #999; padding-top: 20px;">Sent with 💗 by PromNightBot</p>
      </td>
    </tr>
  </table>
</body>
</html>


"""

    msg = Message(subject, sender=os.getenv('DEL_EMAIL'), recipients=[REC_EMAIL])
    msg.html = msgtmp2.format(viewer_link=viewer_link, disable_Link=disable_Link)
    msg.extra_headers = { 
        'List-Unsubscribe': disable_Link ,
        'X-Mailer-Tag': 'prom_invitation',
        'X-Mailer' : 'Flask-Mail'

        }
    
    mail.send(msg)
    return redirect(url_for('success'))

@app.route('/viewer')
def viewer():
    token = request.args.get('token')
    if not token or token not in invitations:
        return "Invalid or expired invitation.", 400

    sender_roll = invitations[token]['sender_roll'].strip().lower()
    sender_info = next((s for s in students if s['roll'] == sender_roll), None)

    if not sender_info:
        return "Sender not found", 404

    sender_gender = sender_info['gender'].strip().lower()

    if token not in session:
                # Extract prefix like 'b23' from sender's roll
        sender_prefix = sender_roll[:3]

        # Filter by same gender and same roll prefix
        same_batch_gender_choices = [
            s for s in students
            if s['roll'] != sender_roll
            and s['gender'] == sender_gender
            and s['roll'][:3] == sender_prefix
        ]

        # Randomly select 3 options from the filtered list
        dummy_choices = random.sample(same_batch_gender_choices, k=min(4, len(same_batch_gender_choices)))

        # Final options list
        options = dummy_choices + [sender_info, {"name": "DON'T WANNA GO", "roll": "😭"}]
        random.shuffle(options)

        # Store in session
        session[token] = options


    else:
        options = session[token]

    return render_template('viewer.html', token=token, options=options, correct_roll=sender_info['roll'])

@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    data = request.get_json()
    token = data.get('token')
    selected_roll = data.get('selected_roll')

    if token not in invitations:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 400

    invitation = invitations[token]
    sender_roll = invitation['sender_roll']
    sender_name = invitation['sender_name']
    recipient_roll = invitation['recipient_roll']

    sender_email = sender_roll + '@students.iitmandi.ac.in'

    if selected_roll == sender_roll:
        subject = "🎉 It's a PROM MATCH!"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 30px;">
            <div style="max-width: 600px; margin: auto; background: linear-gradient(to right, #43e97b, #38f9d7); padding: 20px 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <h2 style="color: #fff; text-align: center;">💃🕺 It's a Match!</h2>
                <p style="color: #fff; font-size: 16px; text-align: center;">
                    Hi <strong>{sender_name}</strong>,<br><br>
                    Your prom invitation was accepted by <strong>{recipient_roll}</strong> 🎉<br>
                    Looks like it’s time to prepare your moves for the dance floor!<br><br>
                    <strong>See you at the PROM NIGHT!</strong> 💌✨
                </p>
            </div>
        </body>
        </html>
        """
        msg = Message(subject, sender=os.getenv('DEL_EMAIL'), recipients=[sender_email])
        msg.html = html_body
        mail.send(msg)
        session.pop(token, None)
        del invitations[token]
        return jsonify({"success": True, "match": True})

    else:
        subject = "😢 Better Luck Next Time"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #fff3f3; padding: 30px;">
            <div style="max-width: 600px; margin: auto; background: linear-gradient(to right, #ff758c, #ff7eb3); padding: 20px 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <h2 style="color: #fff; text-align: center;">Oops! Not This Time 😢</h2>
                <p style="color: #fff; font-size: 16px; text-align: center;">
                    Hey <strong>{sender_name}</strong>,<br><br>
                    Sadly, <strong>{recipient_roll}</strong> didn’t guess you correctly 😔<br>
                    But don’t lose heart — there’s always another dance and another chance!<br><br>
                    You tried and that’s what matters ❤️
                </p>
            </div>
        </body>
        </html>
        """
        msg = Message(subject, sender=os.getenv('DEL_EMAIL'), recipients=[sender_email])
        msg.html = html_body
        mail.send(msg)
        session.pop(token, None)
        del invitations[token]
        return jsonify({"success": True, "match": False})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
