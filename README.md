# Team Task Manager

A project management web application built with **Flask, SQLAlchemy, and Flask-Login**.  
This app helps teams organize projects, assign tasks, and track progress in real time.

## Features
- User authentication (Signup & Login)
- Role-based access (Admin vs Member)
- Admin dashboard for project and task management
- Task assignment with deadlines
- User dashboard for tracking and updating tasks
- Real-time status updates reflected across dashboards

##  Project Structure

##  Pages Overview

### 1. Welcome Page
- **Content:** App title, introduction, buttons for Signup and Login.  
- **Purpose:** Entry point guiding users to register or log in.

### 2. Signup Page
- **Content:** Form with Email, Password, Role.  
- **Purpose:** Allows new users to create accounts. Email ensures uniqueness, password secures the account, role defines access level.

### 3. Login Page
- **Content:** Email + Password form, Login button.  
- **Purpose:** Authenticates users. Redirects Admins to Admin Dashboard, Members to User Dashboard.

### 4. Admin Dashboard
- **Content:** Navigation bar, project list, employee list, task overview, buttons like “Assign Task.”  
- **Purpose:** Central hub for admins to manage projects, assign tasks, and monitor progress.

### 5. Assign Task Page
- **Content:** Form with Task Title, Description, Due Date, Assign To (user), Submit button.  
- **Purpose:** Enables admins to distribute work clearly and link tasks to specific users.

### 6. User Dashboard
- **Content:** List of assigned tasks with status indicators (Pending, In Progress, Done), buttons to update status.  
- **Purpose:** Workspace for users to track and update their tasks. Status changes reflect back to the admin dashboard.

## Tech Stack
- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Frontend:** HTML, CSS, Bootstrap
- **Database:** SQLite (local), PostgreSQL (production on Render)
- **Deployment:** Render


##  Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/NehaRajebhauDevkar/project-management-app.git
   cd project-management-app
