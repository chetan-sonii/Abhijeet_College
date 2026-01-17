# app/models.py
from datetime import datetime, date, time
from enum import Enum
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.extensions import db

# -------------------------
# Helper / mixins
# -------------------------
class TimestampMixin(object):
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

# -------------------------
# Enumerations
# -------------------------
class UserRole(Enum):
    ADMIN = "admin"
    STAFF = "staff"        # non-teaching administrative staff
    FACULTY = "faculty"
    STUDENT = "student"
    ACCOUNTANT = "accountant"
    LIBRARIAN = "librarian"

class AttendanceStatus(Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

# -------------------------
# Core user model
# -------------------------
class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)  # NEW: account approved by admin
    requested_at = db.Column(db.DateTime, default=datetime.utcnow,
                             nullable=False)  # optional: when registration requested
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT, nullable=False)

    # One-to-one optional profiles
    student_profile = db.relationship("StudentProfile", uselist=False, back_populates="user", cascade="all,delete-orphan")
    faculty_profile = db.relationship("FacultyProfile", uselist=False, back_populates="user", cascade="all,delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

# -------------------------
# Academic structure
# -------------------------
class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    courses = db.relationship("Course", back_populates="department", cascade="all,delete-orphan")

class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, index=True, nullable=False)  # e.g., CS101
    title = db.Column(db.String(255), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=3)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    department = db.relationship("Department", back_populates="courses")
    sections = db.relationship("Section", back_populates="course", cascade="all,delete-orphan")

# Semesters / academic terms
class Semester(TimestampMixin, db.Model):
    __tablename__ = "semesters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)    # "Fall 2025"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=False)

    sections = db.relationship("Section", back_populates="semester")

# A Section (or class) is a particular offering of a course in a semester
class Section(TimestampMixin, db.Model):
    __tablename__ = "sections"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=True)  # ex: "CS101-A"
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    room = db.Column(db.String(64), nullable=True)
    schedule = db.Column(db.String(255), nullable=True)  # free-form, or store structured schedule separately

    course = db.relationship("Course", back_populates="sections")
    semester = db.relationship("Semester", back_populates="sections")

    # Many-to-many relationships:
    instructors = db.relationship("FacultyProfile", secondary="section_instructors", back_populates="sections")
    enrollments = db.relationship("Enrollment", back_populates="section", cascade="all,delete-orphan")
    assignments = db.relationship("Assignment", back_populates="section", cascade="all,delete-orphan")
    exams = db.relationship("Exam", back_populates="section", cascade="all,delete-orphan")

# association table for section instructors
section_instructors = db.Table(
    "section_instructors",
    db.Column("section_id", db.Integer, db.ForeignKey("sections.id"), primary_key=True),
    db.Column("faculty_id", db.Integer, db.ForeignKey("faculty_profiles.id"), primary_key=True),
)

# -------------------------
# Profiles
# -------------------------
class StudentProfile(TimestampMixin, db.Model):
    __tablename__ = "student_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    admission_no = db.Column(db.String(50), unique=True, index=True, nullable=False)
    roll_no = db.Column(db.String(50), unique=True, index=True, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(180), nullable=False, index=True, default="student@example.com")
    gender = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    year = db.Column(db.String(20), nullable=True)  # e.g., "1st Year", "2nd Year"

    user = db.relationship("User", back_populates="student_profile")
    department = db.relationship("Department")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all,delete-orphan")
    hostel_allocations = db.relationship("HostelAllocation", back_populates="student", cascade="all,delete-orphan")
    payments = db.relationship("Payment", back_populates="student")

class FacultyProfile(TimestampMixin, db.Model):
    __tablename__ = "faculty_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = db.Column(db.String(80), unique=True, nullable=False)
    designation = db.Column(db.String(120), nullable=True)

    bio = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    user = db.relationship("User", back_populates="faculty_profile")
    department = db.relationship("Department")
    sections = db.relationship("Section", secondary=section_instructors, back_populates="instructors")

    @property
    def avatar(self):
        return self.photo_url or url_for(
            "static",
            filename="index/images/placeholder-face.png"
        )

# -------------------------
# Enrollment & academic records
# -------------------------
class Enrollment(TimestampMixin, db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False, index=True)
    enrolled_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="active")  # active, dropped, completed
    grade_point = db.Column(db.Float, nullable=True)      # optional cumulative for section

    student = db.relationship("StudentProfile", back_populates="enrollments")
    section = db.relationship("Section", back_populates="enrollments")

    __table_args__ = (db.UniqueConstraint("student_id", "section_id", name="uq_enrollment_student_section"),)

# Attendance per session (could be daily or per lecture)
class Attendance(TimestampMixin, db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT)
    remarks = db.Column(db.String(255), nullable=True)

    enrollment = db.relationship("Enrollment", backref=db.backref("attendance_records", cascade="all,delete-orphan"))

    __table_args__ = (db.UniqueConstraint("enrollment_id", "date", name="uq_attendance_enrollment_date"),)

# Assignments and submissions
class Assignment(TimestampMixin, db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    posted_on = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    total_marks = db.Column(db.Integer, nullable=True)

    section = db.relationship("Section", back_populates="assignments")
    submissions = db.relationship("AssignmentSubmission", back_populates="assignment", cascade="all,delete-orphan")

class AssignmentSubmission(TimestampMixin, db.Model):
    __tablename__ = "assignment_submissions"
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False, index=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=False, index=True)
    submitted_on = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(512), nullable=True)   # store path to uploaded file
    marks_obtained = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text)

    assignment = db.relationship("Assignment", back_populates="submissions")
    enrollment = db.relationship("Enrollment")

    __table_args__ = (db.UniqueConstraint("assignment_id", "enrollment_id", name="uq_assignment_enrollment"),)

# Exams + results
class Exam(TimestampMixin, db.Model):
    __tablename__ = "exams"
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # "Midterm", "Final"
    exam_date = db.Column(db.Date)
    total_marks = db.Column(db.Integer)

    section = db.relationship("Section", back_populates="exams")
    results = db.relationship("ExamResult", back_populates="exam", cascade="all,delete-orphan")

class ExamResult(TimestampMixin, db.Model):
    __tablename__ = "exam_results"
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False, index=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollments.id"), nullable=False, index=True)
    marks_obtained = db.Column(db.Float, nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    remarks = db.Column(db.Text)

    exam = db.relationship("Exam", back_populates="results")
    enrollment = db.relationship("Enrollment")

    __table_args__ = (db.UniqueConstraint("exam_id", "enrollment_id", name="uq_exam_enrollment"),)

# -------------------------
# Fees & payments
# -------------------------
class FeeStructure(TimestampMixin, db.Model):
    __tablename__ = "fee_structures"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)  # "Tuition - 1st Year"
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    applicable_to_department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    department = db.relationship("Department")

class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False, index=True)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey("fee_structures.id"), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_on = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(64), nullable=True)  # card, upi, cash
    transaction_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default="completed")  # completed / pending / failed

    student = db.relationship("StudentProfile", back_populates="payments")
    fee_structure = db.relationship("FeeStructure")

# -------------------------
# Library
# -------------------------
class Book(TimestampMixin, db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(32), unique=True, index=True, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=True)
    publisher = db.Column(db.String(255), nullable=True)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    location = db.Column(db.String(120), nullable=True)

    borrow_records = db.relationship("BorrowRecord", back_populates="book", cascade="all,delete-orphan")

class BorrowRecord(TimestampMixin, db.Model):
    __tablename__ = "borrow_records"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    borrowed_on = db.Column(db.DateTime, default=datetime.utcnow)
    due_on = db.Column(db.DateTime)
    returned_on = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default="borrowed")  # borrowed / returned / lost / renewed

    book = db.relationship("Book", back_populates="borrow_records")
    student = db.relationship("StudentProfile")

# -------------------------
# Hostel / Housing
# -------------------------
class Hostel(TimestampMixin, db.Model):
    __tablename__ = "hostels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=True)

    rooms = db.relationship("HostelRoom", back_populates="hostel", cascade="all,delete-orphan")

class HostelRoom(TimestampMixin, db.Model):
    __tablename__ = "hostel_rooms"
    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id"), nullable=False)
    room_no = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, default=1)

    hostel = db.relationship("Hostel", back_populates="rooms")
    allocations = db.relationship("HostelAllocation", back_populates="room", cascade="all,delete-orphan")

class HostelAllocation(TimestampMixin, db.Model):
    __tablename__ = "hostel_allocations"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("hostel_rooms.id"), nullable=False)
    allocated_on = db.Column(db.DateTime, default=datetime.utcnow)
    vacated_on = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default="active")  # active / vacated

    student = db.relationship("StudentProfile", back_populates="hostel_allocations")
    room = db.relationship("HostelRoom", back_populates="allocations")

# -------------------------
# Transport
# -------------------------
class Vehicle(TimestampMixin, db.Model):
    __tablename__ = "vehicles"
    id = db.Column(db.Integer, primary_key=True)
    registration_no = db.Column(db.String(64), unique=True)
    capacity = db.Column(db.Integer)
    driver_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)

class Route(TimestampMixin, db.Model):
    __tablename__ = "routes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    stops = db.Column(db.Text)  # JSON or comma-separated stops


# ... existing imports ...

# 1. Add this Enum with your other Enums
class NoticeCategory(Enum):
    GENERAL = "General"
    ACADEMIC = "Academic"
    EVENT = "Event"
    EXAM = "Exam"
    PLACEMENT = "Placement"


# ... (other models) ...

# 2. Update the Notice model
class Notice(TimestampMixin, db.Model):
    __tablename__ = "notices"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)

    # NEW FIELDS
    category = db.Column(db.Enum(NoticeCategory), default=NoticeCategory.GENERAL, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)  # Pinned notices show first

    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    posted_on = db.Column(db.DateTime, default=datetime.utcnow)

    posted_by = db.relationship("User")

class Event(TimestampMixin, db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime, nullable=True)
    end_datetime = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_by = db.relationship("User")

# Simple audit/log table
class AuditLog(TimestampMixin, db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)
    meta = db.Column(db.Text, nullable=True)

    user = db.relationship("User")

class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(180), nullable=False, index=True )
    phone = db.Column(db.String(50), nullable=True)
    program_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    message = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(32), nullable=False, default="new", index=True)  # new, reviewed, accepted, rejected
    admin_note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # relationships
    program = db.relationship("Course", backref=db.backref("applications", lazy="dynamic"))

    def short_message(self, length=140):
        if not self.message:
            return ""
        return (self.message[:length] + "…") if len(self.message) > length else self.message

class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(180), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)