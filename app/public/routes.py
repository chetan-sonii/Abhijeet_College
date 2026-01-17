# app/public/routes.py
from flask import Blueprint, render_template, jsonify, request, current_app, url_for,redirect,flash
from datetime import datetime
from app.models import Notice, Course, StudentProfile, FacultyProfile, Department, Application, ContactMessage
from app.extensions import db

public_bp = Blueprint("public", __name__, template_folder="../../templates/public", static_folder="../../static")


@public_bp.route("/")
def index():
    # hero/stats logic unchanged — get dynamic counts
    try:
        courses_count = Course.query.count()
    except Exception:
        current_app.logger.exception("Failed to count courses")
        courses_count = 0

    try:
        students_count = StudentProfile.query.count()
    except Exception:
        current_app.logger.exception("Failed to count students")
        students_count = 0

    try:
        faculty_count = FacultyProfile.query.count()
    except Exception:
        current_app.logger.exception("Failed to count faculty")
        faculty_count = 0

    try:
        notices = Notice.query.order_by(Notice.posted_on.desc()).limit(4).all()
    except Exception:
        notices = []

    # departments and courses for earlier sections (if used)
    try:
        departments = Department.query.order_by(Department.name).all()
    except Exception:
        departments = []

    try:
        courses = Course.query.join(Department).order_by(Department.name, Course.title).limit(6).all()
    except Exception:
        courses = []

    # Fetch a small list of faculty for server-render fallback
    try:
        faculties = (
            FacultyProfile.query
            .join(FacultyProfile.user.property.mapper.class_)  # ensures relationship available
            .order_by(FacultyProfile.id)
            .limit(8)
            .all()
        )
    except Exception:
        current_app.logger.exception("Failed to fetch faculties")
        faculties = []

    hero = {
        "title": current_app.config.get("HERO_TITLE", "Welcome to Our College"),
        "subtitle": current_app.config.get("HERO_SUBTITLE", "Manage courses, attendance, assignments and campus services — made for students and staff."),
        "image": url_for("static", filename="index/images/herO.JPG"),
        "cta_primary": {"label": "Create account", "url": url_for("auth.register")},
        "cta_secondary": {"label": "Learn more", "url": url_for("public.about")},
    }

    return render_template(
        "public/index.html",
        hero=hero,
        stats={"courses": courses_count, "students": students_count, "faculty": faculty_count},
        notices=notices,
        departments=departments,
        courses=courses,
        faculties=faculties,
    )


@public_bp.route("/api/staff")
def api_staff():
    """
    Returns faculty list.
    Optional query param:
      - department (int): department id to filter
    """
    dept = request.args.get("department")
    q = FacultyProfile.query.join(FacultyProfile.user)
    if dept and dept.isdigit():
        q = q.filter(FacultyProfile.department_id == int(dept))
    q = q.order_by(FacultyProfile.id).limit(50)

    try:
        results = []
        for f in q:
            user = f.user
            name = (user.first_name or "") + (" " + (user.last_name or "") if user.last_name else "")
            name = name.strip() or (user.email.split("@")[0] if getattr(user, "email", None) else "Faculty")
            results.append({
                "id": f.id,
                "name": name,
                "designation": f.designation or "",
                "department": (f.department.name if getattr(f, "department", None) else ""),
                "bio": (f.bio or "")[:400],
                # if you later add photo URLs to FacultyProfile, return them here; fallback to picsum
                "image": getattr(f, "photo_url", None) or f"https://i.pravatar.cc/300?u=faculty-{f.id}"
            })
        return jsonify({"status": "ok", "staff": results})
    except Exception:
        current_app.logger.exception("Failed to fetch staff")
        return jsonify({"status": "error", "staff": []}), 500


@public_bp.route("/api/notices")
def api_notices():
    limit = 6
    try:
        limit = int(request.args.get("limit", limit))
    except ValueError:
        limit = 6

    try:
        # Sort by Pinned (descending) first, then Date (descending)
        q = Notice.query.order_by(Notice.is_pinned.desc(), Notice.posted_on.desc()).limit(limit).all()
        res = []
        for n in q:
            # Get the string value of the enum (e.g., "Exam")
            cat_name = n.category.value if hasattr(n, 'category') else "General"

            res.append({
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "category": cat_name,  # Send to frontend
                "is_pinned": n.is_pinned,
                "posted_on": n.posted_on.strftime('%d %b %Y') if n.posted_on else "New",
            })
        return jsonify({"status": "ok", "notices": res})
    except Exception as e:
        current_app.logger.exception("Failed to fetch notices")
        return jsonify({"status": "error", "message": str(e)}), 500


@public_bp.route("/api/programs")
def api_programs():
    """
    Returns featured programs (courses grouped by department)
    """
    try:
        programs = (
            db.session.query(
                Course.id,
                Course.title,
                Course.code,
                Department.name.label("department")
            )
            .join(Department, Course.department_id == Department.id)
            .order_by(Department.name, Course.title)
            .limit(6)
            .all()
        )

        data = []
        for p in programs:
            data.append({
                "id": p.id,
                "title": p.title,
                "code": p.code,
                "department": p.department,
                # dynamic image placeholder (no hardcoding)
                "image": f"https://picsum.photos/seed/program-{p.id}/500/350"
            })

        return jsonify({"status": "ok", "programs": data})

    except Exception as e:
        current_app.logger.exception("Programs API failed")
        return jsonify({"status": "error", "programs": []}), 500

@public_bp.route("/api/programs/filter")
def filter_programs():
    dept_id = request.args.get("department")

    q = Course.query.join(Department)
    if dept_id and dept_id.isdigit():
        q = q.filter(Course.department_id == int(dept_id))

    courses = q.order_by(Course.title).all()

    data = []
    for c in courses:
        data.append({
            "id": c.id,
            "title": c.title,
            "code": c.code,
            "department": c.department.name,
            "image": f"https://picsum.photos/seed/course-{c.id}/500/350"
        })

    return jsonify({"status": "ok", "courses": data})

@public_bp.route("/apply", methods=["POST"])
def apply():
    """
    Accepts application form from Enroll modal.
    Returns JSON for AJAX, otherwise redirects with flash.
    """
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    program = request.form.get("program", "").strip()
    message = request.form.get("message", "").strip()

    # Basic validation
    if not name or not email:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"status": "error", "message": "Name and email are required."}), 400
        flash("Name and email are required.", "danger")
        return redirect(url_for("public.index"))

    # Resolve program id to int if provided
    program_id = None
    if program:
        try:
            program_id = int(program)
            # optional: verify program exists
            if not Course.query.get(program_id):
                program_id = None
        except Exception:
            program_id = None

    # Persist application
    app_row = Application(
        name=name,
        email=email,
        phone=phone or None,
        program_id=program_id,
        message=message or None,
        status="new",
    )
    db.session.add(app_row)
    db.session.commit()

    # Logging + response
    current_app.logger.info("Saved application id=%s name=%s email=%s", app_row.id, name, email)

    # 🔑 THIS IS THE IMPORTANT PART
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "ok", "id": app_row.id})

    flash("Application received — we will contact you soon.", "success")
    return redirect(url_for("public.index"))

# ABOUT route
@public_bp.route("/about")
def about():
    # dynamic content for facts
    try:
        courses_count = Course.query.count()
    except Exception:
        current_app.logger.exception("Count courses failed")
        courses_count = 0
    try:
        students_count = StudentProfile.query.count()
    except Exception:
        students_count = 0
    try:
        faculty_count = FacultyProfile.query.count()
    except Exception:
        faculty_count = 0

    # Simple leadership sample (server fallback). Replace with real data when you have it.
    leadership = [
        {"name": "Dr. A. Principal", "title": "Principal", "bio": "Visionary leader", "image": url_for("static", filename="index/images/placeholder-face.png")},
        {"name": "Prof. B. Head", "title": "Head of Academics", "bio": "Curriculum & quality", "image": url_for("static", filename="index/images/placeholder-face.png")},
    ]

    # Core values and mission — prefer app config keys if set
    vision = current_app.config.get("COLLEGE_VISION", "To empower students to become future-ready professionals.")
    mission = current_app.config.get("COLLEGE_MISSION", "Deliver high quality education, foster research & industry collaboration.")
    core_values = current_app.config.get("COLLEGE_CORE_VALUES", [
        "Academic Excellence",
        "Integrity",
        "Inclusivity",
        "Innovation",
        "Industry Collaboration",
    ])

    facts = {
        "courses": courses_count,
        "students": students_count,
        "faculty": faculty_count,
    }

    return render_template(
        "public/about.html",
        vision=vision,
        mission=mission,
        core_values=core_values,
        facts=facts,
        leadership=leadership
    )


# CONTACT routes
@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            # If AJAX, return JSON
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"status": "error", "message": "Name, email and message are required."}), 400
            flash("Please fill required fields: name, email and message.", "danger")
            return redirect(url_for("public.contact"))

        cm = ContactMessage(name=name, email=email, subject=subject or None, message=message)
        db.session.add(cm)
        db.session.commit()
        current_app.logger.info("Saved contact message id=%s from %s", cm.id, cm.email)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"status": "ok", "id": cm.id})

        flash("Thank you — your message has been received.", "success")
        return redirect(url_for("public.contact"))

    # GET: render contact page with basic info
    contact_info = {
        "address": current_app.config.get("COLLEGE_ADDRESS", "123 Campus Road, City, State"),
        "phone": current_app.config.get("COLLEGE_PHONE", "+91 99999 99999"),
        "email": current_app.config.get("COLLEGE_EMAIL", "admissions@college.local")
    }
    return render_template("public/contact.html", contact_info=contact_info)

# friendly shortcut: send /home to index
@public_bp.route("/home")
def home():
    return redirect(url_for("public.index"))

