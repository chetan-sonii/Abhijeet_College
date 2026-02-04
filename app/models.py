# app/models.py

from datetime import datetime
from enum import Enum

from flask import url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


# -------------------------
# Helper / Mixins
# -------------------------
class TimestampMixin(object):
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# -------------------------
# Enumerations
# -------------------------
class UserRole(Enum):
    ADMIN = "admin"
    STUDENT = "student"


class NoticeCategory(Enum):
    GENERAL = "General"
    ACADEMIC = "Academic"
    EXAM = "Exam"


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)

    # NEW: Avatar Field
    avatar = db.Column(db.String(200), nullable=False, default="default.png")

    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT, nullable=False)

    student_profile = db.relationship("StudentProfile", uselist=False, back_populates="user",
                                      cascade="all,delete-orphan")
    notices_posted = db.relationship("Notice", back_populates="posted_by")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

    @property
    def avatar_url(self):
        # Assumes images are in app/static/images/avatars/
        if not self.avatar:
            return url_for('static', filename='images/avatars/default.png')
        return url_for('static', filename=f'images/avatars/{self.avatar}')


# -------------------------
# Academic Structure
# -------------------------
class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    courses = db.relationship("Course", back_populates="department", cascade="all,delete-orphan")
    student_profiles = db.relationship("StudentProfile", back_populates="department")


class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, index=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=3)
    fee = db.Column(db.Numeric(10, 2), default=0.00)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)

    department = db.relationship("Department", back_populates="courses")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all,delete-orphan")
    exams = db.relationship("Exam", back_populates="course", cascade="all,delete-orphan")
    applications = db.relationship("Application", back_populates="program", lazy="dynamic")


# -------------------------
# Profiles
# -------------------------
class StudentProfile(TimestampMixin, db.Model):
    __tablename__ = "student_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    admission_no = db.Column(db.String(50), unique=True, index=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    year = db.Column(db.String(20), default="1st Year")

    user = db.relationship("User", back_populates="student_profile")
    department = db.relationship("Department", back_populates="student_profiles")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all,delete-orphan")
    payments = db.relationship("Payment", back_populates="student")


# -------------------------
# Enrollment & Results
# -------------------------
class Enrollment(TimestampMixin, db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    enrolled_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="active")

    student = db.relationship("StudentProfile", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),)


class Exam(TimestampMixin, db.Model):
    __tablename__ = "exams"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    exam_date = db.Column(db.Date)
    total_marks = db.Column(db.Integer)

    course = db.relationship("Course", back_populates="exams")
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
# Misc (Fees, Notices, etc)
# -------------------------
class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="completed")

    student = db.relationship("StudentProfile", back_populates="payments")


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


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(180), nullable=False)
    phone = db.Column(db.String(50))
    program_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    message = db.Column(db.Text)
    status = db.Column(db.String(32), default="new")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    program = db.relationship("Course", back_populates="applications")

    def short_message(self, length=140):
        if not self.message: return ""
        return (self.message[:length] + "…") if len(self.message) > length else self.message


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(180), nullable=False)
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)