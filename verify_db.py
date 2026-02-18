from app import app, db, Task

def verify():
    print("Verifying database operations...")
    with app.app_context():
        # Setup: Clear existing tasks for test (optional, but good for clean state)
        # db.drop_all()
        # db.create_all()
        
        # Test 1: Add Task
        print("Test 1: Adding task...")
        t = Task(name="Test Task", category="Work", priority="high")
        db.session.add(t)
        db.session.commit()
        t_id = t.id
        print(f"Task added with ID: {t_id}")

        # Test 2: Read Task
        print("Test 2: Reading task...")
        fetched_task = Task.query.get(t_id)
        if fetched_task and fetched_task.name == "Test Task":
            print("Read verification successful.")
        else:
            print("Read verification FAILED.")
            return

        # Test 3: Update Task
        print("Test 3: Updating task...")
        fetched_task.done = True
        db.session.commit()
        updated_task = Task.query.get(t_id)
        if updated_task.done:
            print("Update verification successful.")
        else:
            print("Update verification FAILED.")
            return

        # Test 4: Delete Task
        print("Test 4: Deleting task...")
        db.session.delete(updated_task)
        db.session.commit()
        deleted_task = Task.query.get(t_id)
        if deleted_task is None:
            print("Delete verification successful.")
        else:
            print("Delete verification FAILED.")
            return
            
    print("ALL TESTS PASSED.")

if __name__ == "__main__":
    verify()
