# dbs.py
import os
import random
from datetime import datetime, timedelta, date
from faker import Faker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.extensions import db
from app.models import (
    User, UserRole, Department, Course, StudentProfile,
    Enrollment, Exam, ExamResult, Payment, Notice,
    NoticeCategory, Application
)

fake = Faker('en_IN')
app = create_app()

# Settings
NUM_STUDENTS = 60
NUM_NOTICES = 10
NUM_APPLICATIONS = 8


def seed_data():
    with app.app_context():
        print("🗑️  Cleaning database...")
        db.drop_all()
        db.create_all()
        print("✅ Database Reset.")

        # ---------------------------------------------------------
        # 1. DEPARTMENTS & COURSES
        # ---------------------------------------------------------
        print("🏛️  Creating Departments & Courses...")

        dept_data = [
            ("CSE", "Computer Science", "Software Engineering & AI"),
            ("ECE", "Electronics & Comm", "Circuits, IoT & Embedded Systems"),
            ("ME", "Mechanical Engg", "Robotics & Automation"),
            ("BBA", "Business Admin", "Finance, Marketing & HR"),
        ]

        departments = []
        courses = []

        for code, name, desc in dept_data:
            dept = Department(code=code, name=name, description=desc)
            db.session.add(dept)
            departments.append(dept)
            db.session.flush()  # Get ID

            # Create 3 courses per department
            for i in range(1, 4):
                c_title = f"{name} Level {i}"
                course = Course(
                    code=f"{code}{100 + i}",
                    title=c_title,
                    credits=random.choice([3, 4]),
                    fee=random.choice([15000.0, 20000.0, 12000.0]),
                    department_id=dept.id,
                    description=fake.paragraph(nb_sentences=2)
                )
                db.session.add(course)
                courses.append(course)

        db.session.commit()

        # ---------------------------------------------------------
        # 2. ADMIN & DEMO STUDENT
        # ---------------------------------------------------------
        print("👤 Creating Admin & Demo Student...")

        # Admin
        admin = User(
            email=os.getenv("ADMIN_EMAIL", "admin@college.edu"),
            first_name="Super",
            last_name="Admin",
            role=UserRole.ADMIN,
            is_admin=True,
            is_active=True,
            phone="9999999999"
        )
        admin.set_password(os.getenv("ADMIN_PASSWORD", "admin123"))
        db.session.add(admin)

        # Demo Student
        demo_user = User(
            email=os.getenv("STUDENT_EMAIL", "student@college.edu"),
            first_name="Rahul",
            last_name="Sharma",
            role=UserRole.STUDENT,
            is_admin=False,
            is_active=True,
            phone="9876543210"
        )
        demo_user.set_password(os.getenv("STUDENT_PASSWORD", "student123"))
        db.session.add(demo_user)
        db.session.flush()  # Essential to get demo_user.id

        demo_profile = StudentProfile(
            user_id=demo_user.id,
            admission_no=f"ADM{datetime.now().year}0001",
            date_of_birth=date(2002, 5, 20),
            gender="Male",
            address="Raipur, Chhattisgarh",
            department_id=departments[0].id,
            year="3rd Year"
        )
        db.session.add(demo_profile)
        db.session.flush()  # Essential to get demo_profile.id for enrollment

        # Enroll Demo Student
        demo_courses = courses[:2]
        for c in demo_courses:
            # Use 'student=demo_profile' OR ensure 'student_id=demo_profile.id' is not None
            enr = Enrollment(student_id=demo_profile.id, course_id=c.id, status='active')
            db.session.add(enr)

            pay = Payment(student_id=demo_profile.id, amount=5000.0, status='success')
            db.session.add(pay)

        # ---------------------------------------------------------
        # 3. BULK STUDENTS (FIXED FLUSHING)
        # ---------------------------------------------------------
        print(f"👨‍🎓 Generating {NUM_STUDENTS} Students...")

        for i in range(NUM_STUDENTS):
            # 1. Create User
            gender = random.choice(["Male", "Female"])
            fname = fake.first_name_male() if gender == "Male" else fake.first_name_female()
            lname = fake.last_name()

            u = User(
                email=f"{fname.lower()}.{lname.lower()}{i}@example.com",
                first_name=fname,
                last_name=lname,
                phone=fake.phone_number()[:15],
                role=UserRole.STUDENT,
                is_active=True
            )
            u.set_password("password")
            db.session.add(u)
            db.session.flush()  # --- FIX: Flush to generate u.id ---

            # 2. Create Profile
            dept = random.choice(departments)
            sp = StudentProfile(
                user_id=u.id,  # Now u.id exists
                admission_no=f"ADM{datetime.now().year}{u.id:04d}",
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=24),
                gender=gender,
                address=fake.city(),
                department_id=dept.id,
                year=random.choice(["1st Year", "2nd Year", "3rd Year"])
            )
            db.session.add(sp)
            db.session.flush()  # --- FIX: Flush to generate sp.id ---

            # 3. Enrollments (Now sp.id exists)
            num_c = random.randint(1, 3)
            dept_courses = [c for c in courses if c.department_id == dept.id]
            if not dept_courses: dept_courses = courses[:3]

            my_courses = random.sample(dept_courses, min(len(dept_courses), num_c))

            for c in my_courses:
                enr = Enrollment(student_id=sp.id, course_id=c.id, status='active')
                db.session.add(enr)

                # Payments
                if random.random() > 0.4:
                    pay = Payment(
                        student_id=sp.id,
                        amount=float(c.fee),
                        paid_on=fake.date_time_this_year(),
                        status='success'
                    )
                    db.session.add(pay)

        db.session.commit()

        # ---------------------------------------------------------
        # 4. EXAMS & RESULTS
        # ---------------------------------------------------------
        print("📝 Scheduling Exams & Grading...")

        all_exams = []
        for course in courses:
            # Past Exam
            past = Exam(
                course_id=course.id,
                name=f"Mid-Term: {course.code}",
                exam_date=date.today() - timedelta(days=random.randint(10, 60)),
                total_marks=50
            )
            db.session.add(past)
            all_exams.append(past)

            # Upcoming
            future = Exam(
                course_id=course.id,
                name=f"Finals: {course.code}",
                exam_date=date.today() + timedelta(days=random.randint(5, 30)),
                total_marks=100
            )
            db.session.add(future)

        db.session.commit()  # Commit exams to get IDs

        # Results for Past Exams
        for exam in all_exams:
            enrollments = Enrollment.query.filter_by(course_id=exam.course_id).all()
            for enr in enrollments:
                if random.random() > 0.1:  # 90% students attempted
                    obtained = random.uniform(20, exam.total_marks)
                    res = ExamResult(
                        exam_id=exam.id,
                        enrollment_id=enr.id,
                        marks_obtained=round(obtained, 1),
                        grade="A" if obtained > 40 else "B",
                        remarks="Good"
                    )
                    db.session.add(res)

        # ---------------------------------------------------------
        # 5. NOTICES & APPLICATIONS
        # ---------------------------------------------------------
        print("📢 Finishing touches...")

        # Notices
        for _ in range(NUM_NOTICES):
            n = Notice(
                title=fake.sentence(),
                body=fake.paragraph(),
                category=random.choice(list(NoticeCategory)),
                is_pinned=random.choice([True, False]),
                posted_by_id=admin.id
            )
            db.session.add(n)

        # Pending Apps
        for _ in range(NUM_APPLICATIONS):
            a = Application(
                name=fake.name(),
                email=fake.email(),
                program_id=random.choice(courses).id,
                status="new"
            )
            db.session.add(a)

        db.session.commit()
        print("✨ SEEDING COMPLETE! ✨")


if __name__ == "__main__":
    seed_data()