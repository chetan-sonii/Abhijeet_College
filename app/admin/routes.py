# app/admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models import (
    Application, Course, User, ContactMessage, StudentProfile, FacultyProfile,
    Department, Notice, Payment, Exam, ExamResult, Section, Enrollment, FeeStructure, NoticeCategory
)
from app.extensions import db
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy.orm import joinedload

admin_bp = Blueprint("admin", __name__, template_folder="../../templates/admin", url_prefix="/admin")

def admin_guard():
    """Single admin guard helper — returns a redirect if current_user isn't admin."""
    if not (current_user and getattr(current_user, "is_admin", False)):
        flash("Administrator access required.", "warning")
        return redirect(url_for("auth.login"))
    return None


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin:
        return admin_guard()

    try:
        stats = {
            "total_apps": db.session.query(func.count(Application.id)).scalar() or 0,
            "new_apps": db.session.query(func.count(Application.id)).filter(Application.status == "new").scalar() or 0,
            "total_contacts": db.session.query(func.count(ContactMessage.id)).scalar() or 0,
            "unread_contacts": db.session.query(func.count(ContactMessage.id)).filter(ContactMessage.is_read == False).scalar() or 0,
            "pending_users": db.session.query(func.count(User.id)).filter(User.is_active == False, User.is_admin == False).scalar() or 0,
            "total_users": db.session.query(func.count(User.id)).scalar() or 0,
            "courses": db.session.query(func.count(Course.id)).scalar() or 0,
            "students": db.session.query(func.count(StudentProfile.id)).scalar() or 0,
            "faculty": db.session.query(func.count(FacultyProfile.id)).scalar() or 0,
        }
    except Exception:
        current_app.logger.exception("dashboard stats error")
        stats = {k: 0 for k in ["total_apps","new_apps","total_contacts","unread_contacts","pending_users","total_users","courses","students","faculty"]}

    recent_apps = Application.query.order_by(Application.created_at.desc()).limit(6).all()
    recent_contacts = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(6).all()
    recent_users = User.query.filter(User.is_active == False, User.is_admin == False).order_by(User.requested_at.desc()).limit(6).all()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_apps=recent_apps,
        recent_contacts=recent_contacts,
        recent_users=recent_users
    )


# JSON endpoints used by admin JS -------------------------------------------------

@admin_bp.route("/api/stats")
@login_required
def api_stats():
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    try:
        data = {
            "total_apps": db.session.query(func.count(Application.id)).scalar() or 0,
            "new_apps": db.session.query(func.count(Application.id)).filter(Application.status == "new").scalar() or 0,
            "total_contacts": db.session.query(func.count(ContactMessage.id)).scalar() or 0,
            "unread_contacts": db.session.query(func.count(ContactMessage.id)).filter(ContactMessage.is_read == False).scalar() or 0,
            "pending_users": db.session.query(func.count(User.id)).filter(User.is_active == False, User.is_admin == False).scalar() or 0,
            "total_users": db.session.query(func.count(User.id)).scalar() or 0,
            "courses": db.session.query(func.count(Course.id)).scalar() or 0,
            "students": db.session.query(func.count(StudentProfile.id)).scalar() or 0,
            "faculty": db.session.query(func.count(FacultyProfile.id)).scalar() or 0,
        }
        return jsonify({"status":"ok", "stats": data})
    except Exception:
        current_app.logger.exception("api_stats failed")
        return jsonify({"status":"error","message":"server_error"}), 500


@admin_bp.route("/api/recent_applications")
@login_required
def api_recent_applications():
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    try:
        limit = int(request.args.get("limit", 6))
        rows = Application.query.order_by(Application.created_at.desc()).limit(limit).all()
        apps = []
        for a in rows:
            apps.append({
                "id": a.id,
                "name": a.name,
                "email": a.email,
                "program": a.program.title if getattr(a, "program", None) else None,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None
            })
        return jsonify({"status":"ok","applications": apps})
    except Exception:
        current_app.logger.exception("api_recent_applications failed")
        return jsonify({"status":"error","applications": []}), 500


@admin_bp.route("/api/recent_contacts")
@login_required
def api_recent_contacts():
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    try:
        limit = int(request.args.get("limit", 6))
        rows = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(limit).all()
        contacts = []
        for c in rows:
            contacts.append({
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "subject": c.subject,
                "is_read": bool(c.is_read),
                "created_at": c.created_at.isoformat() if c.created_at else None
            })
        return jsonify({"status":"ok","contacts": contacts})
    except Exception:
        current_app.logger.exception("api_recent_contacts failed")
        return jsonify({"status":"error","contacts": []}), 500


# --------------------
# Single Applications & Contacts page (combined)
# --------------------
@admin_bp.route("/apps")
@login_required
def apps_page():
    if not current_user.is_admin:
        return admin_guard()

    apps = Application.query.order_by(Application.created_at.desc()).limit(40).all()
    contacts = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(40).all()

    combined = []
    for a in apps:
        combined.append({
            "id": f"app-{a.id}",
            "type": "application",
            "pk": a.id,
            "name": a.name,
            "email": a.email,
            "summary": a.short_message(140),
            "status": a.status,
            "created_at": a.created_at
        })
    for c in contacts:
        combined.append({
            "id": f"contact-{c.id}",
            "type": "contact",
            "pk": c.id,
            "name": c.name,
            "email": c.email,
            "summary": (c.message[:140] + "…") if c.message and len(c.message) > 140 else (c.message or ""),
            "status": ("read" if c.is_read else "new"),
            "created_at": c.created_at
        })

    combined = sorted(combined, key=lambda r: r["created_at"] or datetime.min, reverse=True)[:60]

    return render_template("admin/apps.html", items=combined)


# API list / detail / mark / delete for apps & contacts (unchanged logic kept)
@admin_bp.route("/api/apps")
@login_required
def api_apps():
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 80))

    apps_q = Application.query
    if q:
        apps_q = apps_q.filter(or_(Application.name.ilike(f"%{q}%"), Application.email.ilike(f"%{q}%"), Application.message.ilike(f"%{q}%")))
    apps = apps_q.order_by(Application.created_at.desc()).limit(limit).all()

    contacts_q = ContactMessage.query
    if q:
        contacts_q = contacts_q.filter(or_(ContactMessage.name.ilike(f"%{q}%"), ContactMessage.email.ilike(f"%{q}%"), ContactMessage.message.ilike(f"%{q}%")))
    contacts = contacts_q.order_by(ContactMessage.created_at.desc()).limit(limit).all()

    out = []
    for a in apps:
        out.append({
            "id": f"app-{a.id}",
            "type": "application",
            "pk": a.id,
            "name": a.name,
            "email": a.email,
            "summary": (a.message or "")[:200],
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None
        })
    for c in contacts:
        out.append({
            "id": f"contact-{c.id}",
            "type": "contact",
            "pk": c.id,
            "name": c.name,
            "email": c.email,
            "summary": (c.message or "")[:200],
            "status": "read" if c.is_read else "new",
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    out_sorted = sorted(out, key=lambda r: r["created_at"] or "", reverse=True)
    return jsonify({"status":"ok","items": out_sorted[:limit]})


@admin_bp.route("/api/apps/<string:item_id>")
@login_required
def api_get_app(item_id):
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403

    if item_id.startswith("app-"):
        pk = int(item_id.split("-",1)[1])
        a = Application.query.get(pk)
        if not a:
            return jsonify({"status":"error","message":"not_found"}), 404
        return jsonify({
            "status":"ok",
            "type":"application",
            "data":{
                "id": a.id, "name": a.name, "email": a.email, "phone": a.phone,
                "program_id": a.program_id, "program": a.program.title if getattr(a, "program", None) else None,
                "message": a.message, "status": a.status, "created_at": a.created_at.isoformat() if a.created_at else None
            }
        })
    elif item_id.startswith("contact-"):
        pk = int(item_id.split("-",1)[1])
        c = ContactMessage.query.get(pk)
        if not c:
            return jsonify({"status":"error","message":"not_found"}), 404
        return jsonify({
            "status":"ok",
            "type":"contact",
            "data":{
                "id": c.id, "name": c.name, "email": c.email, "phone": getattr(c, "phone", None),
                "subject": c.subject, "message": c.message, "is_read": bool(c.is_read),
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
        })
    else:
        return jsonify({"status":"error","message":"invalid_id"}), 400


@admin_bp.route("/api/apps/<string:item_id>/mark", methods=["POST"])
@login_required
def api_mark_app(item_id):
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403

    payload = request.get_json() or {}
    if item_id.startswith("app-"):
        pk = int(item_id.split("-",1)[1])
        a = Application.query.get_or_404(pk)
        new_status = payload.get("status")
        if new_status:
            a.status = new_status
            db.session.add(a)
            db.session.commit()
            return jsonify({"status":"ok","id": a.id, "new_status": a.status})
        return jsonify({"status":"error","message":"no_status"}), 400
    elif item_id.startswith("contact-"):
        pk = int(item_id.split("-",1)[1])
        c = ContactMessage.query.get_or_404(pk)
        set_read = payload.get("is_read")
        if set_read is None:
            c.is_read = not bool(c.is_read)
        else:
            c.is_read = bool(set_read)
        db.session.add(c)
        db.session.commit()
        return jsonify({"status":"ok","id": c.id, "is_read": bool(c.is_read)})
    return jsonify({"status":"error","message":"invalid_id"}), 400


@admin_bp.route("/api/apps/<string:item_id>/delete", methods=["POST"])
@login_required
def api_delete_app(item_id):
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    if item_id.startswith("app-"):
        pk = int(item_id.split("-",1)[1])
        a = Application.query.get_or_404(pk)
        db.session.delete(a)
        db.session.commit()
        return jsonify({"status":"ok","deleted": True})
    elif item_id.startswith("contact-"):
        pk = int(item_id.split("-",1)[1])
        c = ContactMessage.query.get_or_404(pk)
        db.session.delete(c)
        db.session.commit()
        return jsonify({"status":"ok","deleted": True})
    return jsonify({"status":"error","message":"invalid_id"}), 400


# --------------------
# Courses management (list + create/edit via modal)
# NOTE: Course model has 'credits' not 'fees'. Use credits here.
# --------------------
@admin_bp.route("/courses")
@login_required
def courses_page():
    if not current_user.is_admin:
        return admin_guard()
    courses = Course.query.order_by(Course.title).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template("admin/courses.html", courses=courses, departments=departments)


@admin_bp.route("/api/courses/create", methods=["POST"])
@login_required
def api_course_create():
    if not current_user.is_admin:
        return jsonify({"status":"error"}), 403
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    code = data.get("code", "").strip()
    dept_id = data.get("department_id")
    credits = data.get("credits")
    description = data.get("description")
    if not title:
        return jsonify({"status":"error","message":"title_required"}),400
    if not code:
        return jsonify({"status":"error","message":"code_required"}),400
    try:
        course = Course(
            title=title,
            code=code,
            department_id=int(dept_id) if dept_id else None,
            credits=int(credits) if credits is not None and credits != "" else Course.credits.property.columns[0].default.arg,
            description=description
        )
        db.session.add(course)
        db.session.commit()
        return jsonify({"status":"ok","id":course.id,"title":course.title})
    except IntegrityError as ie:
        db.session.rollback()
        current_app.logger.exception("course create integrity error")
        return jsonify({"status":"error","message":"duplicate_code_or_constraint"}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("course create failed")
        return jsonify({"status":"error","message":"server_error"}), 500


@admin_bp.route("/api/courses/<int:cid>/update", methods=["POST"])
@login_required
def api_course_update(cid):
    if not current_user.is_admin:
        return jsonify({"status":"error"}), 403
    c = Course.query.get_or_404(cid)
    data = request.get_json() or {}
    c.title = data.get("title", c.title)
    c.code = data.get("code", c.code)
    dept_id = data.get("department_id")
    c.department_id = int(dept_id) if dept_id else c.department_id
    if "credits" in data:
        try:
            c.credits = int(data.get("credits"))
        except (TypeError, ValueError):
            pass
    c.description = data.get("description", c.description)
    try:
        db.session.add(c)
        db.session.commit()
        return jsonify({"status":"ok","id":c.id})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"status":"error","message":"duplicate_code_or_constraint"}), 400
    except Exception:
        db.session.rollback()
        current_app.logger.exception("course update failed")
        return jsonify({"status":"error","message":"server_error"}), 500


@admin_bp.route("/api/courses/<int:cid>/delete", methods=["POST"])
@login_required
def api_course_delete(cid):
    if not current_user.is_admin:
        return jsonify({"status":"error"}), 403
    c = Course.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status":"ok","deleted":True})


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


# --------------------
# Students page (safe fee detection using Payment.student_id only)
# --------------------
@admin_bp.route("/students")
@login_required
def students_page():
    if not current_user.is_admin:
        return admin_guard()
    q = StudentProfile.query.order_by(StudentProfile.id.desc())
    fee_filter = request.args.get("fee_paid")
    students = q.all()
    out = []
    for s in students:
        paid = False
        try:
            paid_amount = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.student_id == s.id).scalar() or 0
            paid = float(paid_amount) > 0
        except Exception:
            paid = False
        out.append({
            "id": s.id,
            "name": getattr(s, "full_name", None) or getattr(s, "name", None) or s.email or "",
            "class": getattr(s, "year", None) or "",
            "paid": paid,
            "profile": s
        })
    if fee_filter in ("yes","no"):
        out = [r for r in out if (r["paid"] and fee_filter == "yes") or (not r["paid"] and fee_filter == "no")]
    return render_template("admin/students.html", students=out, fee_filter=fee_filter)


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


# --------------------
# Pending users (unchanged)
# --------------------
@admin_bp.route("/users/pending")
@login_required
def users_pending():
    if not current_user.is_admin:
        return admin_guard()
    page = request.args.get("page", 1, type=int)
    q = User.query.filter(User.is_active == False, User.is_admin == False).order_by(User.requested_at.desc())
    pagination = q.paginate(page=page, per_page=20, error_out=False)
    users = pagination.items
    return render_template("admin/users_pending.html", users=users, pagination=pagination)


@admin_bp.route("/users/<int:user_id>/approve", methods=["POST"])
@login_required
def users_approve(user_id):
    if not current_user.is_admin:
        return admin_guard()
    u = User.query.get_or_404(user_id)
    u.is_active = True
    db.session.add(u)
    db.session.commit()
    flash(f"User {u.username or u.email} approved.", "success")
    return redirect(url_for("admin.users_pending"))


@admin_bp.route("/users/<int:user_id>/reject", methods=["POST"])
@login_required
def users_reject(user_id):
    if not current_user.is_admin:
        return admin_guard()
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    flash(f"User {u.username or u.email} rejected and removed.", "info")
    return redirect(url_for("admin.users_pending"))


@admin_bp.route("/exams")
@login_required
def exams_page():
    if not current_user.is_admin:
        return admin_guard()

    # Eager-load section -> course to avoid N+1 and make Jinja rendering reliable
    exams = (
        db.session.query(Exam)
        .options(joinedload(Exam.section).joinedload(Section.course))
        .order_by(Exam.exam_date.desc())
        .all()
    )

    # sections and departments for the create/edit modal select boxes
    sections = Section.query.order_by(Section.code).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template(
        "admin/exams.html",
        exams=exams,
        sections=sections,
        department=departments,
    )



@admin_bp.route("/api/exams", methods=["GET"])
@login_required
def api_exams_list():
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    rows = Exam.query.order_by(Exam.exam_date.desc()).all()
    out = []
    for e in rows:
        out.append({
            "id": e.id,
            "title": e.name,
            "section": e.section.code if getattr(e, "section", None) else None,
            "course": e.section.course.title if getattr(e, "section", None) and getattr(e.section, "course", None) else None,
            "exam_date": e.exam_date.isoformat() if e.exam_date else None,
            "total_marks": e.total_marks
        })

    return jsonify({"status":"ok","exams":out})


@admin_bp.route("/api/exams/create", methods=["POST"])
@login_required
def api_exams_create():
    if not current_user.is_admin:
        return jsonify({"status":"error"}), 403
    data = request.get_json() or {}
    title = data.get("title","").strip()
    section_id = data.get("section_id")
    exam_date = data.get("exam_date")
    total_marks = data.get("total_marks") or None
    if not title or not section_id:
        return jsonify({"status":"error","message":"title_and_section_required"}), 400
    e = Exam(name=title, section_id=int(section_id), exam_date=exam_date or None, total_marks=float(total_marks) if total_marks not in (None, "") else None)
    db.session.add(e)
    db.session.commit()
    return jsonify({"status":"ok","id":e.id})


@admin_bp.route("/api/exams/<int:eid>/delete", methods=["POST"])
@login_required
def api_exams_delete(eid):
    if not current_user.is_admin:
        return jsonify({"status":"error"}), 403
    e = Exam.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    return jsonify({"status":"ok","deleted":True})


@admin_bp.route("/api/exams/<int:eid>/results")
@login_required
def api_exams_results(eid):
    if not current_user.is_admin:
        return jsonify({"status":"error"}), 403
    exam = Exam.query.get_or_404(eid)
    # get enrollments for the section and any existing results
    enrolls = Enrollment.query.filter(Enrollment.section_id == exam.section_id).all()
    # build response rows
    rows = []
    for en in enrolls:
        # try to find result
        res = ExamResult.query.filter_by(exam_id=eid, enrollment_id=en.id).first()
        rows.append({
            "enrollment_id": en.id,
            "student_name": getattr(en.student, "full_name", None) or getattr(en.student, "name", None) or "",
            "student_id": en.student_id,
            "marks_obtained": res.marks_obtained if res else None,
            "grade": res.grade if res else None,
            "result_id": res.id if res else None
        })
    return jsonify({"status":"ok","rows":rows, "exam": {"id": exam.id, "title": exam.name, "total_marks": exam.total_marks}})


@admin_bp.route("/api/exams/<int:eid>/results/save", methods=["POST"])
@login_required
def api_exams_results_save(eid):
    if not current_user.is_admin:
        return jsonify({"status":"error"}), 403
    payload = request.get_json() or {}
    # payload expected: [{"enrollment_id":..,"marks_obtained":..,"grade":.., "result_id":..}, ...]
    rows = payload.get("rows", [])
    saved = []
    for r in rows:
        enrollment_id = int(r.get("enrollment_id"))
        res_id = r.get("result_id")
        marks = r.get("marks_obtained")
        grade = r.get("grade")
        if res_id:
            res = ExamResult.query.get(int(res_id))
            if res:
                res.marks_obtained = float(marks) if marks not in (None,"") else None
                res.grade = grade
                db.session.add(res)
                saved.append(res.id)
        else:
            new = ExamResult(exam_id=eid, enrollment_id=enrollment_id, marks_obtained=float(marks) if marks not in (None,"") else None, grade=grade)
            db.session.add(new)
            db.session.flush()
            saved.append(new.id)
    db.session.commit()
    return jsonify({"status":"ok","saved": saved})

# ---------- FeeStructure APIs (list/create/delete) ----------
@admin_bp.route("/api/fee_structures", methods=["GET", "POST"])
@login_required
def api_fee_structures():
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403

    if request.method == "GET":
        # optional filter: department_id
        dept_id = request.args.get("department_id")
        q = FeeStructure.query.order_by(FeeStructure.created_at.desc())
        if dept_id:
            q = q.filter(FeeStructure.applicable_to_department_id == int(dept_id))
        rows = q.all()
        out = [{"id": r.id, "name": r.name, "amount": str(r.amount), "description": r.description, "department_id": r.applicable_to_department_id} for r in rows]
        return jsonify({"status":"ok","fee_structures": out})

    # POST -> create
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    amount = data.get("amount")
    description = data.get("description")
    dept_id = data.get("department_id") or None
    if not name or amount is None:
        return jsonify({"status":"error","message":"name_and_amount_required"}), 400
    try:
        fs = FeeStructure(name=name, amount=amount, description=description, applicable_to_department_id=int(dept_id) if dept_id else None)
        db.session.add(fs)
        db.session.commit()
        return jsonify({"status":"ok","id": fs.id, "name": fs.name, "amount": str(fs.amount)})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("fee structure create failed")
        return jsonify({"status":"error","message":"server_error"}), 500

# add to app/admin/routes.py (merge with exams routes)
@admin_bp.route("/api/exams/<int:eid>/update", methods=["POST"])
@login_required
def api_exams_update(eid):
    """Update an existing exam (admin only)."""
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403

    exam = Exam.query.get_or_404(eid)
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    section_id = data.get("section_id")
    exam_date = data.get("exam_date")
    total_marks = data.get("total_marks")

    if title:
        exam.title = title
    if section_id is not None and section_id != "":
        try:
            exam.section_id = int(section_id)
        except Exception:
            pass
    # accept empty exam_date as clear
    exam.exam_date = exam_date if exam_date not in (None, "") else None
    if total_marks not in (None, ""):
        try:
            exam.total_marks = float(total_marks)
        except Exception:
            pass

    try:
        db.session.add(exam)
        db.session.commit()
        return jsonify({"status":"ok","id": exam.id})
    except Exception:
        db.session.rollback()
        current_app.logger.exception("api_exams_update failed")
        return jsonify({"status":"error","message":"server_error"}), 500

@admin_bp.route("/api/fee_structures/<int:fid>/delete", methods=["POST"])
@login_required
def api_fee_structure_delete(fid):
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    fs = FeeStructure.query.get_or_404(fid)
    db.session.delete(fs)
    db.session.commit()
    return jsonify({"status":"ok","deleted":True})


# ---------- Student detail API for modal ----------
@admin_bp.route("/api/students/<int:sid>")
@login_required
def api_student_detail(sid):
    if not current_user.is_admin:
        return jsonify({"status":"error","message":"admin_required"}), 403
    s = StudentProfile.query.get_or_404(sid)

    # basic profile
    profile = {
        "id": s.id,
        "full_name": getattr(s, "full_name", None) or getattr(s, "name", None) or "",
        "email": s.email or "",
        "phone": getattr(s, "phone", None) or "",
        "department": s.department.name if getattr(s, "department", None) else None,
        "year": getattr(s, "year", None) or getattr(s, "class_name", None) or "",
        "registration_no": getattr(s, "registration_no", None) or ""
    }

    # enrollments (section info)
    enrolls = []
    for en in s.enrollments:
        enrolls.append({
            "enrollment_id": en.id,
            "section_id": en.section_id,
            "section_code": en.section.code if getattr(en, "section", None) else None,
            "course_title": en.section.course.title if getattr(en, "section", None) and getattr(en.section, "course", None) else None,
            "semester": en.section.semester.name if getattr(en, "section", None) and getattr(en.section, "semester", None) else None,
            "status": en.status
        })

    # payments summary
    payments = []
    total_paid = 0
    for p in Payment.query.filter(Payment.student_id == s.id).order_by(Payment.created_at.desc()).all():
        payments.append({"id": p.id, "amount": float(p.amount), "method": p.method if hasattr(p, "method") else None, "tx": getattr(p, "transaction_id", None), "created_at": p.created_at.isoformat() if p.created_at else None})
        try:
            total_paid += float(p.amount)
        except Exception:
            pass

    # fees applicable (department-level FeeStructures)
    fee_structs = []
    if s.department:
        fs_rows = FeeStructure.query.filter(FeeStructure.applicable_to_department_id == s.department.id).all()
        for fs in fs_rows:
            fee_structs.append({"id": fs.id, "name": fs.name, "amount": str(fs.amount), "description": fs.description})

    return jsonify({"status":"ok", "profile": profile, "enrollments": enrolls, "payments": payments, "total_paid": total_paid, "fee_structures": fee_structs})


# ---------- Exams filtering: update api_exams_list to accept filters ----------
@admin_bp.route("/api/exams", methods=["GET"])
@login_required
def api_exams():
    if not current_user.is_admin:
        return jsonify({"status": "error", "message": "admin_required"}), 403

    # filters
    department_id = request.args.get("department_id")
    q = request.args.get("q", "").strip()
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    # join Exam -> Section -> Course to get course title reliably
    query = (
        db.session.query(Exam, Section, Course)
        .join(Section, Exam.section_id == Section.id)
        .join(Course, Section.course_id == Course.id)
    )

    if department_id:
        try:
            query = query.filter(Course.department_id == int(department_id))
        except Exception:
            pass

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Exam.name.ilike(like),
                Course.title.ilike(like),
                Section.code.ilike(like),
            )
        )

    if date_from:
        try:
            query = query.filter(Exam.exam_date >= date_from)
        except Exception:
            pass

    if date_to:
        try:
            query = query.filter(Exam.exam_date <= date_to)
        except Exception:
            pass

    rows = query.order_by(Exam.exam_date.desc()).all()

    exams = []
    for exam, section, course in rows:
        exams.append(
            {
                "id": exam.id,
                # use exam.name (ORM field) but call JSON key "title" for frontend consistency
                "title": exam.name,
                "exam_date": exam.exam_date.isoformat() if exam.exam_date else None,
                "total_marks": exam.total_marks,
                "section_id": section.id,
                "section_code": section.code,
                "course_title": course.title,
            }
        )
    current_app.logger.debug(exams)
    return jsonify({"status": "ok", "exams": exams})


@admin_bp.route("/api/exams/<int:exam_id>/results", methods=["GET"])
def api_exam_results(exam_id):
    """
    Fetch all students enrolled in the exam's section,
    joined with their existing results (if any).
    """
    exam = Exam.query.get_or_404(exam_id)
    section = exam.section

    if not section:
        return jsonify({"error": "No section attached to this exam"}), 400

    # 1. Get all students enrolled in this section
    enrollments = Enrollment.query.filter_by(section_id=section.id).all()

    data = []
    for enr in enrollments:
        # 2. Check if a result already exists for this exam + enrollment
        result = ExamResult.query.filter_by(exam_id=exam.id, enrollment_id=enr.id).first()

        student_name = enr.student.user.full_name() if enr.student and enr.student.user else "Unknown"
        admission_no = enr.student.admission_no if enr.student else "N/A"

        data.append({
            "enrollment_id": enr.id,
            "student_name": student_name,
            "admission_no": admission_no,
            "marks_obtained": result.marks_obtained if result else "",
            "remarks": result.remarks if result else ""
        })

    return jsonify({
        "exam_title": exam.name,
        "total_marks": exam.total_marks,
        "results": data
    })


@admin_bp.route("/api/exams/<int:exam_id>/results", methods=["POST"])
def api_exam_results_save(exam_id):
    """
    Save or update marks for the students.
    """
    exam = Exam.query.get_or_404(exam_id)
    data = request.get_json()

    if not data or "results" not in data:
        return jsonify({"message": "Invalid data"}), 400

    try:
        for row in data["results"]:
            enrollment_id = row.get("enrollment_id")
            marks_str = str(row.get("marks_obtained", "")).strip()

            # Skip invalid enrollment IDs
            if not enrollment_id:
                continue

            # Find existing result or create new one
            result = ExamResult.query.filter_by(exam_id=exam.id, enrollment_id=enrollment_id).first()

            if not result:
                result = ExamResult(exam_id=exam.id, enrollment_id=enrollment_id)
                db.session.add(result)

            # Handle Marks (convert to float or None)
            if marks_str == "":
                result.marks_obtained = None
            else:
                try:
                    result.marks_obtained = float(marks_str)
                except ValueError:
                    continue  # Skip bad data

            # Optional: Remarks
            result.remarks = row.get("remarks", "")

        db.session.commit()
        return jsonify({"message": "Results saved successfully", "status": "success"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e), "status": "error"}), 500