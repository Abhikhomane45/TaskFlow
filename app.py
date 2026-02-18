from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Configure database
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Fix for Vercel Postgres using postgres:// which SQLAlchemy doesn't support
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
elif os.environ.get('VERCEL'):
    # Fallback to tmp SQLite if no DATABASE_URL is set (e.g. during build or if not configured)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/tasks.db'
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='Uncategorized')
    priority = db.Column(db.String(20), default='medium')
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "priority": self.priority,
            "done": self.done,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

# Create the database tables
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    tasks = Task.query.all()
    return render_template("index.html", tasks=[t.to_dict() for t in tasks])


@app.route("/dashboard")
def dashboard():
    tasks = Task.query.all()
    
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
def add_task():
    task_name = request.form.get("task")
    task_category = request.form.get("category", "Uncategorized")
    task_priority = request.form.get("priority", "medium")

    if task_name:
        new_task = Task(
            name=task_name,
            category=task_category,
            priority=task_priority
        )
        db.session.add(new_task)
        db.session.commit()

    return redirect(url_for("index"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        task.name = request.form.get("task")
        task.category = request.form.get("category", "Uncategorized")
        task.priority = request.form.get("priority", "medium")
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("edit.html", task=task.to_dict())


@app.route("/delete/<int:task_id>")
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/api/tasks")
def api_tasks():
    tasks = Task.query.all()
    return jsonify([t.to_dict() for t in tasks])


if __name__ == "__main__":
    app.run(debug=True, port=8000)
