# dbs.py
import os
import random
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Load env variables first
load_dotenv()

from app import create_app
from app.extensions import db
from app.models import (
    User, UserRole, Department, Course, StudentProfile, Enrollment,
    Notice, NoticeCategory, Application, Exam, ExamResult, Payment
)

app = create_app()


def seed_data():
    with app.app_context():
        print("🗑️  Cleaning database...")
        db.drop_all()
        db.create_all()
        print("✅ Database Reset.")

        # ------------------------------------------------
        # 1. Create Departments & Courses
        # ------------------------------------------------
        print("🏛️  Creating Departments & Courses...")

        depts_data = [
            ("CSE", "Computer Science", "Software, AI, and Systems"),
            ("BBA", "Business Admin", "Management, Finance, and Marketing"),
            ("ME", "Mechanical Eng", "Robotics and Mechanics"),
        ]

        departments = {}
        for code, name, desc in depts_data:
            d = Department(code=code, name=name, description=desc)
            db.session.add(d)
            departments[code] = d

        db.session.commit()  # Commit to get IDs

        courses_data = [
            # CSE
            ("CS101", "Intro to Python", 4, 150.00, "CSE"),
            ("CS201", "Data Structures", 4, 150.00, "CSE"),
            ("CS305", "Web Development", 3, 120.00, "CSE"),
            # BBA
            ("MKT101", "Digital Marketing", 3, 100.00, "BBA"),
            ("FIN202", "Corporate Finance", 4, 140.00, "BBA"),
            # ME
            ("ME101", "Thermodynamics", 4, 160.00, "ME"),
        ]

        all_courses = []
        for code, title, credits, fee, dept_code in courses_data:
            c = Course(
                code=code,
                title=title,
                credits=credits,
                fee=fee,
                department_id=departments[dept_code].id,
                description=f"Comprehensive course on {title}."
            )
            db.session.add(c)
            all_courses.append(c)

        db.session.commit()

        # ------------------------------------------------
        # 2. Create Specific Admin (from .env)
        # ------------------------------------------------
        admin_email = os.getenv("ADMIN_EMAIL", "admin@college.edu")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

        admin = User(
            email=admin_email,
            first_name="Super",
            last_name="Admin",
            role=UserRole.ADMIN,
            is_admin=True,
            is_active=True
        )
        admin.set_password(admin_pass)
        db.session.add(admin)
        print(f"👤 Admin created: {admin_email}")

        # ------------------------------------------------
        # 3. Create Specific Student (from .env)
        # ------------------------------------------------
        student_email = os.getenv("STUDENT_EMAIL", "student@college.edu")
        student_pass = os.getenv("STUDENT_PASSWORD", "student123")

        student_user = User(
            email=student_email,
            first_name="Rahul",
            last_name="Sharma",
            phone="9876543210",
            role=UserRole.STUDENT,
            is_admin=False,
            is_active=True
        )
        student_user.set_password(student_pass)
        db.session.add(student_user)
        db.session.commit()  # Commit user to get ID

        # Create Profile
        student_profile = StudentProfile(
            user_id=student_user.id,
            admission_no="ADM2026001",
            date_of_birth=date(2004, 5, 15),
            gender="Male",
            address="123, College Road, Delhi",
            department_id=departments["CSE"].id,
            year="2nd Year"
        )
        db.session.add(student_profile)
        db.session.commit()
        print(f"🎓 Student created: {student_email}")

        # ------------------------------------------------
        # 4. Enroll Student & Add Payments
        # ------------------------------------------------
        # Enroll in CS101 and CS305
        enrolled_courses = [c for c in all_courses if c.code in ["CS101", "CS305"]]

        enrollments = []
        for course in enrolled_courses:
            enr = Enrollment(
                student_id=student_profile.id,
                course_id=course.id
            )
            db.session.add(enr)
            enrollments.append(enr)

        # Add a dummy payment
        payment = Payment(
            student_id=student_profile.id,
            amount=500.00,
            status="completed"
        )
        db.session.add(payment)

        db.session.commit()

        # ------------------------------------------------
        # 5. Create Exams & Results
        # ------------------------------------------------
        # Create an exam for CS101
        cs101 = next(c for c in all_courses if c.code == "CS101")
        exam = Exam(
            course_id=cs101.id,
            name="Mid-Term Assessment",
            exam_date=date.today() + timedelta(days=5),
            total_marks=50
        )
        db.session.add(exam)
        db.session.commit()

        # Give the student a result for this exam
        result = ExamResult(
            exam_id=exam.id,
            enrollment_id=enrollments[0].id,  # CS101 enrollment
            marks_obtained=42.5,
            grade="A",
            remarks="Excellent work"
        )
        db.session.add(result)

        # ------------------------------------------------
        # 6. Notices & Applications
        # ------------------------------------------------
        notices = [
            (
            "Welcome Class of 2026", "We are excited to start the new academic session.", NoticeCategory.GENERAL, True),
            ("Mid-Term Dates", "Mid-term exams for CSE start next week.", NoticeCategory.EXAM, False),
            ("Holiday Announcement", "College remains closed on Friday.", NoticeCategory.GENERAL, False),
        ]

        for title, body, cat, pinned in notices:
            n = Notice(
                title=title, body=body, category=cat,
                is_pinned=pinned, posted_by_id=admin.id
            )
            db.session.add(n)

        # Pending Applications (Fake users)
        apps = [
            ("Amit Verma", "amit@example.com", "CSE", "I love coding."),
            ("Sneha Gupta", "sneha@example.com", "BBA", "Interested in management."),
        ]

        for name, email, dept_code, msg in apps:
            prog = next(c for c in all_courses if c.department.code == dept_code)
            a = Application(
                name=name, email=email, program_id=prog.id,
                message=msg, status="new"
            )
            db.session.add(a)

        db.session.commit()
        print("✨ Seeding Complete! System ready.")


if __name__ == "__main__":
    seed_data()