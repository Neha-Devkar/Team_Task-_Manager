from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import datetime, os

# ------------------ APP CONFIG ------------------
import os
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../frontend/templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../frontend/static')
)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "defaultsecret")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///project.db")
db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all()


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
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    due_date = db.Column(db.Date)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ HELPERS ------------------
def is_admin():
    return current_user.is_authenticated and current_user.role == "Admin"

# ------------------ AUTH ROUTES ------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form.get('role', 'Member')

        if User.query.filter_by(email=email).first():
            return redirect(url_for('login'))

        new_user = User(email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard' if user.role == "Admin" else 'user_dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ------------------ PROJECT ROUTES ------------------
@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if request.method == 'POST':
        if not is_admin():
            return "Forbidden", 403
        project = Project(
            name=request.form['name'],
            description=request.form['description'],
            created_by=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('projects.html')

# ------------------ TASK ROUTES ------------------
@app.route('/projects/<int:project_id>/tasks', methods=['GET', 'POST'])
@login_required
def assign_task(project_id):
    if not is_admin():
        return "Forbidden", 403
    user_id = request.args.get('user_id')  # ✅ get user_id from query string
    if request.method == 'POST':
        task = Task(
            title=request.form['title'],
            due_date=datetime.datetime.strptime(request.form['due_date'], "%Y-%m-%d").date(),
            assigned_to=int(user_id),   # ✅ assign directly to that user
            project_id=project_id
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('create_task.html', project_id=project_id)

@app.route('/tasks/<int:task_id>/update', methods=['POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assigned_to != current_user.id and not is_admin():
        return "Forbidden", 403
    task.status = request.form['status']
    db.session.commit()
    return redirect(url_for('user_dashboard'))

# ------------------ DASHBOARDS ------------------
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('user_dashboard'))
    return render_template(
        'dashboard_admin.html',
        users=User.query.filter_by(role="Member").all(),
        projects=Project.query.all(),
        tasks=Task.query.all()
    )

@app.route('/dashboard')
@login_required
def user_dashboard():
    return render_template(
        'dashboard_user.html',
        projects=Project.query.filter_by(created_by=current_user.id).all(),
        tasks=Task.query.filter_by(assigned_to=current_user.id).all()
    )

@app.route('/admin/user/<int:user_id>/dashboard')
@login_required
def admin_view_user_dashboard(user_id):
    if not is_admin():
        return redirect(url_for('user_dashboard'))
    user = User.query.get_or_404(user_id)
    return render_template(
        'dashboard_user.html',
        projects=Project.query.filter_by(created_by=user.id).all(),
        tasks=Task.query.filter_by(assigned_to=user.id).all(),
        user=user   # ✅ pass user object so template knows whose dashboard
    )

# ------------------ HOME ------------------
@app.route('/')
def home():
    return render_template('index.html')

# ------------------ MAIN ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
