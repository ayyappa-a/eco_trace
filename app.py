from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Appuuu@localhost:5432/eco_trace"
)

# ...existing code...
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db = SQLAlchemy(app)

# Login manager setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# =======================
# MODELS (from models/)
# =======================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_type = db.Column(db.String(50))
    quantity = db.Column(db.Float)
    date = db.Column(db.Date, default=datetime.utcnow)

class Emission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    emission_kg = db.Column(db.Float)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    badge_name = db.Column(db.String(100))
    earned_on = db.Column(db.Date, default=datetime.utcnow)

# =======================
# LOGIN HANDLERS
# =======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# =======================
# DASHBOARD & EMISSIONS
# =======================
def calculate_emission(activity_type, quantity):
    factors = {
        "car": 0.21,        # kg CO2 per km
        "bus": 0.1,
        "train": 0.05,
        "electricity": 0.5, # kg CO2 per kWh
        "meat": 2.5,        # kg CO2 per meal
        "vegetarian": 1.0,
    }
    return round(quantity * factors.get(activity_type, 0), 2)

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        activity_type = request.form["activity_type"]
        quantity = float(request.form["quantity"])

        activity = Activity(user_id=current_user.id, activity_type=activity_type, quantity=quantity)
        db.session.add(activity)
        db.session.commit()

        emission_value = calculate_emission(activity_type, quantity)
        emission = Emission(activity_id=activity.id, emission_kg=emission_value)
        db.session.add(emission)

        if emission_value < 1.0:
            badge = Badge(user_id=current_user.id, badge_name="Eco Warrior")
            db.session.add(badge)

        db.session.commit()
        flash("Activity logged and emission calculated.")
        return redirect(url_for("dashboard"))

    # Load activities for chart
    activities = Activity.query.filter_by(user_id=current_user.id).all()
    chart_labels = [a.activity_type for a in activities]
    chart_data = []
    for a in activities:
        e = Emission.query.filter_by(activity_id=a.id).first()
        chart_data.append(e.emission_kg if e else 0)

    # Calculate total emissions
    total_emissions = db.session.query(db.func.sum(Emission.emission_kg)) \
        .join(Activity, Emission.activity_id == Activity.id) \
        .filter(Activity.user_id == current_user.id).scalar() or 0

    # Get badges
    badges = Badge.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "dashboard.html",
        labels=chart_labels,
        data=chart_data,
        total_emissions=round(total_emissions, 2),
        badges=badges
    )
# =======================
# LEADERBOARD
# =======================
@app.route("/leaderboard")
@login_required
def leaderboard():
    users = User.query.all()
    leaderboard_data = []

    for user in users:
        total_emission = db.session.query(db.func.sum(Emission.emission_kg)) \
            .join(Activity, Emission.activity_id == Activity.id) \
            .filter(Activity.user_id == user.id).scalar() or 0

        badge_count = Badge.query.filter_by(user_id=user.id).count()

        leaderboard_data.append({
            'username': user.username,
            'total_emission': round(total_emission, 2),
            'badges': badge_count
        })

    leaderboard_data.sort(key=lambda x: x['total_emission'])
    return render_template("leaderboard.html", leaderboard=leaderboard_data)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
