import errno
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask.ctx import RequestContext
from flask_wtf import FlaskForm
from jinja2 import exceptions
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import psycopg2
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd 
import sqlite3
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'mcdonz'  # Replace with your own secret key
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Retrieve database credentials securely using keyring
db_host = "127.0.0.1"
db_name = "healthdb"
db_user = "postgres"
db_password = "mcdonz"

# Configure the PostgreSQL database connection
conn = psycopg2.connect(
    dbname="healthdb",
    user="postgres",
    password="mcdonz",
    host="localhost",
    port="5432"
)
conn.autocommit = True
cursor = conn.cursor()

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password


@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None


bcrypt = Bcrypt(app)
mail = Mail(app)

@app.route('/')
def home():
    return render_template('index.html')


# User routes
@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        flash('Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('user_register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()

        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[2])
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mcdonz@localhost/healthdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

   # Define the data model
class Patient(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       fullname = db.Column(db.String(100), nullable=False)
       age = db.Column(db.String(100), nullable=False)
       sex = db.Column(db.String(100), nullable=False)
       phone = db.Column(db.String(100), nullable=False)
       address = db.Column(db.String(100), nullable=False)
       blood_group = db.Column(db.String(100), nullable=False)
       weight = db.Column(db.String(100), nullable=False)
       genotype = db.Column(db.String(100), nullable=False)
       


@app.route('/add_patient', methods=['POST'])
def add_patient():
    if request.method == 'POST':
        # Retrieve data from the form
        fullname = request.form['fullname']
        age = request.form['age']
        sex = request.form['sex']
        phone = request.form['phone']
        address = request.form['address']
        blood_group = request.form['blood_group']
        weight = request.form['weight']
        genotype = request.form['genotype']

        # Create a new employee record
        new_patient = Patient(fullname=fullname, age=age, sex=sex, phone=phone, address=address, blood_group=blood_group,
                              weight=weight, genotype=genotype)

        # Add the new patient to the database
        db.session.add(new_patient)
        db.session.commit()

    # Redirect to the home page after submitting the form
    return redirect(url_for('user_dashboard'))

@app.route('/user_dashboard')
def user_dashboard():
    conn = psycopg2.connect(
        host="127.0.0.1", 
        dbname="healthdb", 
        user="postgres", 
        password="mcdonz"
    )
    cursor = conn.cursor()

    # Example query to select all employees
    cursor.execute("SELECT * FROM patient")
    data = cursor.fetchall()

    print(data) #Print data for debugging

    # Close cursor and connection
    cursor.close()
    conn.close()

    return render_template('user_dashboard.html', data=data)

# Define a route for the health tips page
@app.route('/health_tips')
def health_tips():
    return render_template('health_tips.html')


# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle user registration form submission
        name = request.form['name']
        age = request.form['age']
        sex = request.form['sex']
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        phone = request.form['phone']

        # Connect to the database
        conn = psycopg2.connect(host=db_host, dbname=db_name, user=db_user, password=db_password)
        cur = conn.cursor()

        # Insert user data into the database
        cursor.execute("INSERT INTO users (name, age, sex, username, email, password, phone) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                       (name, age, sex, username, email, password, phone))
        conn.commit()

        #Commit the database insertions
        conn.commit()

        # Close the database connection
        cur.close()
        conn.close()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Password Recovery Route
@app.route('/password_reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        # Handle password reset request and send a reset email (not implemented here)
        flash('Password reset email sent! Check your inbox.', 'info')
        return redirect(url_for('login'))
    return render_template('password_reset.html')

# Admin Dashboard (Protected Route)

def user_dashboard():
    # Add authentication check here (e.g., check if the user is an admin)
    return render_template('user_dashboard.html')




# Define the route for the contact form
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Connect to the database
        conn = psycopg2.connect(host=db_host, dbname=db_name, user=db_user, password=db_password)
        cur = conn.cursor()

        # Insert form data into the database
        cur.execute("INSERT INTO contact_form (name, email, message) VALUES (%s, %s, %s)",
                    (name, email, message))
        #Commit the database insertions
        conn.commit()

        # Close the database connection
        cur.close()
        conn.close()

        flash('Form submitted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('contact.html')


class VitalsForm(FlaskForm):
    bmi = FloatField('BMI', validators=[DataRequired(), NumberRange(min=0)])
    heart_rate = IntegerField('Heart Rate', validators=[DataRequired(), NumberRange(min=0)])
    bp = StringField('Blood Pressure', validators=[DataRequired()])
    sugar_level = StringField('Sugar Level', validators=[DataRequired()])
    blood_percentage = StringField('Blood Percentage', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def upload_vitals():
    form = VitalsForm()

    if form.validate_on_submit():
        # Assuming you have a user authentication system in place to get the user_id
        user_id = 1  # Replace with the actual user ID
        bmi = form.bmi.data
        heart_rate = form.heart_rate.data
        bp = form.bp.data
        sugar_level = form.sugar_level.data
        blood_percentage = form.blood_percentage.data

 # Store the patient vitals in the database
        sql = "INSERT INTO patient_vitals (user_id, bmi, heart_rate, bp, sugar_level, blood_percentage) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (user_id, bmi, heart_rate, bp, sugar_level, blood_percentage))
        conn.commit()

        return redirect(url_for('success'))

    return render_template('upload_vitals.html', form=form)

@app.route('/success')
def success():
    return 'Vitals uploaded successfully!'

if __name__ == '__main__':
    app.run(debug=True)

