# app/users/routes.py
import os
import secrets
from tkinter import Image
from PIL import Image

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import StudentProfile, Enrollment, Exam, ExamResult, Payment, Notice, Course
from datetime import date
from sqlalchemy import func

from app.users.forms import EditProfileForm

users_bp = Blueprint("users", __name__, template_folder="../../templates/users", url_prefix="/student")


def get_student_profile():
    """Helper to ensure user has a student profile"""
    if not current_user.student_profile:
        # Fallback if approved but no profile (shouldn't happen with new logic)
        return None
    return current_user.student_profile


@users_bp.route("/dashboard")
@login_required
def dashboard():
    profile = get_student_profile()
    if not profile:
        return render_template("users/no_profile.html")

    # 1. Stats
    enrolled_count = len(profile.enrollments)

    # Calculate Fees
    total_fee = sum(e.course.fee for e in profile.enrollments)
    total_paid = sum(p.amount for p in profile.payments)
    balance = float(total_fee) - float(total_paid)

    # 2. Upcoming Exams (Filter exams for enrolled courses where date >= today)
    enrolled_course_ids = [e.course_id for e in profile.enrollments]
    upcoming_exams = Exam.query.filter(
        Exam.course_id.in_(enrolled_course_ids),
        Exam.exam_date >= date.today()
    ).order_by(Exam.exam_date).limit(5).all()

    # 3. Recent Notices
    notices = Notice.query.order_by(Notice.posted_on.desc()).limit(3).all()

    return render_template(
        "users/dashboard.html",
        profile=profile,
        stats={
            "courses": enrolled_count,
            "balance": balance,
            "upcoming_exams": len(upcoming_exams)
        },
        upcoming_exams=upcoming_exams,
        notices=notices
    )


@users_bp.route("/courses")
@login_required
def my_courses():
    profile = current_user.student_profile
    if not profile: return redirect(url_for("users.dashboard"))

    # 1. Get IDs of courses user is already enrolled in (or pending)
    my_course_ids = [e.course_id for e in profile.enrollments]

    # 2. Fetch courses the student is NOT in (for the "Browse" modal)
    available_courses = Course.query.filter(Course.id.notin_(my_course_ids)).order_by(Course.title).all()

    return render_template(
        "users/courses.html",
        enrollments=profile.enrollments,
        available_courses=available_courses
    )


@users_bp.route("/courses/enroll/<int:course_id>", methods=["POST"])
@login_required
def enroll_request(course_id):
    profile = current_user.student_profile
    if not profile: return redirect(url_for("users.dashboard"))

    # Check if already enrolled
    exists = Enrollment.query.filter_by(student_id=profile.id, course_id=course_id).first()
    if exists:
        flash("You have already applied for or are enrolled in this course.", "warning")
    else:
        # Create PENDING enrollment
        enrollment = Enrollment(
            student_id=profile.id,
            course_id=course_id,
            status="pending"  # Admin must approve this
        )
        db.session.add(enrollment)
        db.session.commit()
        flash("Enrollment requested! Waiting for admin approval.", "success")

    return redirect(url_for("users.my_courses"))


@users_bp.route("/exams")
@login_required
def my_exams():
    profile = get_student_profile()
    if not profile: return redirect(url_for("users.dashboard"))

    enrolled_course_ids = [e.course_id for e in profile.enrollments]

    # Fetch all relevant exams
    all_exams = Exam.query.filter(Exam.course_id.in_(enrolled_course_ids)).order_by(Exam.exam_date.desc()).all()

    # Separate into Upcoming vs Past/Results
    upcoming = []
    results = []

    today = date.today()

    for exam in all_exams:
        if exam.exam_date and exam.exam_date >= today:
            upcoming.append(exam)
        else:
            # Check if result exists for this student
            # We need the enrollment_id for this specific course
            enrollment = next((e for e in profile.enrollments if e.course_id == exam.course_id), None)
            user_result = None
            if enrollment:
                user_result = ExamResult.query.filter_by(exam_id=exam.id, enrollment_id=enrollment.id).first()

            results.append({
                "exam": exam,
                "score": user_result.marks_obtained if user_result else None,
                "grade": user_result.grade if user_result else "-",
                "remarks": user_result.remarks if user_result else ""
            })

    return render_template("users/exams.html", upcoming=upcoming, results=results)


@users_bp.route("/fees")
@login_required
def my_fees():
    profile = get_student_profile()
    if not profile: return redirect(url_for("users.dashboard"))

    # Calculation
    total_fee = sum(e.course.fee for e in profile.enrollments)
    total_paid = sum(p.amount for p in profile.payments)

    # Logic to handle overpayment
    raw_balance = float(total_fee) - float(total_paid)
    if raw_balance > 0:
        balance_due = raw_balance
        credit = 0.0
    else:
        balance_due = 0.0
        credit = abs(raw_balance)

    # History
    history = profile.payments

    return render_template("users/fees.html",
                           total_fee=total_fee,
                           total_paid=total_paid,
                           balance_due=balance_due,
                           credit=credit,
                           history=history)


def save_picture(form_picture):
    """Save profile picture with a random hex name."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext

    # FIX: Point strictly to 'static/images/avatars'
    folder_path = os.path.join(current_app.root_path, 'static/images/avatars')

    # Create directory if it doesn't exist to prevent errors
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    picture_path = os.path.join(folder_path, picture_fn)

    # Resize to 150x150 to save space
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@users_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        # 1. Update User (Auth) Data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data

        # 2. Handle Image Upload
        if form.avatar.data:
            try:
                picture_file = save_picture(form.avatar.data)
                current_user.avatar = picture_file  # Save filename to DB
            except Exception as e:
                flash(f"Error saving image: {str(e)}", "danger")
                return redirect(url_for('users.profile'))

        # 3. Update Student Profile Data
        if current_user.student_profile:
            current_user.student_profile.date_of_birth = form.date_of_birth.data
            current_user.student_profile.gender = form.gender.data
            current_user.student_profile.address = form.address.data

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('users.profile'))

    elif request.method == 'GET':
        # Pre-populate form
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone

        if current_user.student_profile:
            form.date_of_birth.data = current_user.student_profile.date_of_birth
            form.gender.data = current_user.student_profile.gender
            form.address.data = current_user.student_profile.address

    return render_template('users/profile.html', title='Edit Profile', form=form)