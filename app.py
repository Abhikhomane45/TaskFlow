from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import json
import os

# Create a Flask application instance
app = Flask(__name__)

# JSON file where all tasks will be saved and loaded from
DATA_FILE = "tasks.json"


# --------------------- Helper Functions ---------------------

def load_tasks():
    """
    Loads tasks from the JSON file.
    If the file exists, read and return the list of tasks.
    If it doesn't exist, return an empty list.
    """
    if os.path.exists(DATA_FILE):  # Check if tasks.json exists
        with open(DATA_FILE, 'r') as f:
            return json.load(f)  # Read JSON & convert to Python list
    return []  # If file not found, return empty list


def save_tasks(tasks):
    """
    Saves the updated tasks list back to the JSON file.
    """
    with open(DATA_FILE, 'w') as f:
        json.dump(tasks, f, indent=4)  # Write tasks to file in formatted style


# Load tasks only once when server starts
tasks = load_tasks()


# --------------------- Routes (Pages) ---------------------

@app.route("/")
def index():
    """
    Homepage route.
    Displays all tasks on index.html.
    Sends 'tasks' list to the template.
    """
    return render_template("index.html", tasks=tasks)


@app.route("/dashboard")
def dashboard():
    """
    Dashboard page showing analytics:
    - Total tasks
    - Completed tasks
    - Pending tasks
    - Tasks count by category
    """
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task['done'])  # Count done=True
    pending_tasks = total_tasks - completed_tasks

    # Count how many tasks in each category (Work, Study, etc.)
    tasks_by_category = {}
    for task in tasks:
        category = task.get('category', 'Uncategorized')
        tasks_by_category[category] = tasks_by_category.get(category, 0) + 1

    # Render dashboard template with statistics
    return render_template("dashboard.html",
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           pending_tasks=pending_tasks,
                           tasks_by_category=tasks_by_category)


@app.route("/add", methods=["POST"])
def add_task():
    """
    Adds a new task.
    Form sends task name, category, and priority using POST request.
    """
    task_name = request.form.get("task")  # Task title
    task_category = request.form.get("category", "Uncategorized")  # Task category
    task_priority = request.form.get("priority", "medium")  # Priority level

    if task_name:
        # Create a new task dictionary
        new_task = {
            "id": len(tasks) + 1,  # Unique incremental ID
            "name": task_name,
            "category": task_category,
            "priority": task_priority,
            "done": False,  # By default, the task is not completed
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")  # Timestamp
        }

        tasks.append(new_task)  # Add new task to list
        save_tasks(tasks)  # Save to JSON file

    return redirect(url_for("index"))  # Redirect to homepage


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    """
    Edit a task.
    GET → show the edit page with existing data.
    POST → save the updated task.
    """
    # Find task with matching ID
    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        return redirect(url_for("index"))  # If not found, return home

    if request.method == "POST":
        # Get edited data from form
        updated_name = request.form.get("task")
        updated_category = request.form.get("category", "Uncategorized")
        updated_priority = request.form.get("priority", "medium")

        # Update values if user entered proper info
        if updated_name:
            task['name'] = updated_name
            task['category'] = updated_category
            task['priority'] = updated_priority
            save_tasks(tasks)  # Save changes

        return redirect(url_for("index"))

    # Show edit form page
    return render_template("edit.html", task=task)


@app.route("/delete/<int:task_id>")
def delete(task_id):
    """
    Deletes a task by filtering it out from the list.
    """
    global tasks  # Modify the global tasks list
    tasks = [t for t in tasks if t['id'] != task_id]  # Keep only tasks != id
    save_tasks(tasks)
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    """
    Toggles the 'done' status of a task.
    If done=True → becomes False
    If done=False → becomes True
    """
    task = next((t for t in tasks if t['id'] == task_id), None)

    if task:
        task['done'] = not task['done']  # Flip True/False
        save_tasks(tasks)

    return redirect(url_for("index"))


@app.route("/api/tasks")
def api_tasks():
    """
    Returns all tasks as JSON (API endpoint).
    Useful for mobile apps, JS frontend, etc.
    """
    return jsonify(tasks)


# Run Flask app on port 8000
if __name__ == "__main__":
    app.run(debug=True, port=8000)
