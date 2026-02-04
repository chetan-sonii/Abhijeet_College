# app/admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models import (
    Application, Course, User, ContactMessage, StudentProfile,
    Department, Notice, Payment, Exam, ExamResult, Enrollment, NoticeCategory
)
from app.extensions import db
from sqlalchemy import func, or_
from datetime import datetime
from sqlalchemy.orm import joinedload

admin_bp = Blueprint("admin", __name__, template_folder="../../templates/admin", url_prefix="/admin")


def admin_guard():
    if not (current_user and getattr(current_user, "is_admin", False)):
        flash("Administrator access required.", "warning")
        return redirect(url_for("auth.login"))
    return None


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin: return admin_guard()
    try:
        stats = {
            "total_apps": db.session.query(func.count(Application.id)).scalar() or 0,
            "new_apps": db.session.query(func.count(Application.id)).filter(Application.status == "new").scalar() or 0,
            "total_contacts": db.session.query(func.count(ContactMessage.id)).scalar() or 0,
            "unread_contacts": db.session.query(func.count(ContactMessage.id)).filter(
                ContactMessage.is_read == False).scalar() or 0,
            "pending_users": db.session.query(func.count(User.id)).filter(User.is_active == False,
                                                                          User.is_admin == False).scalar() or 0,
            "total_users": db.session.query(func.count(User.id)).scalar() or 0,
            "courses": db.session.query(func.count(Course.id)).scalar() or 0,
            "students": db.session.query(func.count(StudentProfile.id)).scalar() or 0,

        }
    except Exception:
        stats = {k: 0 for k in
                 ["total_apps", "new_apps", "total_contacts", "unread_contacts", "pending_users", "total_users",
                  "courses", "students", "faculty"]}

    recent_apps = Application.query.order_by(Application.created_at.desc()).limit(6).all()
    recent_contacts = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(6).all()
    recent_users = User.query.filter(User.is_active == False, User.is_admin == False).order_by(
        User.requested_at.desc()).limit(6).all()

    return render_template("admin/dashboard.html", stats=stats, recent_apps=recent_apps,
                           recent_contacts=recent_contacts, recent_users=recent_users)



# --------------------
# APPLICATIONS & CONTACTS (Unified)
# --------------------
@admin_bp.route("/apps")
@login_required
def apps_page():
    if not current_user.is_admin: return admin_guard()

    # Combined list logic
    apps = Application.query.order_by(Application.created_at.desc()).limit(50).all()
    contacts = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(50).all()

    combined = []
    for a in apps:
        combined.append({
            "id": f"app-{a.id}", "type": "application", "pk": a.id,
            "name": a.name, "email": a.email, "summary": a.short_message(140),
            "status": a.status, "created_at": a.created_at,"phone": a.phone,
        })
    for c in contacts:
        combined.append({
            "id": f"contact-{c.id}", "type": "contact", "pk": c.id,
            "name": c.name, "email": c.email,
            "summary": (c.message[:140] + "…") if c.message else "",
            "status": ("read" if c.is_read else "new"), "created_at": c.created_at
        })

    combined = sorted(combined, key=lambda r: r["created_at"] or datetime.min, reverse=True)
    return render_template("admin/apps.html", items=combined)


# --- APIs for Apps.js ---
@admin_bp.route("/api/apps")
@login_required
def api_apps():
    if not current_user.is_admin: return jsonify({"status": "error"}), 403
    q = request.args.get("q", "").strip()
    limit = 80

    apps_q = Application.query
    contacts_q = ContactMessage.query

    if q:
        term = f"%{q}%"
        apps_q = apps_q.filter(or_(Application.name.ilike(term), Application.email.ilike(term)))
        contacts_q = contacts_q.filter(or_(ContactMessage.name.ilike(term), ContactMessage.email.ilike(term)))

    apps = apps_q.order_by(Application.created_at.desc()).limit(limit).all()
    contacts = contacts_q.order_by(ContactMessage.created_at.desc()).limit(limit).all()

    out = []
    for a in apps:
        out.append(
            {"id": f"app-{a.id}", "type": "application", "name": a.name, "email": a.email, "summary": a.short_message(),
             "status": a.status, "created_at": a.created_at.isoformat()})
    for c in contacts:
        out.append(
            {"id": f"contact-{c.id}", "type": "contact", "name": c.name, "email": c.email, "summary": c.message[:100],
             "status": "read" if c.is_read else "new", "created_at": c.created_at.isoformat()})

    return jsonify({"status": "ok", "items": sorted(out, key=lambda x: x['created_at'], reverse=True)})


@admin_bp.route("/api/apps/<string:item_id>")
@login_required
def api_get_app(item_id):
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    if item_id.startswith("app-"):
        a = Application.query.get(int(item_id.split("-")[1]))
        if not a: return jsonify({"status": "error"}), 404
        return jsonify({
            "status": "ok", "type": "application",
            "data": {"id": a.id, "name": a.name, "email": a.email, "phone": a.phone,
                     "program": a.program.title if a.program else "-", "message": a.message, "status": a.status,
                     "created_at": a.created_at.isoformat()}
        })
    elif item_id.startswith("contact-"):
        c = ContactMessage.query.get(int(item_id.split("-")[1]))
        if not c: return jsonify({"status": "error"}), 404
        return jsonify({
            "status": "ok", "type": "contact",
            "data": {"id": c.id, "name": c.name, "email": c.email, "subject": c.subject, "message": c.message,
                     "is_read": c.is_read, "created_at": c.created_at.isoformat()}
        })
    return jsonify({"status": "error"}), 400


@admin_bp.route("/api/apps/<string:item_id>/mark", methods=["POST"])
@login_required
def api_mark_app(item_id):
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    if item_id.startswith("app-"):
        a = Application.query.get(int(item_id.split("-")[1]))
        a.status = "accepted" if a.status == "new" else "new"

        db.session.commit()
        return jsonify({"status": "ok", "new_status": a.status})
    elif item_id.startswith("contact-"):
        c = ContactMessage.query.get(int(item_id.split("-")[1]))
        c.is_read = not c.is_read
        db.session.commit()
        return jsonify({"status": "ok", "is_read": c.is_read})
    return jsonify({"status": "error"}), 400


@admin_bp.route("/api/apps/<string:item_id>/delete", methods=["POST"])
@login_required
def api_delete_app(item_id):
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    if item_id.startswith("app-"):
        db.session.delete(Application.query.get(int(item_id.split("-")[1])))
    elif item_id.startswith("contact-"):
        db.session.delete(ContactMessage.query.get(int(item_id.split("-")[1])))
    db.session.commit()
    return jsonify({"status": "ok"})


# --------------------------
# Pending Enrollments (AJAX)
# --------------------------
@admin_bp.route("/api/users/<int:user_id>/reject", methods=["POST"])
@login_required
def api_reject_user(user_id):
    if not current_user.is_admin:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        user = User.query.get_or_404(user_id)
        email = user.email
        db.session.delete(user)
        db.session.commit()
        return jsonify({"status": "success", "message": f"User {email} rejected", "id": user_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------
# COURSES MANAGEMENT (AJAX)
# --------------------------
@admin_bp.route("/courses")
@login_required
def courses_page():
    if not current_user.is_admin: return admin_guard()
    courses = Course.query.options(joinedload(Course.department)).order_by(Course.code).all()
    departments = Department.query.all()
    return render_template("admin/courses.html", courses=courses, departments=departments)


@admin_bp.route("/api/courses", methods=["POST"])
@login_required
def api_course_create():
    if not current_user.is_admin: return jsonify({"error": "Auth required"}), 403

    data = request.form
    try:
        c = Course(
            code=data.get("code").upper(),
            title=data.get("title"),
            credits=int(data.get("credits", 3)),
            fee=float(data.get("fee", 0.0)),
            department_id=data.get("department_id") or None,
            description=data.get("description")
        )
        db.session.add(c)
        db.session.commit()

        # Return the new row data for the frontend
        return jsonify({
            "status": "success",
            "course": {
                "id": c.id,
                "code": c.code,
                "title": c.title,
                "credits": c.credits,
                "fee": c.fee,
                "dept_name": c.department.name if c.department else "—"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@admin_bp.route("/api/courses/<int:course_id>", methods=["GET", "POST", "DELETE"])
@login_required
def api_course_manage(course_id):
    if not current_user.is_admin: return jsonify({"error": "Auth required"}), 403

    c = Course.query.get_or_404(course_id)

    # GET details
    if request.method == "GET":
        return jsonify({
            "status": "success",
            "data": {
                "id": c.id, "code": c.code, "title": c.title,
                "credits": c.credits, "fee": c.fee,
                "department_id": c.department_id, "description": c.description
            }
        })

    # UPDATE details
    if request.method == "POST":
        data = request.form
        try:
            c.code = data.get("code").upper()
            c.title = data.get("title")
            c.credits = int(data.get("credits", 3))
            c.fee = float(data.get("fee", 0.0))
            c.department_id = data.get("department_id") or None
            c.description = data.get("description")
            db.session.commit()

            return jsonify({
                "status": "success",
                "course": {
                    "id": c.id, "code": c.code, "title": c.title,
                    "credits": c.credits, "fee": c.fee,
                    "dept_name": c.department.name if c.department else "—"
                }
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    # DELETE
    if request.method == "DELETE":
        try:
            db.session.delete(c)
            db.session.commit()
            return jsonify({"status": "success", "id": course_id})
        except Exception as e:
            return jsonify(
                {"status": "error", "message": "Cannot delete course. It may have active sections or results."}), 400
# --------------------
# Notices management
# --------------------
@admin_bp.route("/notices")
@login_required
def notices_page():
    if not current_user.is_admin:
        return admin_guard()  # Assuming you have an admin_guard helper, otherwise use abort(403)

    # Sort: Pinned first, then by Date (newest first)
    notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.posted_on.desc()).all()
    return render_template("admin/notices.html", notices=notices)


@admin_bp.route("/api/notices/create", methods=["POST"])
@login_required
def api_notice_create():
    if not current_user.is_admin:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.get_json() or {}
    title = data.get("title", "").strip()
    body = data.get("body", "").strip()
    cat_str = data.get("category", "General")
    is_pinned = data.get("is_pinned", False)

    if not title or not body:
        return jsonify({"status": "error", "message": "Title and Body are required"}), 400

    # Convert string to Enum safely
    try:
        # Use the value (e.g., "Exam") to find the Enum
        category_enum = NoticeCategory(cat_str)
    except ValueError:
        # Fallback if invalid category sent
        category_enum = NoticeCategory.GENERAL

    n = Notice(
        title=title,
        body=body,
        category=category_enum,
        is_pinned=bool(is_pinned),
        posted_by_id=current_user.id,
        posted_on=datetime.utcnow()
    )

    try:
        db.session.add(n)
        db.session.commit()
        return jsonify({"status": "ok", "id": n.id, "message": "Notice published successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating notice: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500


# [NEW] Route to Update a Notice
@admin_bp.route("/api/notices/<int:nid>/update", methods=["POST"])
@login_required
def api_notice_update(nid):
    if not current_user.is_admin:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    n = Notice.query.get_or_404(nid)
    data = request.get_json() or {}

    # Update fields
    n.title = data.get("title", n.title).strip()
    n.body = data.get("body", n.body).strip()

    # Handle Category Update
    cat_str = data.get("category")
    if cat_str:
        try:
            n.category = NoticeCategory(cat_str)
        except ValueError:
            pass  # Keep old category if invalid

    # Handle Pinned Status
    if "is_pinned" in data:
        n.is_pinned = bool(data["is_pinned"])

    n.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({"status": "ok", "message": "Notice updated"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# [EXISTING] Delete route (keep as is)
@admin_bp.route("/api/notices/<int:nid>/delete", methods=["POST"])
@login_required
def api_notice_delete(nid):
    if not current_user.is_admin:
        return jsonify({"status": "error"}), 403
    n = Notice.query.get_or_404(nid)
    db.session.delete(n)
    db.session.commit()
    return jsonify({"status": "ok", "deleted": True})

@admin_bp.route("/students")
@login_required
def students_page():
    if not current_user.is_admin: return admin_guard()
    # Pass courses for the filter dropdown
    courses = Course.query.order_by(Course.title).all()
    return render_template("admin/students.html", courses=courses)


@admin_bp.route("/api/students")
@login_required
def api_students_list():
    """
    AJAX Endpoint for filtering and listing students.
    """
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    # Filters
    search_q = request.args.get("q", "").strip()
    course_id = request.args.get("course_id")
    fee_status = request.args.get("fee_status")  # 'paid', 'pending'

    # Base Query
    query = StudentProfile.query.join(User).options(
        joinedload(StudentProfile.user),
        joinedload(StudentProfile.enrollments).joinedload(Enrollment.course),
        joinedload(StudentProfile.payments)
    )

    # Apply Search (Name, Email, Admission No)
    if search_q:
        term = f"%{search_q}%"
        query = query.filter(
            (User.first_name.ilike(term)) |
            (User.last_name.ilike(term)) |
            (User.email.ilike(term)) |
            (StudentProfile.admission_no.ilike(term))
        )

    # Apply Course Filter
    if course_id:
        query = query.join(Enrollment).filter(Enrollment.course_id == course_id)

    # Fetch all (for fee filtering in Python - easier for complex logic)
    students = query.all()

    data = []
    for s in students:
        # Calculate Fees
        total_fee = sum(e.course.fee for e in s.enrollments)
        total_paid = sum(p.amount for p in s.payments)
        balance = float(total_fee) - float(total_paid)

        is_paid = balance <= 0

        # Apply Fee Filter
        if fee_status == "paid" and not is_paid: continue
        if fee_status == "pending" and is_paid: continue

        data.append({
            "id": s.id,
            "admission_no": s.admission_no,
            "name": s.user.full_name(),
            "email": s.user.email,
            "courses_count": len(s.enrollments),
            "fee_status": "Paid" if is_paid else f"Due: ${balance:.2f}",
            "is_paid": is_paid,
            "is_active": s.user.is_active
        })

    return jsonify({"status": "success", "students": data})


admin_bp.route("/api/students/<int:student_id>")

@admin_bp.route("/api/students/<int:student_id>")
@login_required
def api_student_detail(student_id):
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    s = StudentProfile.query.get_or_404(student_id)

    # 1. Academics
    enrollments_data = []
    total_fee = 0.0
    for e in s.enrollments:
        fee = float(e.course.fee)
        total_fee += fee
        enrollments_data.append({
            "id": e.id,
            "course_title": e.course.title,
            "course_code": e.course.code,
            "fee": fee,
            "enrolled_on": e.enrolled_on.strftime("%Y-%m-%d")
        })

    # 2. Payments
    payments_data = []
    total_paid = 0.0
    for p in s.payments:
        amt = float(p.amount)
        total_paid += amt
        payments_data.append({
            "id": p.id,
            "amount": amt,
            "date": p.paid_on.strftime("%Y-%m-%d"),
            "status": p.status
        })

    # 3. FIX: Logic for Balance vs Credit
    raw_balance = total_fee - total_paid

    if raw_balance > 0:
        balance_due = raw_balance
        credit = 0.0
        status_label = "Pending"
    else:
        balance_due = 0.0
        credit = abs(raw_balance)  # This is the "Extra" paid
        status_label = "Settled" if credit == 0 else "Overpaid"

    return jsonify({
        "status": "success",
        "profile": {
            "id": s.id,
            "user_id": s.user.id,
            "avatar": s.user.avatar_url,  # SEND AVATAR URL
            "name": s.user.full_name(),
            "email": s.user.email,
            "phone": s.user.phone,
            "admission_no": s.admission_no,
            "dob": s.date_of_birth.strftime("%Y-%m-%d") if s.date_of_birth else "-",
            "address": s.address,
            "is_active": s.user.is_active,
            "joined": s.created_at.strftime("%Y-%m-%d")
        },
        "academics": enrollments_data,
        "finance": {
            "total_fee": total_fee,
            "total_paid": total_paid,
            "balance_due": balance_due,  # Now strictly >= 0
            "credit": credit,  # Positive if overpaid
            "status": status_label,
            "history": payments_data
        }
    })


@admin_bp.route("/api/students/<int:student_id>/action", methods=["POST"])
@login_required
def api_student_action(student_id):
    """
    Handle actions: Block User, Unenroll from Course
    """
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    action = request.form.get("action")
    s = StudentProfile.query.get_or_404(student_id)

    try:
        if action == "block":
            s.user.is_active = False
            msg = "Student blocked successfully."
        elif action == "unblock":
            s.user.is_active = True
            msg = "Student unblocked successfully."
        elif action == "unenroll":
            enrollment_id = request.form.get("enrollment_id")
            enr = Enrollment.query.get(enrollment_id)
            if enr and enr.student_id == s.id:
                db.session.delete(enr)
                msg = "Student unenrolled from course."
            else:
                return jsonify({"status": "error", "message": "Invalid enrollment"}), 400
        else:
            return jsonify({"status": "error", "message": "Unknown action"}), 400

        db.session.commit()
        return jsonify({"status": "success", "message": msg})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------
# Applications list & deprecated edit — redirect to unified apps page
# --------------------
@admin_bp.route("/applications")
@login_required
def applications_list():
    if not getattr(current_user, "is_admin", False):
        return admin_guard()
    # redirect to combined apps page
    return redirect(url_for("admin.apps_page"))


@admin_bp.route("/applications/<int:app_id>", methods=["GET", "POST"])
@login_required
def application_edit(app_id):
    # Edit page is deprecated. Use the modal on /admin/apps.
    flash("Direct application edit page is deprecated. Use Applications page (modal view).", "info")
    return redirect(url_for("admin.apps_page"))


@admin_bp.route("/applications/<int:app_id>/delete", methods=["POST"])
@login_required
def application_delete(app_id):
    if not getattr(current_user, "is_admin", False):
        return admin_guard()
    app_row = Application.query.get_or_404(app_id)
    db.session.delete(app_row)
    db.session.commit()
    flash("Application removed.", "success")
    return redirect(url_for("admin.apps_page"))









@admin_bp.route("/users/<int:user_id>/approve", methods=["POST"])
@login_required
def users_approve(user_id):
    if not current_user.is_admin: return redirect(url_for("auth.login"))

    user = User.query.get_or_404(user_id)
    course_id = request.form.get("course_id")  # Changed form field name

    try:
        user.is_active = True

        if course_id and course_id.strip():
            course = Course.query.get(int(course_id))
            if course:
                # 1. Create Profile
                if not user.student_profile:
                    adm_no = f"ADM{datetime.now().year}{user.id:04d}"
                    profile = StudentProfile(
                        user_id=user.id,
                        email=user.email,
                        admission_no=adm_no,
                        first_name=user.first_name,
                        last_name=user.last_name,
                    )
                    db.session.add(profile)
                    db.session.flush()
                else:
                    profile = user.student_profile

                # 2. Create Enrollment (Direct to Course)
                existing = Enrollment.query.filter_by(student_id=profile.id, course_id=course.id).first()
                if not existing:
                    enrollment = Enrollment(student_id=profile.id, course_id=course.id)
                    db.session.add(enrollment)
                    flash(f"Approved and enrolled in {course.title}.", "success")
                else:
                    flash("Approved (already enrolled).", "info")
            else:
                flash("Approved, but invalid course selected.", "warning")
        else:
            flash(f"User {user.email} approved (no enrollment).", "success")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("Error processing approval.", "danger")

    return redirect(url_for("admin.enrollment_pending"))


@admin_bp.route("/users/<int:user_id>/reject", methods=["POST"])
@login_required
def users_reject(user_id):
    if not current_user.is_admin: return admin_guard()

    user = User.query.get_or_404(user_id)
    email = user.email
    db.session.delete(user)
    db.session.commit()

    flash(f"User {email} has been rejected and removed.", "info")
    return redirect(url_for("admin.enrollment_pending"))


# NOTE: The route URL is now /requests/pending to match the new sidebar link
@admin_bp.route("/requests/pending")
@login_required
def enrollment_pending():
    if not current_user.is_admin: return admin_guard()

    # 1. Fetch New Account Requests (Users who are inactive)
    pending_users = User.query.filter(User.is_active == False).order_by(User.requested_at.desc()).all()

    # 2. Fetch Course Enrollment Requests (Active users with 'pending' enrollments)
    pending_enrollments = Enrollment.query.filter_by(status="pending").options(
        joinedload(Enrollment.student).joinedload(StudentProfile.user),
        joinedload(Enrollment.course)
    ).all()

    # 3. Fetch all courses (for the 'Approve New Account' dropdown)
    courses = Course.query.order_by(Course.code).all()

    # DEBUG: Print to console to verify data is being fetched
    print(f"DEBUG: Found {len(pending_enrollments)} pending enrollments.")

    return render_template(
        "admin/users_pending.html",
        pending_users=pending_users,
        pending_enrollments=pending_enrollments,
        courses=courses
    )


# 1. Route to APPROVE a Course Enrollment Request
@admin_bp.route("/enrollments/<int:enrollment_id>/approve", methods=["POST"])
@login_required
def approve_enrollment(enrollment_id):
    if not current_user.is_admin: return jsonify({"error": "Auth"}), 403

    enr = Enrollment.query.get_or_404(enrollment_id)
    enr.status = "active"
    db.session.commit()

    flash("Course enrollment approved.", "success")
    return redirect(url_for("admin.enrollment_pending"))


# 2. Route to REJECT a Course Enrollment Request
@admin_bp.route("/enrollments/<int:enrollment_id>/reject", methods=["POST"])
@login_required
def reject_enrollment(enrollment_id):
    if not current_user.is_admin: return jsonify({"error": "Auth"}), 403

    enr = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enr)
    db.session.commit()

    flash("Enrollment request rejected.", "info")
    return redirect(url_for("admin.enrollment_pending"))
# --------------------------
# EXAMS MANAGEMENT
# --------------------------
@admin_bp.route("/exams")
@login_required
def exams_page():
    if not current_user.is_admin: return admin_guard()

    # Fetch all courses for the 'Create Exam' dropdown
    courses = Course.query.order_by(Course.title).all()
    departments = Department.query.order_by(Department.name).all()

    return render_template("admin/exams.html", courses=courses, departments=departments)


@admin_bp.route("/api/exams")
@login_required
def api_exams_list():
    """List exams with optional filtering"""
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    # Filters
    q = request.args.get("q", "").strip()
    dept_id = request.args.get("department_id")

    query = Exam.query.join(Course).options(joinedload(Exam.course))

    if dept_id:
        query = query.filter(Course.department_id == dept_id)

    if q:
        term = f"%{q}%"
        query = query.filter(Exam.name.ilike(term) | Course.title.ilike(term))

    exams = query.order_by(Exam.exam_date.desc()).all()

    data = []
    for e in exams:
        data.append({
            "id": e.id,
            "title": e.name,
            "course_title": e.course.title,
            "course_code": e.course.code,
            "date": e.exam_date.strftime("%Y-%m-%d") if e.exam_date else "-",
            "total_marks": e.total_marks
        })

    return jsonify({"status": "success", "exams": data})


@admin_bp.route("/api/exams/create", methods=["POST"])
@login_required
def api_exam_create():
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    data = request.get_json()
    try:
        exam = Exam(
            name=data.get("title"),
            course_id=int(data.get("course_id")),
            exam_date=datetime.strptime(data.get("date"), "%Y-%m-%d").date() if data.get("date") else None,
            total_marks=int(data.get("total_marks") or 100)
        )
        db.session.add(exam)
        db.session.commit()
        return jsonify({"status": "success", "message": "Exam created"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@admin_bp.route("/api/exams/<int:exam_id>/results", methods=["GET"])
@login_required
def api_exam_results(exam_id):
    """Fetch students for marks entry"""
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    exam = Exam.query.get_or_404(exam_id)

    # 1. Find all students enrolled in this Course
    enrollments = Enrollment.query.filter_by(course_id=exam.course_id).options(joinedload(Enrollment.student)).all()

    results_data = []
    for enr in enrollments:
        # 2. Check if mark already exists
        res = ExamResult.query.filter_by(exam_id=exam.id, enrollment_id=enr.id).first()

        # Get student user details
        student_user = enr.student.user

        results_data.append({
            "enrollment_id": enr.id,
            "admission_no": enr.student.admission_no,
            "student_name": student_user.full_name(),
            "marks_obtained": res.marks_obtained if res else "",
            "remarks": res.remarks if res else ""
        })

    return jsonify({
        "status": "success",
        "exam": {"title": exam.name, "total_marks": exam.total_marks},
        "students": results_data
    })


@admin_bp.route("/api/exams/<int:exam_id>/results", methods=["POST"])
@login_required
def api_exam_results_save(exam_id):
    """Save marks in bulk"""
    if not current_user.is_admin: return jsonify({"status": "error"}), 403

    data = request.get_json()
    rows = data.get("rows", [])

    try:
        for row in rows:
            enrollment_id = row.get("enrollment_id")
            marks = row.get("marks")

            if not enrollment_id: continue

            # Find or Create Result
            res = ExamResult.query.filter_by(exam_id=exam_id, enrollment_id=enrollment_id).first()
            if not res:
                res = ExamResult(exam_id=exam_id, enrollment_id=enrollment_id)
                db.session.add(res)

            # Update values
            if marks == "" or marks is None:
                res.marks_obtained = None
            else:
                res.marks_obtained = float(marks)

            res.remarks = row.get("remarks", "")

        db.session.commit()
        return jsonify({"status": "success", "message": "Results saved"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/api/exams/<int:exam_id>/delete", methods=["POST"])
@login_required
def api_exam_delete(exam_id):
    if not current_user.is_admin: return jsonify({"status": "error"}), 403
    db.session.delete(Exam.query.get_or_404(exam_id))
    db.session.commit()
    return jsonify({"status": "success"})