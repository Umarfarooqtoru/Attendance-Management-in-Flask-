# Employee Attendance Management System

A web-based attendance management system built with Flask that allows employees to mark their attendance and administrators to manage employee records, track attendance, and handle overtime approvals.

## Features

- **Employee Management**
  - Add new employees with unique employee IDs
  - View list of all employees
  - Track individual employee attendance records

- **Attendance Tracking**
  - Simple punch in/out system for employees
  - Automatic calculation of work hours
  - Overtime tracking and approval system
  - Support for marking leaves
  - Monthly attendance view with calendar display

- **Attendance Status Types**
  - Present (P)
  - Absent (A)
  - Leave (L)

- **Admin Features**
  - Secure admin login system
  - Monthly attendance overview
  - Overtime approval/rejection
  - Individual employee attendance history
  - Mark employee leaves

## Technology Stack

- Python 3.x
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Werkzeug 3.0.1
- SQLite Database
- Bootstrap 5.1.3
- HTML/CSS/JavaScript

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - Unix/MacOS:
     ```
     source venv/bin/activate
     ```
4. Install required packages:
   ```
   pip install -r requirements.txt
   ```
5. Initialize the database:
   ```
   python init_db.py
   ```
6. Run the application:
   ```
   python app.py
   ```

## Default Admin Credentials

- Username: admin
- Password: admin123

## Usage

1. **Employee Attendance**
   - Visit the home page
   - Enter employee ID
   - Click "Punch In/Out" to mark attendance

2. **Admin Tasks**
   - Log in using admin credentials
   - Add/view employees
   - View attendance records
   - Approve/reject overtime
   - View monthly attendance
   - Mark employee leaves

3. **Monthly Attendance View**
   - Select month and year
   - View color-coded attendance status
   - Mark leaves for absent days
   - Track attendance patterns

## Working Hours

- Standard working hours: 8 hours per day
- System automatically calculates:
  - Regular hours
  - Overtime (more than 8 hours)
  - Short hours (less than 8 hours)
