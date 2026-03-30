from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
# A secret key is required to use Flask sessions (required for Flask-Login and flash messages)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')

# Configure database
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Fix for Vercel Postgres using postgres:// which SQLAlchemy doesn't support
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
elif os.environ.get('VERCEL'):
    # Fallback to tmp SQLite if no DATABASE_URL is set
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/tasks.db'
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(50), default='Uncategorized')
    priority = db.Column(db.String(20), default='medium')
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "due_date": self.due_date,
            "category": self.category,
            "priority": self.priority,
            "done": self.done,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

# Recreate database to apply new schema
with app.app_context():
    # Normally we would use Flask-Migrate, but here we drop and recreate for simplicity
    db.drop_all()
    db.create_all()

# Routes

@app.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", tasks=[t.to_dict() for t in tasks])

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
            
        new_user = User(username=username, password=generate_password_hash(password, method='scrypt'))
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Registration successful!', 'success')
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'error')
            
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Stats
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.done)
    pending_tasks = total_tasks - completed_tasks

    # Count tasks by category
    tasks_by_category = {}
    for task in tasks:
        category = task.category or 'Uncategorized'
        tasks_by_category[category] = tasks_by_category.get(category, 0) + 1

    return render_template(
        "dashboard.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        tasks_by_category=tasks_by_category,
    )

@app.route("/add", methods=["POST"])
@login_required
def add_task():
    task_name = request.form.get("task")
    task_description = request.form.get("description", "")
    task_due_date = request.form.get("due_date", "")
    task_category = request.form.get("category", "Uncategorized")
    task_priority = request.form.get("priority", "medium")

    if task_name:
        new_task = Task(
            name=task_name,
            description=task_description,
            due_date=task_due_date,
            category=task_category,
            priority=task_priority,
            user_id=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully!', 'success')

    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        task.name = request.form.get("task")
        task.description = request.form.get("description", "")
        task.due_date = request.form.get("due_date", "")
        task.category = request.form.get("category", "Uncategorized")
        task.priority = request.form.get("priority", "medium")
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for("index"))

    return render_template("edit.html", task=task.to_dict())

@app.route("/delete/<int:task_id>")
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted!', 'info')
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>")
@login_required
def toggle(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/api/tasks")
@login_required
def api_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return jsonify([t.to_dict() for t in tasks])

if __name__ == "__main__":
    app.run(debug=True, port=8000)
