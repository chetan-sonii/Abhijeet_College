# dbs.py
"""
Seed script for the College Management app.

Place at project root and run:
    python dbs.py
or to wipe & reseed:
    python dbs.py --force
"""

import random
import argparse
from datetime import datetime, timedelta, date
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import (
    User,
    UserRole,
    Department,
    Course,
    Semester,
    Section,
    StudentProfile,
    FacultyProfile,
    section_instructors,
    Enrollment,
    Attendance,
    AttendanceStatus,
    Assignment,
    AssignmentSubmission,
    Exam,
    ExamResult,
    FeeStructure,
    Payment,
    Book,
    BorrowRecord,
    Hostel,
    HostelRoom,
    HostelAllocation,
    Vehicle,
    Route,
    Notice,
    NoticeCategory,  # <--- NEW IMPORT
    Event,
    AuditLog,
)

# ---------- configuration ----------
NUM_STUDENTS = 12
NUM_FACULTY = 3
NUM_COURSES = 6

# ---------- helpers ----------
def mk_email(name, domain="college.local.com"):
    name = name.lower().replace(" ", ".")
    return f"{name}@{domain}"

def random_choice(seq):
    return random.choice(seq)

def ensure(obj):
    """Add and commit a single object, return it (useful when relationships need ids)."""
    db.session.add(obj)
    db.session.flush()
    return obj

# ---------- seed functions ----------
def seed_departments():
    print("Seeding departments...")
    depts = [
        {"code": "CSE", "name": "Computer Science and Engineering"},
        {"code": "ECE", "name": "Electronics and Communication Engineering"},
        {"code": "ME", "name": "Mechanical Engineering"},
    ]
    created = []
    for d in depts:
        existing = Department.query.filter_by(code=d["code"]).first()
        if existing:
            created.append(existing)
            continue
        obj = Department(code=d["code"], name=d["name"], description=f"{d['name']} department")
        created.append(ensure(obj))
    return created

def seed_courses(departments):
    print("Seeding courses...")
    sample = [
        ("CS101", "Intro to Programming", 3, "CSE"),
        ("CS201", "Data Structures", 4, "CSE"),
        ("EC101", "Circuit Theory", 3, "ECE"),
        ("EC201", "Digital Electronics", 3, "ECE"),
        ("ME101", "Engineering Mechanics", 3, "ME"),
        ("ME201", "Thermodynamics", 3, "ME"),
    ]
    created = []
    dept_map = {d.code: d for d in departments}
    for code, title, credits, dcode in sample[:NUM_COURSES]:
        if Course.query.filter_by(code=code).first():
            created.append(Course.query.filter_by(code=code).first())
            continue
        course = Course(code=code, title=title, credits=credits,
                        description=f"{title} - course description",
                        department=dept_map.get(dcode))
        created.append(ensure(course))
    return created

def seed_semesters():
    print("Seeding semesters...")
    s1 = Semester.query.filter_by(name="Fall 2025").first()
    s2 = Semester.query.filter_by(name="Spring 2026").first()
    if not s1:
        s1 = ensure(Semester(name="Fall 2025", start_date=date(2025, 7, 1), end_date=date(2025, 11, 30), is_active=False))
    if not s2:
        s2 = ensure(Semester(name="Spring 2026", start_date=date(2026, 1, 10), end_date=date(2026, 5, 30), is_active=True))
    return [s1, s2]

def seed_users(departments):
    print("Seeding users (admin, faculty, students)...")
    created_admin = None

    # Admin user
    if not User.query.filter_by(email="admin@college.com").first():
        admin = User(email="admin@college.local", first_name="Super", last_name="Admin", role=UserRole.ADMIN)
        admin.set_password("change-me")
        ensure(admin)
        created_admin = admin
    else:
        created_admin = User.query.filter_by(email="admin@college.local").first()

    # Faculty
    faculties = []
    for i in range(1, NUM_FACULTY + 1):
        email = mk_email(f"faculty{i}")
        fuser = User.query.filter_by(email=email).first()
        if fuser:
            faculties.append(fuser)
            continue
        fuser = User(email=email, first_name=f"Faculty{i}", last_name="Member", role=UserRole.FACULTY)
        fuser.set_password("faculty123")
        ensure(fuser)
        faculty_profile = FacultyProfile(user=fuser, employee_id=f"FAC{i:03d}", designation="Assistant Professor",
                                         bio="Experienced faculty", department=random.choice(departments))
        ensure(faculty_profile)
        faculties.append(fuser)
    # Students
    students = []
    for i in range(1, NUM_STUDENTS + 1):
        email = mk_email(f"student{i}")
        u = User.query.filter_by(email=email).first()
        if u:
            students.append(u)
            continue
        u = User(email=email, first_name=f"Student{i}", last_name="Learner", role=UserRole.STUDENT)
        u.set_password("student123")
        ensure(u)
        dept = random.choice(departments)
        profile = StudentProfile(user=u, admission_no=f"ADM{2025}{i:03d}", roll_no=f"R{1000+i}",
                                 date_of_birth=date(2003, random.randint(1, 12), random.randint(1, 28)),
                                 gender=random_choice(["male", "female"]), address="Some address", department=dept, year="1st Year")
        ensure(profile)
        students.append(u)

    return created_admin, faculties, students

def seed_sections_and_enrollments(courses, semesters, faculties, students):
    print("Seeding sections and enrollments...")
    sections = []
    enrollments = []
    semester = semesters[1] if len(semesters) > 1 else semesters[0]  # prefer Spring 2026
    for course in courses:
        # create 1-2 sections per course
        for sfx in ("A",):
            code = f"{course.code}-{sfx}"
            sec = Section.query.filter_by(code=code, course_id=course.id, semester_id=semester.id).first()
            if not sec:
                sec = Section(code=code, course=course, semester=semester, capacity=40, room=f"Room {random.randint(100,499)}",
                              schedule="Mon/Wed/Fri 10:00-11:00")
                ensure(sec)
                # assign 1 faculty randomly
                fac_profile = random.choice(faculties).faculty_profile
                if fac_profile:
                    sec.instructors.append(fac_profile)
            sections.append(sec)

            # enroll 4-6 random students
            candidates = random.sample(students, k=min(6, max(3, len(students)//2)))
            for u in candidates:
                student_profile = u.student_profile
                if not student_profile:
                    continue
                existing = Enrollment.query.filter_by(student_id=student_profile.id, section_id=sec.id).first()
                if existing:
                    enrollments.append(existing)
                    continue
                enr = Enrollment(student=student_profile, section=sec, status="active")
                ensure(enr)
                enrollments.append(enr)
    return sections, enrollments

def seed_attendance(enrollments):
    print("Seeding attendance records...")
    today = date.today()
    # create attendance for last 6 days for each enrollment (random present/absent)
    for enr in enrollments:
        for days in range(1, 7):
            adate = today - timedelta(days=days)
            # avoid duplicate
            if Attendance.query.filter_by(enrollment_id=enr.id, date=adate).first():
                continue
            status = random.choice([AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LATE])
            att = Attendance(enrollment=enr, date=adate, status=status)
            ensure(att)

def seed_assignments_and_submissions(sections, enrollments):
    print("Seeding assignments and submissions...")
    assignments = []
    for sec in sections:
        # create 1 assignment per section
        a = Assignment(section=sec, title=f"{sec.code} - Homework 1", description="Solve problems 1-5",
                       posted_on=datetime.utcnow() - timedelta(days=10), due_date=datetime.utcnow() + timedelta(days=7),
                       total_marks=100)
        ensure(a)
        assignments.append(a)

        # create submissions for half of enrollments in that section
        section_enrs = Enrollment.query.filter_by(section_id=sec.id).all()
        for enr in random.sample(section_enrs, k=max(1, len(section_enrs)//2)):
            if AssignmentSubmission.query.filter_by(assignment_id=a.id, enrollment_id=enr.id).first():
                continue
            sub = AssignmentSubmission(assignment=a, enrollment=enr, submitted_on=datetime.utcnow()-timedelta(days=2),
                                       file_path=f"uploads/assignments/{a.id}/{enr.id}.pdf", marks_obtained=random.randint(50, 95),
                                       feedback="Good work")
            ensure(sub)

def seed_exams_and_results(sections, enrollments):
    print("Seeding exams and results...")
    for sec in sections:
        ex = Exam(section=sec, name="Midterm", exam_date=date.today() - timedelta(days=20), total_marks=100)
        ensure(ex)
        # create results for enrollments in section
        section_enrs = Enrollment.query.filter_by(section_id=sec.id).all()
        for enr in section_enrs:
            if ExamResult.query.filter_by(exam_id=ex.id, enrollment_id=enr.id).first():
                continue
            marks = random.randint(30, 95)
            res = ExamResult(exam=ex, enrollment=enr, marks_obtained=marks, grade=calc_grade(marks))
            ensure(res)

def calc_grade(marks):
    if marks >= 85:
        return "A"
    if marks >= 70:
        return "B"
    if marks >= 55:
        return "C"
    if marks >= 40:
        return "D"
    return "F"

def seed_fees_and_payments(students):
    print("Seeding fee structures and payments...")
    fs = []
    # two fee structures
    tuition = FeeStructure(name="Tuition Fee - 1st Year", amount=Decimal("50000.00"), description="Tuition for first year")
    lab = FeeStructure(name="Lab Fee", amount=Decimal("5000.00"), description="Lab facility fee")
    for f in (tuition, lab):
        if not FeeStructure.query.filter_by(name=f.name).first():
            ensure(f)
        else:
            f = FeeStructure.query.filter_by(name=f.name).first()
        fs.append(f)

    for u in students:
        sp = u.student_profile
        if not sp:
            continue
        # create 1-2 payments
        p1 = Payment(student=sp, fee_structure=fs[0], amount=fs[0].amount, paid_on=datetime.utcnow() - timedelta(days=random.randint(5,30)),
                     payment_method=random.choice(["card", "upi", "cash"]), transaction_id=f"TXN{random.randint(100000,999999)}",
                     status="completed")
        ensure(p1)
        if random.choice([True, False]):
            p2 = Payment(student=sp, fee_structure=fs[1], amount=fs[1].amount, paid_on=datetime.utcnow() - timedelta(days=random.randint(1,20)),
                         payment_method=random.choice(["card","cash"]), transaction_id=f"TXN{random.randint(100000,999999)}", status="completed")
            ensure(p2)

def seed_library(students):
    print("Seeding library books and borrow records...")
    sample_books = [
        {"isbn":"9780131103627","title":"The C Programming Language","author":"Kernighan & Ritchie"},
        {"isbn":"9780132350884","title":"Clean Code","author":"Robert C. Martin"},
        {"isbn":"9780201616224","title":"The Pragmatic Programmer","author":"Andrew Hunt"},
        {"isbn":"9780262033848","title":"Introduction to Algorithms","author":"Cormen et al."},
        {"isbn":"9780134093413","title":"Computer Networking","author":"Kurose & Ross"},
    ]
    created_books = []
    for b in sample_books:
        book = Book.query.filter_by(isbn=b["isbn"]).first()
        if not book:
            book = ensure(Book(isbn=b["isbn"], title=b["title"], author=b["author"], total_copies=3, available_copies=3))
        created_books.append(book)

    # Borrow records for some students
    for student in random.sample(students, k=min(6, len(students))):
        sp = student.student_profile
        if not sp:
            continue
        book = random.choice(created_books)
        br = BorrowRecord(book=book, student=sp, borrowed_on=datetime.utcnow() - timedelta(days=random.randint(1,15)),
                          due_on=datetime.utcnow() + timedelta(days=14), status="borrowed")
        ensure(br)
        # decrement available copies (simple)
        if book.available_copies and book.available_copies > 0:
            book.available_copies = max(0, book.available_copies - 1)
            db.session.add(book)

def seed_hostel_allocations(students):
    print("Seeding hostels and room allocations...")
    h = Hostel.query.filter_by(name="Main Hostel").first()
    if not h:
        h = ensure(Hostel(name="Main Hostel", address="On-campus"))
    # create rooms
    rooms = []
    for num in range(1, 6):
        rn = f"{100+num}"
        r = HostelRoom.query.filter_by(hostel_id=h.id, room_no=rn).first()
        if not r:
            r = ensure(HostelRoom(hostel=h, room_no=rn, capacity=2))
        rooms.append(r)

    # allocate a few students
    for student in random.sample(students, k=min(4, len(students))):
        sp = student.student_profile
        if not sp:
            continue
        # skip if already allocated
        if HostelAllocation.query.filter_by(student_id=sp.id).first():
            continue
        room = random.choice(rooms)
        alloc = HostelAllocation(student=sp, room=room, allocated_on=datetime.utcnow() - timedelta(days=random.randint(1,100)), status="active")
        ensure(alloc)

def seed_transport():
    print("Seeding vehicles and routes...")
    v1 = Vehicle.query.filter_by(registration_no="MH01AB0001").first()
    if not v1:
        v1 = ensure(Vehicle(registration_no="MH01AB0001", capacity=20, driver_name="Ramesh Kumar", phone="9999999999"))
    route = Route.query.filter_by(name="North Campus Route").first()
    if not route:
        route = ensure(Route(name="North Campus Route", stops="Stop A,Stop B,Stop C"))

def seed_notices_events(admin_user):
    print("Seeding notices and events with categories...")

    # Data designed to show off the Badge and Pinned features
    notices_data = [
        {
            "title": "Semester Exams - Final Schedule",
            "body": "The final schedule for the Spring 2026 semester exams is now available. Click here to download the PDF. Exams begin on May 1st.",
            "category": NoticeCategory.EXAM,
            "is_pinned": True,  # Will appear first
            "days_ago": 0
        },
        {
            "title": "Campus Recruitment Drive: Google & Amazon",
            "body": "Top tech companies are visiting campus on Feb 15th. All final year students must update their resumes in the placement portal by Friday.",
            "category": NoticeCategory.PLACEMENT,
            "is_pinned": True, # Will appear second
            "days_ago": 1
        },
        {
            "title": "Annual TechFest 'Innovate' Registration",
            "body": "Registration for the annual tech fest is now open. Events include Hackathon, RoboWars, and Coding Sprint. Visit the auditorium for details.",
            "category": NoticeCategory.EVENT,
            "is_pinned": False,
            "days_ago": 2
        },
        {
            "title": "Scholarship Applications Open",
            "body": "State merit scholarship applications are now open for the academic year 2026-27. Eligible students should submit forms to the admin office.",
            "category": NoticeCategory.ACADEMIC,
            "is_pinned": False,
            "days_ago": 5
        },
        {
            "title": "Library Maintenance Schedule",
            "body": "The central library will remain closed for maintenance on Sunday, 25th Jan. Digital access will remain available.",
            "category": NoticeCategory.GENERAL,
            "is_pinned": False,
            "days_ago": 7
        },
        {
            "title": "Blood Donation Camp",
            "body": "NSS is organizing a blood donation camp in the main hallway this Saturday. Volunteers are welcome.",
            "category": NoticeCategory.EVENT,
            "is_pinned": False,
            "days_ago": 10
        }
    ]

    for data in notices_data:
        if not Notice.query.filter_by(title=data["title"]).first():
            n = Notice(
                title=data["title"],
                body=data["body"],
                category=data["category"],
                is_pinned=data["is_pinned"],
                posted_by=admin_user,
                posted_on=datetime.utcnow() - timedelta(days=data["days_ago"])
            )
            ensure(n)

    # Process events
    events_data = [
        {
            "title": "Freshers Orientation",
            "description": "Orientation for new students",
            "start": datetime.utcnow() + timedelta(days=7),
            "end": datetime.utcnow() + timedelta(days=7, hours=3),
            "location": "Main Auditorium"
        }
    ]

    for data in events_data:
        if not Event.query.filter_by(title=data["title"]).first():
            e = Event(
                title=data["title"],
                description=data["description"],
                start_datetime=data["start"],
                end_datetime=data["end"],
                location=data["location"],
                created_by=admin_user
            )
            ensure(e)

def seed_audit_logs(admin_user):
    print("Seeding audit logs...")
    if not AuditLog.query.first():
        al = AuditLog(user=admin_user, action="seed:initial", ip_address="127.0.0.1", meta="seed script run")
        ensure(al)

# ---------- orchestrator ----------
def seed_all(force=False):
    app = create_app()
    with app.app_context():
        if force:
            print("Force flag detected — dropping and recreating all tables...")
            db.drop_all()
            db.create_all()
        else:
            # if there is already data, skip by default
            if User.query.first():
                print("Database already contains data. Use --force to wipe and reseed.")
                return

        departments = seed_departments()
        courses = seed_courses(departments)
        semesters = seed_semesters()
        admin_user, faculties, students = seed_users(departments)
        sections, enrollments = seed_sections_and_enrollments(courses, semesters, faculties, students)
        db.session.commit()  # commit so that subsequent relationships have ids

        seed_attendance(enrollments)
        seed_assignments_and_submissions(sections, enrollments)
        seed_exams_and_results(sections, enrollments)
        seed_fees_and_payments(students)
        seed_library(students)
        seed_hostel_allocations(students)
        seed_transport()
        seed_notices_events(admin_user)
        seed_audit_logs(admin_user)

        # final commit
        db.session.commit()
        print("Seeding complete.")

# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database with mock college data.")
    parser.add_argument("--force", action="store_true", help="Drop all tables and recreate before seeding.")
    args = parser.parse_args()
    seed_all(force=args.force)