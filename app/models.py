# app/models.py
from datetime import datetime
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
    STAFF = "staff"
    FACULTY = "faculty"
    STUDENT = "student"
    ACCOUNTANT = "accountant"
    LIBRARIAN = "librarian"

class NoticeCategory(Enum):
    GENERAL = "General"
    ACADEMIC = "Academic"
    EVENT = "Event"
    EXAM = "Exam"
    PLACEMENT = "Placement"

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
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT, nullable=False)

    # Relationships
    student_profile = db.relationship("StudentProfile", uselist=False, back_populates="user", cascade="all,delete-orphan")
    faculty_profile = db.relationship("FacultyProfile", uselist=False, back_populates="user", cascade="all,delete-orphan")
    notices_posted = db.relationship("Notice", back_populates="posted_by")
    events_created = db.relationship("Event", back_populates="created_by")

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
    student_profiles = db.relationship("StudentProfile", back_populates="department")
    faculty_profiles = db.relationship("FacultyProfile", back_populates="department")

class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, index=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=3)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    department = db.relationship("Department", back_populates="courses")
    sections = db.relationship("Section", back_populates="course", cascade="all,delete-orphan")
    applications = db.relationship("Application", back_populates="program", lazy="dynamic")

class Semester(TimestampMixin, db.Model):
    __tablename__ = "semesters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=False)

    sections = db.relationship("Section", back_populates="semester")

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
    # Consider removing email here if User.email is sufficient, otherwise keeping it as 'personal email'
    email = db.Column(db.String(180), nullable=False, index=True, default="student@example.com")
    gender = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    year = db.Column(db.String(20), nullable=True)

    user = db.relationship("User", back_populates="student_profile")
    department = db.relationship("Department", back_populates="student_profiles")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all,delete-orphan")
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
    department = db.relationship("Department", back_populates="faculty_profiles")
    # 'sections' relationship is defined in Section via secondary table

    @property
    def avatar(self):
        # Fallback logic if photo_url is not present (requires user to implement photo_url or generic)
        return url_for("static", filename="index/images/placeholder-face.png")

# -------------------------
# Association Table
# -------------------------
section_instructors = db.Table(
    "section_instructors",
    db.Column("section_id", db.Integer, db.ForeignKey("sections.id"), primary_key=True),
    db.Column("faculty_id", db.Integer, db.ForeignKey("faculty_profiles.id"), primary_key=True),
)

# -------------------------
# Section (Class)
# -------------------------
class Section(TimestampMixin, db.Model):
    __tablename__ = "sections"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    room = db.Column(db.String(64), nullable=True)
    schedule = db.Column(db.String(255), nullable=True)

    course = db.relationship("Course", back_populates="sections")
    semester = db.relationship("Semester", back_populates="sections")

    instructors = db.relationship("FacultyProfile", secondary=section_instructors, backref="sections")
    enrollments = db.relationship("Enrollment", back_populates="section", cascade="all,delete-orphan")
    exams = db.relationship("Exam", back_populates="section", cascade="all,delete-orphan")
    # REMOVED: assignments relationship (Model deleted)

# -------------------------
# Enrollment & Results
# -------------------------
class Enrollment(TimestampMixin, db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False, index=True)
    enrolled_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="active")
    grade_point = db.Column(db.Float, nullable=True)

    student = db.relationship("StudentProfile", back_populates="enrollments")
    section = db.relationship("Section", back_populates="enrollments")

    __table_args__ = (db.UniqueConstraint("student_id", "section_id", name="uq_enrollment_student_section"),)

class Exam(TimestampMixin, db.Model):
    __tablename__ = "exams"
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
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
# Fees
# -------------------------
class FeeStructure(TimestampMixin, db.Model):
    __tablename__ = "fee_structures"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
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
    payment_method = db.Column(db.String(64), nullable=True)
    transaction_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default="completed")

    student = db.relationship("StudentProfile", back_populates="payments")
    fee_structure = db.relationship("FeeStructure")

# -------------------------
# Communication & Misc
# -------------------------
class Notice(TimestampMixin, db.Model):
    __tablename__ = "notices"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(NoticeCategory), default=NoticeCategory.GENERAL, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    posted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    posted_on = db.Column(db.DateTime, default=datetime.utcnow)

    posted_by = db.relationship("User", back_populates="notices_posted")

class Event(TimestampMixin, db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime, nullable=True)
    end_datetime = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_by = db.relationship("User", back_populates="events_created")

class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(180), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=True)
    program_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="new", index=True)
    admin_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    program = db.relationship("Course", back_populates="applications")

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