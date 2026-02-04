# app/users/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import StudentProfile, Enrollment, Exam, ExamResult, Payment, Notice, Course
from datetime import date
from sqlalchemy import func

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