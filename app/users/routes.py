# app/users/routes.py  (replace existing)
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    StudentProfile, Enrollment, Course, Section, Exam, ExamResult, Payment, FeeStructure, UserRole
)
from datetime import datetime
import uuid

# use normal template loading (templates/...), don't force a relative path here
users_bp = Blueprint("users", __name__, url_prefix="/users")

def ensure_student():
    """Return a StudentProfile instance for current_user or None"""
    if not current_user or not current_user.is_authenticated:
        return None
    # Prefer explicit relationship
    student = getattr(current_user, "student_profile", None)
    if student:
        return student
    # fallback: StudentProfile.user_id -> users.id
    try:
        return StudentProfile.query.filter_by(user_id=current_user.id).first()
    except Exception:
        current_app.logger.exception("ensure_student() failed")
        return None

def require_active_student(raise_for_api=False):
    """
    Guard: only allow STUDENT role and active accounts.
    If raise_for_api=True (used by APIs) return JSON tuple (resp, code) when blocked.
    Otherwise return a redirect response (or None if allowed).
    """
    if not current_user.is_authenticated:
        if raise_for_api:
            return jsonify({"status":"error","message":"login_required"}), 401
        return redirect(url_for("auth.login"))

    # Admins should go to admin area
    if getattr(current_user, "is_admin", False):
        if raise_for_api:
            return jsonify({"status":"error","message":"admin_forbidden"}), 403
        flash("Admins do not have a student dashboard.", "warning")
        return redirect(url_for("admin.dashboard"))

    # Only allow users with STUDENT role (defensive)
    try:
        if getattr(current_user, "role", None) != UserRole.STUDENT:
            if raise_for_api:
                return jsonify({"status":"error","message":"students_only"}), 403
            flash("This area is for student accounts only.", "warning")
            return redirect(url_for("public.index"))
    except Exception:
        # if role is stored as string for some reason, allow access only if a student_profile exists
        if not getattr(current_user, "student_profile", None):
            if raise_for_api:
                return jsonify({"status":"error","message":"students_only"}), 403
            flash("This area is for student accounts only.", "warning")
            return redirect(url_for("public.index"))

    # account must be active/approved by admin
    if not getattr(current_user, "is_active", False):
        if raise_for_api:
            return jsonify({"status":"error","message":"account_inactive"}), 403
        flash("Your account is pending activation by admin.", "warning")
        return redirect(url_for("public.index"))

    return None

# ---- Pages ----

@users_bp.route("/dashboard")
@login_required
def dashboard():
    redirect_resp = require_active_student()
    if redirect_resp:
        return redirect_resp
    student = ensure_student()
    return render_template("users/dashboard.html", student=student)


@users_bp.route("/courses")
@login_required
def my_courses():
    redirect_resp = require_active_student()
    if redirect_resp:
        return redirect_resp
    student = ensure_student()
    return render_template("users/courses.html", student=student)


@users_bp.route("/exams")
@login_required
def my_exams():
    redirect_resp = require_active_student()
    if redirect_resp:
        return redirect_resp
    student = ensure_student()
    return render_template("users/exams.html", student=student)


@users_bp.route("/fees")
@login_required
def my_fees():
    redirect_resp = require_active_student()
    if redirect_resp:
        return redirect_resp
    student = ensure_student()
    return render_template("users/fees.html", student=student)


# ---- JSON APIs used by the pages ----

@users_bp.route("/api/overview")
@login_required
def api_overview():
    # API-style guard: return JSON error when blocked
    guard = require_active_student(raise_for_api=True)
    if guard:
        return guard

    student = ensure_student()
    if not student:
        return jsonify({"status":"error","message":"no_student_profile"}), 404

    # Build summary (defensive)
    try:
        enrollments = Enrollment.query.filter(Enrollment.student_id == student.id).all()
        enroll_count = len(enrollments)
    except Exception:
        current_app.logger.exception("api_overview enrollments")
        enroll_count = 0
        enrollments = []

    # upcoming exams (for student's sections)
    upcoming = []
    try:
        section_ids = [e.section_id for e in enrollments if getattr(e, "section_id", None)]
        if section_ids:
            upcoming_q = Exam.query.filter(Exam.section_id.in_(section_ids), Exam.exam_date >= datetime.utcnow()).order_by(Exam.exam_date.asc()).limit(6).all()
            for ex in upcoming_q:
                upcoming.append({
                    "id": ex.id,
                    "title": getattr(ex, "name", "") or getattr(ex, "title", ""),
                    "exam_date": ex.exam_date.isoformat() if ex.exam_date else None
                })
    except Exception:
        current_app.logger.exception("api_overview exams")
        upcoming = []

    # fees + payments
    total_fees = 0.0
    total_paid = 0.0
    fee_items = []
    try:
        dept = getattr(student, "department", None)
        if dept:
            fs = FeeStructure.query.filter(FeeStructure.applicable_to_department_id == dept.id).all()
            for f in fs:
                try:
                    amt = float(f.amount)
                except Exception:
                    amt = 0.0
                total_fees += amt
                fee_items.append({"id": f.id, "name": f.name, "amount": amt})
        pays = Payment.query.filter(Payment.student_id == student.id).order_by(Payment.paid_on.desc()).all()
        for p in pays:
            try:
                total_paid += float(p.amount)
            except Exception:
                pass
    except Exception:
        current_app.logger.exception("api_overview fees")

    remaining = max(0.0, total_fees - total_paid)
    return jsonify({
        "status":"ok",
        "data":{
            "enroll_count": enroll_count,
            "upcoming_exams": upcoming,
            "total_fees": total_fees,
            "total_paid": total_paid,
            "remaining": remaining,
            "fee_items": fee_items
        }
    })


@users_bp.route("/api/courses")
@login_required
def api_my_courses():
    guard = require_active_student(raise_for_api=True)
    if guard:
        return guard

    student = ensure_student()
    if not student:
        return jsonify({"status":"error","message":"no_student"}), 404

    try:
        enrolls = Enrollment.query.filter(Enrollment.student_id == student.id).all()
        out = []
        for en in enrolls:
            section = getattr(en, "section", None)
            course = getattr(section, "course", None) if section else None
            out.append({
                "enrollment_id": en.id,
                "section_id": getattr(section, "id", None),
                "section_code": getattr(section, "code", None),
                "course_id": getattr(course, "id", None),
                "course_title": getattr(course, "title", None),
                "status": getattr(en, "status", None)
            })
        return jsonify({"status":"ok","courses": out})
    except Exception:
        current_app.logger.exception("api_my_courses")
        return jsonify({"status":"error","courses":[]}), 500


@users_bp.route("/api/exams")
@login_required
def api_my_exams():
    guard = require_active_student(raise_for_api=True)
    if guard:
        return guard
    student = ensure_student()
    if not student:
        return jsonify({"status":"error","message":"no_student"}), 404
    try:
        enrolls = Enrollment.query.filter(Enrollment.student_id == student.id).all()
        section_ids = [e.section_id for e in enrolls if getattr(e,"section_id",None)]
        exams = []
        if section_ids:
            exams_q = Exam.query.filter(Exam.section_id.in_(section_ids)).order_by(Exam.exam_date.asc()).all()
            for ex in exams_q:
                result = ExamResult.query.filter_by(exam_id=ex.id).join(Enrollment, ExamResult.enrollment_id == Enrollment.id).filter(Enrollment.student_id == student.id).first()
                exams.append({
                    "id": ex.id,
                    "title": getattr(ex, "name", None) or getattr(ex, "title", None),
                    "exam_date": ex.exam_date.isoformat() if ex.exam_date else None,
                    "total_marks": ex.total_marks,
                    "result": {
                        "marks_obtained": getattr(result, "marks_obtained", None) if result else None,
                        "grade": getattr(result, "grade", None) if result else None
                    }
                })
        return jsonify({"status":"ok","exams":exams})
    except Exception:
        current_app.logger.exception("api_my_exams")
        return jsonify({"status":"error","exams": []}), 500


@users_bp.route("/api/fees")
@login_required
def api_my_fees():
    guard = require_active_student(raise_for_api=True)
    if guard:
        return guard
    student = ensure_student()
    if not student:
        return jsonify({"status":"error","message":"no_student"}), 404

    try:
        total_fees = 0.0
        fee_lines = []
        dept = getattr(student, "department", None)
        if dept:
            fs = FeeStructure.query.filter(FeeStructure.applicable_to_department_id == dept.id).all()
            for f in fs:
                try:
                    amt = float(f.amount)
                except Exception:
                    amt = 0.0
                fee_lines.append({"id": f.id, "name": f.name, "amount": amt})
                total_fees += amt

        total_paid = 0.0
        payments = Payment.query.filter(Payment.student_id == student.id).order_by(Payment.paid_on.desc()).all()
        pay_lines = []
        for p in payments:
            try:
                amt = float(p.amount)
            except Exception:
                amt = 0.0
            pay_lines.append({"id": p.id, "amount": amt, "method": getattr(p, "payment_method", None), "tx": getattr(p, "transaction_id", None), "created_at": p.paid_on.isoformat() if p.paid_on else None})
            total_paid += amt

        return jsonify({"status":"ok","fees": {"lines": fee_lines, "total_fees": total_fees, "total_paid": total_paid, "remaining": max(0.0, total_fees - total_paid), "payments": pay_lines}})
    except Exception:
        current_app.logger.exception("api_my_fees")
        return jsonify({"status":"error"}), 500


@users_bp.route("/api/fees/pay", methods=["POST"])
@login_required
def api_fees_pay():
    guard = require_active_student(raise_for_api=True)
    if guard:
        return guard
    student = ensure_student()
    if not student:
        return jsonify({"status":"error","message":"no_student"}), 404

    data = request.get_json() or {}
    amount = data.get("amount")
    method = data.get("method") or "mock"
    if amount is None:
        return jsonify({"status":"error","message":"amount_required"}), 400

    try:
        payment = Payment(
            student_id = student.id,
            fee_structure_id = None,
            amount = float(amount),
            payment_method = method,
            transaction_id = str(uuid.uuid4()),
            paid_on = datetime.utcnow(),
            status = "completed"
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify({"status":"ok","payment": {"id": payment.id, "amount": float(payment.amount)}})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("api_fees_pay")
        return jsonify({"status":"error","message":"server_error"}), 500
