from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask( __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ------------------ MODELS ------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default="Member")

    projects = db.relationship('Project', backref='creator', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    due_date = db.Column(db.String(50))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ ROUTES ------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form.get('role', 'Member')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return redirect(url_for('login'))

        new_user = User(email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == "Admin":
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard_page'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if request.method == 'POST':
        if current_user.role != "Admin":
            return "Forbidden"
        name = request.form['name']
        description = request.form['description']
        project = Project(name=name, description=description, created_by=current_user.id)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('projects_list'))
    return render_template('projects.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})

@app.route('/projects', methods=['POST'])
@login_required
def create_project():
    if current_user.role != "Admin":
        return jsonify({"error": "Forbidden"}), 403
    data = request.json
    project = Project(name=data['name'], description=data['description'], created_by=current_user.id)
    db.session.add(project)
    db.session.commit()
    return jsonify({"message": "Project created!"})

@app.route('/projects/<int:project_id>/tasks', methods=['GET', 'POST'])
@login_required
def assign_task(project_id):
    if current_user.role != "Admin":
        return "Forbidden"
    if request.method == 'POST':
        title = request.form['title']
        due_date = datetime.datetime.strptime(request.form['due_date'], "%Y-%m-%d").date()
        assigned_to = request.form['assigned_to']
        task = Task(title=title, due_date=due_date, assigned_to=assigned_to, project_id=project_id)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('dashboard_page'))
    users = User.query.all()
    return render_template('tasks.html', project_id=project_id, users=users)


@app.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if task.assigned_to != current_user.id and current_user.role != "Admin":
        return jsonify({"error": "Forbidden"}), 403
    data = request.json
    task.status = data['status']
    db.session.commit()
    return jsonify({"message": "Task updated!"})

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != "Admin":
        return redirect(url_for('user_dashboard'))
    users = User.query.filter_by(role="Member").all()
    projects = Project.query.all()
    tasks = Task.query.all()
    return render_template('dashboard_admin.html', users=users, projects=projects, tasks=tasks)

@app.route('/admin/create_task/<int:project_id>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_create_task(project_id, user_id):
    if current_user.role != "Admin":
        return redirect(url_for('dashboard_page'))
    if request.method == 'POST':
        title = request.form['title']
        due_date = request.form['due_date']
        new_task = Task(title=title, due_date=due_date, assigned_to=user_id, project_id=project_id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('create_task.html', project_id=project_id, user_id=user_id)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard():
    projects = Project.query.filter_by(created_by=current_user.id).all()
    tasks = Task.query.filter_by(assigned_to=current_user.id).all()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_project = Project(name=name, description=description, created_by=current_user.id)
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('user_dashboard'))
    return render_template('dashboard_user.html', projects=projects, tasks=tasks)

@app.route('/update_task/<int:task_id>/<string:new_status>', methods=['POST'])
@login_required
def update_task_status(task_id, new_status):
    task = Task.query.get_or_404(task_id)
    if current_user.role == "Admin" or task.assigned_to == current_user.id:
        task.status = new_status
        db.session.commit()
    return redirect(url_for('user_dashboard'))


# ------------------ TEMPLATE ROUTES ------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET'])
def signup_page():
    return render_template('signup.html')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/dashboard', methods=['GET'])
def dashboard_page():
    return render_template('dashboard_user.html')

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
