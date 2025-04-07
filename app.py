from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    attendances = db.relationship('Attendance', backref='employee', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    entry_time = db.Column(db.DateTime, nullable=True)
    exit_time = db.Column(db.DateTime, nullable=True)
    overtime_approved = db.Column(db.Boolean, nullable=True)
    overtime_minutes = db.Column(db.Integer, default=0)
    deduction_minutes = db.Column(db.Integer, default=0)
    status = db.Column(db.String(1), default='A')  # 'A' for Absent, 'L' for Leave, 'P' for Present

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def calculate_work_hours(entry_time, exit_time):
    if not exit_time:
        return 0, 0, 0
    
    total_minutes = int((exit_time - entry_time).total_seconds() / 60)
    standard_minutes = 8 * 60  # 8 hours in minutes
    
    if total_minutes > standard_minutes:
        overtime = total_minutes - standard_minutes
        deduction = 0
    else:
        overtime = 0
        deduction = standard_minutes - total_minutes
        
    return total_minutes / 60, overtime, deduction

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        
        if not employee:
            flash('Invalid Employee ID')
            return redirect(url_for('index'))
        
        today = datetime.now().date()
        existing_attendance = Attendance.query.filter_by(
            employee_id=employee.id,
            date=today
        ).first()
        
        if not existing_attendance:
            # Mark entry
            new_attendance = Attendance(
                employee_id=employee.id,
                date=today,
                entry_time=datetime.now()
            )
            db.session.add(new_attendance)
            message = f'Entry time marked for {employee.name}'
        elif not existing_attendance.exit_time:
            # Mark exit
            existing_attendance.exit_time = datetime.now()
            # Calculate overtime or deduction
            total_hours, overtime_minutes, deduction_minutes = calculate_work_hours(
                existing_attendance.entry_time, 
                existing_attendance.exit_time
            )
            existing_attendance.overtime_minutes = overtime_minutes
            existing_attendance.deduction_minutes = deduction_minutes
            message = f'Exit time marked for {employee.name}'
            if overtime_minutes > 0:
                message += f'. {overtime_minutes} minutes of overtime pending approval.'
            elif deduction_minutes > 0:
                message += f'. {deduction_minutes} minutes short of standard hours.'
        else:
            message = f'Attendance already marked for today for {employee.name}'
        
        db.session.commit()
        flash(message)
        return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    employees = Employee.query.all()
    attendances = Attendance.query.all()
    return render_template('admin_dashboard.html', employees=employees, attendances=attendances)

@app.route('/admin/attendance/<employee_id>')
@login_required
def view_attendance(employee_id):
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        flash('Employee not found')
        return redirect(url_for('admin_dashboard'))
    
    attendances = Attendance.query.filter_by(employee_id=employee.id).all()
    return render_template('view_attendance.html', employee=employee, attendances=attendances)

@app.route('/admin/add_employee', methods=['POST'])
@login_required
def add_employee():
    name = request.form.get('name')
    employee_id = request.form.get('employee_id')
    
    if Employee.query.filter_by(employee_id=employee_id).first():
        flash('Employee ID already exists')
        return redirect(url_for('admin_dashboard'))
    
    new_employee = Employee(name=name, employee_id=employee_id)
    db.session.add(new_employee)
    db.session.commit()
    flash('Employee added successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_overtime/<int:attendance_id>', methods=['POST'])
@login_required
def approve_overtime(attendance_id):
    attendance = Attendance.query.get_or_404(attendance_id)
    action = request.form.get('action')
    
    if action == 'approve':
        attendance.overtime_approved = True
        message = 'Overtime approved'
    elif action == 'reject':
        attendance.overtime_approved = False
        attendance.overtime_minutes = 0
        message = 'Overtime rejected'
    
    db.session.commit()
    flash(message)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin/monthly_attendance', methods=['GET', 'POST'])
@login_required
def monthly_attendance():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    selected_month = datetime.now().month
    selected_year = datetime.now().year
    
    if request.method == 'POST':
        selected_month = int(request.form.get('month', selected_month))
        selected_year = int(request.form.get('year', selected_year))
    
    # Get all employees
    employees = Employee.query.all()
    
    # Get the number of days in the selected month
    num_days = calendar.monthrange(selected_year, selected_month)[1]
    
    # Get all dates in the month
    start_date = datetime(selected_year, selected_month, 1).date()
    end_date = datetime(selected_year, selected_month, num_days).date()
    
    # Get all attendance records for the month
    attendances = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()
    
    # Create attendance dictionary
    attendance_dict = {}
    for employee in employees:
        attendance_dict[employee.id] = {
            'name': employee.name,
            'employee_id': employee.employee_id,
            'days': {}
        }
        # Initialize all days as 'A' (Absent)
        for day in range(1, num_days + 1):
            date = datetime(selected_year, selected_month, day).date()
            attendance_dict[employee.id]['days'][day] = 'A'
    
    # Update attendance status
    for attendance in attendances:
        day = attendance.date.day
        if attendance.entry_time:
            attendance_dict[attendance.employee_id]['days'][day] = 'P'
        if attendance.status == 'L':
            attendance_dict[attendance.employee_id]['days'][day] = 'L'
    
    return render_template('monthly_attendance.html',
                         attendance_dict=attendance_dict,
                         month=selected_month,
                         year=selected_year,
                         num_days=num_days,
                         current_month=datetime.now().month,
                         current_year=datetime.now().year)

@app.route('/admin/mark_leave/<employee_id>/<date>', methods=['POST'])
@login_required
def mark_leave(employee_id, date):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    try:
        date = datetime.strptime(date, '%Y-%m-%d').date()
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        
        if not employee:
            flash('Employee not found')
            return redirect(url_for('monthly_attendance'))
        
        attendance = Attendance.query.filter_by(
            employee_id=employee.id,
            date=date
        ).first()
        
        if not attendance:
            attendance = Attendance(
                employee_id=employee.id,
                date=date,
                status='L'
            )
            db.session.add(attendance)
        else:
            attendance.status = 'L'
            attendance.entry_time = None
            attendance.exit_time = None
        
        db.session.commit()
        flash(f'Leave marked for {employee.name} on {date}')
    except Exception as e:
        flash('Error marking leave')
    
    return redirect(url_for('monthly_attendance'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)