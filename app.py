from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from openpyxl import load_workbook

# =========================================================
# PROJECT LOCATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates")
)
app.secret_key = os.environ.get("SECTION_SYNC_SECRET_KEY", "sectionsync-local-development-key")


# =========================================================
# DATABASE LOCATION
# =========================================================

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "section_management.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    # Allows database columns to be accessed by name
    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# CREATE DATABASE AND TABLES
# =========================================================

def create_database():

    # Create database folder
    os.makedirs(
        os.path.join(BASE_DIR, "database"),
        exist_ok=True
    )

    connection = get_db_connection()
    cursor = connection.cursor()

    # =====================================================
    # ADMINS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            admin_id TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            admin_name TEXT NOT NULL,

            email TEXT

        )
    """)


    # =====================================================
    # DEMO ADMIN
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM admins
        WHERE admin_id = ?
    """, (
        "admin01",
    ))

    admin = cursor.fetchone()


    if not admin:

        cursor.execute("""
            INSERT INTO admins
            (
                admin_id,
                password,
                admin_name,
                email
            )
            VALUES (?, ?, ?, ?)
        """, (

            "admin01",

            "admin123",

            "SectionSync Administrator",

            "admin@sectionsync.com"

        ))
    # =====================================================
    # STUDENTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_name TEXT NOT NULL,

            enrollment_no TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            program TEXT NOT NULL
        )
    """)

    # =====================================================
    # ADD PROFILE COLUMNS TO EXISTING DATABASE
    # =====================================================

    # These columns are added if your old database
    # does not already contain them.

    try:

        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN dob TEXT
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN email TEXT
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN batch TEXT
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN cgpa REAL
        """)

    except sqlite3.OperationalError:

        pass


    # Demo accounts use the college enrollment number pattern from 618 to 668.
    # Their profiles are distinct so the logged-in student's name and course
    # appear correctly throughout the student pages.
    demo_programs = ["CSE", "AI&DS", "AI&ML", "AI", "EEE", "ECE"]
    demo_names = [
        "Aarav Sharma", "Ananya Reddy", "Arjun Kumar", "Diya Patel",
        "Ishaan Rao", "Kavya Nair", "Rohan Gupta", "Saanvi Iyer",
        "Vivaan Das", "Meera Joshi", "Aditya Menon", "Ira Singh",
    ]
    for number in range(618, 669):
        enrollment_no = f"24STUCHH01{number:04d}"
        index = number - 618
        existing = cursor.execute(
            "SELECT id FROM students WHERE enrollment_no = ?",
            (enrollment_no,)
        ).fetchone()
        if existing:
            cursor.execute(
                "UPDATE students SET password = ? WHERE enrollment_no = ?",
                ("college@123", enrollment_no)
            )
            if number == 618:
                cursor.execute("""
                    UPDATE students SET student_name = ?, program = ?, dob = ?,
                        email = ?, batch = ?, cgpa = ? WHERE enrollment_no = ?
                """, (
                    "Preethi Rao", "CSE", "15-08-2007",
                    "preethi@college.edu", "2024-2028", 3.65, enrollment_no
                ))
            continue

        cursor.execute("""
            INSERT INTO students
                (student_name, enrollment_no, password, program,
                 dob, email, batch, cgpa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Preethi Rao" if number == 618 else f"{demo_names[(index - 1) % len(demo_names)]} {number}",
            enrollment_no, "college@123", demo_programs[index % len(demo_programs)],
            f"{(index % 28) + 1:02d}-0{(index % 9) + 1}-2006",
            f"{enrollment_no.lower()}@college.edu", "2024-2028",
            round(2.2 + ((index * 17) % 181) / 100, 2),
        ))

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            UNIQUE (section_name, program)
        )
    """)
    sections_by_program = {
        "CSE": ["A", "B", "C", "D"],
        "AI&DS": ["E", "F", "G"],
        "AI&ML": ["H", "I"],
        "AI": ["J", "K"],
        "EEE": ["L", "M"],
        "ECE": ["N", "O"],
    }
    for program, section_names in sections_by_program.items():
        for section_name in section_names:
            cursor.execute("""
                INSERT OR IGNORE INTO sections (section_name, program, capacity)
                VALUES (?, ?, 50)
            """, (section_name, program))


    # =====================================================
    # FEE PAYMENTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_payments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_name TEXT NOT NULL,

            enrollment_no TEXT NOT NULL,

            order_id TEXT UNIQUE NOT NULL,

            payment_status TEXT NOT NULL
        )
    """)


    # =====================================================
    # DEMO STUDENT
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM students
        WHERE enrollment_no = ?
    """, (
        "24STUCHH010618",
    ))

    student = cursor.fetchone()


    # Insert demo student if it does not exist
    if not student:

        cursor.execute("""
            INSERT INTO students
            (
                student_name,
                enrollment_no,
                password,
                program,
                dob,
                email,
                batch
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            "Preethi Rao",

            "24STUCHH010618",

            "1234",

            "CSE",

            "DD-MM-YYYY",

            "your-email@example.com",

            "2024-2028"
        ))


    # =====================================================
    # UPDATE DEMO STUDENT PROFILE
    # =====================================================

    # This also works if the student already existed
    # in the old database.

    cursor.execute("""
        UPDATE students

        SET
            student_name = ?,
            dob = ?,
            email = ?,
            program = ?,
            batch = ?

        WHERE enrollment_no = ?
    """, (

        "Preethi Rao",

        "15-08-2007",

        "preethi@college.edu",

        "CSE",

        "2024-2028",

        "24STUCHH010618"
    ))


    # =====================================================
    # DEMO FEE PAYMENT RECORDS
    # =====================================================

    fee_records = [

        (
            "Preethi Rao",
            "24STUCHH010618",
            "050326084153",
            "Verified"
        ),

        (
            "Rahul Kumar",
            "24STUCHH010619",
            "COLLEGE123457",
            "Verified"
        ),

        (
            "Ananya Sharma",
            "24STUCHH010620",
            "COLLEGE123458",
            "Verified"
        )
    ]


    # Insert fee records only if they don't exist
    for record in fee_records:

        cursor.execute("""
            SELECT *
            FROM fee_payments
            WHERE order_id = ?
        """, (
            record[2],
        ))

        existing_record = cursor.fetchone()


        if not existing_record:

            cursor.execute("""
                INSERT INTO fee_payments
                (
                    student_name,
                    enrollment_no,
                    order_id,
                    payment_status
                )
                VALUES (?, ?, ?, ?)
            """, record)


    # Save database changes
    connection.commit()

    connection.close()


# =========================================================
# HOME / LOGIN PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "login.html"
    )


@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        # Get enrollment number from login form
        enrollment_no = request.form.get(
            "enrollment",
            ""
        ).strip()


        # Get password from login form
        password = request.form.get(
            "password",
            ""
        ).strip()


        # Connect to database
        connection = get_db_connection()


        # Find the account first, then verify either its own password or
        # the local-only password used for testing different student IDs.
        student = connection.execute("""
            SELECT *
            FROM students

            WHERE enrollment_no = ?
        """, (
            enrollment_no,
        )).fetchone()


        # Close connection
        connection.close()


        # Successful login
        stored_password_matches = (
            student is not None and student["password"] == password
        )
        local_test_password_matches = (
            student is not None
            and app.config.get("LOCAL_STUDENT_TEST_PASSWORD")
            and password == app.config["LOCAL_STUDENT_TEST_PASSWORD"]
        )

        if stored_password_matches or local_test_password_matches:

            session["student_id"] = student["id"]
            session.pop("admin_id", None)

            return redirect(
                "/student/dashboard"
            )


        # Invalid login
        return render_template(
            "login.html",
            error="Invalid enrollment number or password."
        )


    return render_template(
        "login.html"
    )

# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        admin_id = request.form.get(
            "admin_id",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        connection = get_db_connection()


        admin = connection.execute("""
            SELECT *
            FROM admins

            WHERE admin_id = ?
            AND password = ?
        """, (

            admin_id,

            password

        )).fetchone()


        connection.close()


        if admin:

            session["admin_id"] = admin["id"]
            session.pop("student_id", None)

            return redirect(
                "/admin/dashboard"
            )


        return render_template(
            "admin/login.html",

            error="Invalid Admin ID or password."
        )


    return render_template(
        "admin/login.html"
    )

# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    return render_template(
        "admin/dashboard.html"
    )

@app.route("/admin/profile")
def admin_profile():

    connection = get_db_connection()

    admin = connection.execute("""
        SELECT *
        FROM admins
        WHERE admin_id = ?
    """, ("admin01",)).fetchone()

    connection.close()

    return render_template(
        "admin/profile.html",
        admin=admin
    )


@app.route("/admin/student-management", methods=["GET", "POST"])
def student_management():

    message = None
    upload_errors = []

    if request.method == "POST":

        excel_file = request.files.get("excel_file")

        if not excel_file or not excel_file.filename:
            message = "Please select an Excel file."

        elif not excel_file.filename.lower().endswith(".xlsx"):
            message = "Please select a valid .xlsx Excel file."

        else:
            workbook = None
            connection = None

            try:
                workbook = load_workbook(
                    excel_file,
                    read_only=True,
                    data_only=True
                )

                sheet = workbook.active
                rows = sheet.iter_rows(values_only=True)
                first_row = next(rows, None)

                if not first_row:
                    message = "The Excel file is empty."

                else:
                    headers = [
                        "_".join(str(value).strip().lower().split())
                        if value is not None else ""
                        for value in first_row
                    ]

                    required = [
                        "student_name",
                        "enrollment_no",
                        "password",
                        "program"
                    ]

                    missing = [
                        column for column in required
                        if column not in headers
                    ]

                    if missing:
                        message = (
                            "Missing Excel columns: "
                            + ", ".join(missing)
                        )

                    else:
                        connection = get_db_connection()
                        cursor = connection.cursor()

                        preference_columns = [
                            f"preference_{number}"
                            for number in range(1, 5)
                            if f"preference_{number}" in headers
                        ]
                        if preference_columns:
                            cursor.execute("""
                                CREATE TABLE IF NOT EXISTS student_preferences (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    student_id INTEGER NOT NULL,
                                    preference_order INTEGER NOT NULL,
                                    section_name TEXT NOT NULL,
                                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                    UNIQUE (student_id, preference_order),
                                    UNIQUE (student_id, section_name)
                                )
                            """)

                        added = 0
                        skipped = 0

                        for row_number, values in enumerate(rows, start=2):

                            if all(value is None for value in values):
                                continue

                            data = dict(zip(headers, values))

                            def clean(value):
                                if value is None:
                                    return ""

                                if (
                                    isinstance(value, float)
                                    and value.is_integer()
                                ):
                                    return str(int(value))

                                return str(value).strip()

                            student_name = clean(
                                data.get("student_name")
                            )
                            enrollment_no = clean(
                                data.get("enrollment_no")
                            )
                            password = clean(data.get("password"))
                            program = clean(data.get("program"))
                            program_aliases = {
                                "AIDS": "AI&DS",
                                "AI&DS": "AI&DS",
                                "AIML": "AI&ML",
                                "AI&ML": "AI&ML",
                            }
                            program = program_aliases.get(
                                program.upper(), program
                            )

                            dob = clean(data.get("dob")) or None
                            email = clean(data.get("email")) or None
                            batch = clean(data.get("batch")) or None
                            cgpa_raw = clean(data.get("cgpa"))

                            try:
                                cgpa = float(cgpa_raw) if cgpa_raw else None
                            except ValueError:
                                cgpa = -1

                            if not all([
                                student_name,
                                enrollment_no,
                                password,
                                program
                            ]):
                                skipped += 1
                                upload_errors.append(
                                    f"Row {row_number}: "
                                    "A required field is empty."
                                )
                                continue

                            if cgpa is not None and not 0 <= cgpa <= 10:
                                skipped += 1
                                upload_errors.append(
                                    f"Row {row_number}: CGPA must be a number from 0 to 10."
                                )
                                continue

                            imported_preferences = [
                                clean(data.get(f"preference_{number}"))
                                for number in range(1, 5)
                            ]
                            imported_preferences = [
                                section for section in imported_preferences if section
                            ]
                            if len(imported_preferences) != len(set(imported_preferences)):
                                skipped += 1
                                upload_errors.append(
                                    f"Row {row_number}: Section preferences must not repeat."
                                )
                                continue

                            try:
                                cursor.execute("""
                                    INSERT INTO students (
                                        student_name,
                                        enrollment_no,
                                        password,
                                        program,
                                        dob,
                                        email,
                                        batch,
                                        cgpa
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    student_name,
                                    enrollment_no,
                                    password,
                                    program,
                                    dob,
                                    email,
                                    batch,
                                    cgpa
                                ))

                                if imported_preferences:
                                    cursor.executemany("""
                                        INSERT INTO student_preferences (
                                            student_id, preference_order, section_name
                                        ) VALUES (?, ?, ?)
                                    """, [
                                        (cursor.lastrowid, order, section)
                                        for order, section in enumerate(imported_preferences, start=1)
                                    ])

                                added += 1

                            except sqlite3.IntegrityError:
                                skipped += 1
                                upload_errors.append(
                                    f"Row {row_number}: Enrollment "
                                    f"{enrollment_no} already exists."
                                )

                        connection.commit()

                        message = (
                            f"Upload completed: {added} student(s) "
                            f"added and {skipped} row(s) skipped."
                        )

            except Exception:
                if connection:
                    connection.rollback()

                message = (
                    "Unable to read the Excel file. Check that it is "
                    "a valid .xlsx file with the required column headers."
                )

            finally:
                if connection:
                    connection.close()

                if workbook:
                    workbook.close()

    search = request.args.get("search", "").strip()
    program = request.args.get("program", "").strip()

    connection = get_db_connection()
    try:
        connection.execute("ALTER TABLE students ADD COLUMN cgpa REAL")
    except sqlite3.OperationalError:
        pass
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            UNIQUE (section_name, program)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            section_id INTEGER NOT NULL,
            cgpa_band TEXT NOT NULL,
            allocated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    query = """
        SELECT
            s.*,
            (
                SELECT sec.section_name
                FROM allocations a
                JOIN sections sec ON sec.id = a.section_id
                WHERE a.student_id = s.id
            ) AS allocation,
            COALESCE(
                (
                    SELECT payment_status
                    FROM fee_payments
                    WHERE enrollment_no = s.enrollment_no
                    ORDER BY id DESC
                    LIMIT 1
                ),
                'Not Verified'
            ) AS fee_status
        FROM students s
        WHERE 1 = 1
    """

    parameters = []

    if search:
        query += """
            AND (
                s.enrollment_no LIKE ?
                OR s.student_name LIKE ?
            )
        """
        parameters.extend([
            "%" + search + "%",
            "%" + search + "%"
        ])

    if program:
        query += " AND s.program = ?"
        parameters.append(program)

    query += " ORDER BY s.id ASC"

    students = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return render_template(
        "admin/manage_std.html",
        students=students,
        search=search,
        program=program,
        message=message,
        upload_errors=upload_errors[:10]
    )


# =========================================================
# SECTION CAPACITY
# =========================================================

@app.route("/admin/section-capacity", methods=["GET", "POST"])
def section_capacity():

    message = None
    error = None
    connection = get_db_connection()

    # Create the table here so existing installations are upgraded
    # automatically when an administrator first opens this page.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            UNIQUE (section_name, program)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            section_id INTEGER NOT NULL,
            cgpa_band TEXT NOT NULL,
            allocated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    if request.method == "POST":
        action = request.form.get("action", "add")
        section_name = request.form.get("section_name", "").strip()
        program = request.form.get("program", "").strip()

        try:
            capacity = int(request.form.get("capacity", ""))
        except ValueError:
            capacity = 0

        if action != "add":
            error = "That section action is not supported."
        elif not section_name or not program:
            error = "Section name and program are required."
        elif capacity < 1:
            error = "Seat capacity must be at least 1."
        else:
            try:
                connection.execute("""
                    INSERT INTO sections (section_name, program, capacity)
                    VALUES (?, ?, ?)
                """, (section_name, program, capacity))
                connection.commit()
                message = "Section added successfully."
            except sqlite3.IntegrityError:
                error = "That section already exists for this program."

    sections = connection.execute("""
        SELECT sec.section_name, sec.program, sec.capacity,
               COUNT(a.id) AS allocated,
               sec.capacity - COUNT(a.id) AS available
        FROM sections sec
        LEFT JOIN allocations a ON a.section_id = sec.id
        GROUP BY sec.id
        ORDER BY sec.program, sec.section_name
    """).fetchall()

    connection.close()

    return render_template(
        "admin/manage_sections.html",
        sections=sections,
        message=message,
        error=error
    )


# =========================================================
# CGPA CONSTRAINTS
# =========================================================

@app.route("/admin/cgpa-constraints", methods=["GET", "POST"])
def cgpa_constraints():

    programs = ["CSE", "AI&DS", "AI&ML", "AI", "EEE", "ECE"]
    message = None
    error = None
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS cgpa_constraints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program TEXT NOT NULL UNIQUE,
            minimum_cgpa REAL,
            medium_cgpa REAL,
            maximum_cgpa REAL,
            low_students INTEGER NOT NULL DEFAULT 20,
            medium_students INTEGER NOT NULL DEFAULT 20,
            high_students INTEGER NOT NULL DEFAULT 20
        )
    """)

    # Add the new band and student-count columns to databases created
    # by the earlier single-threshold version of this page.
    for column, definition in (
        ("medium_cgpa", "REAL"),
        ("maximum_cgpa", "REAL"),
        ("low_students", "INTEGER NOT NULL DEFAULT 20"),
        ("medium_students", "INTEGER NOT NULL DEFAULT 20"),
        ("high_students", "INTEGER NOT NULL DEFAULT 20"),
    ):
        try:
            connection.execute(
                f"ALTER TABLE cgpa_constraints ADD COLUMN {column} {definition}"
            )
        except sqlite3.OperationalError:
            pass

    if request.method == "POST":
        program = request.form.get("program", "").strip()
        cgpa_fields = ("minimum_cgpa", "medium_cgpa", "maximum_cgpa")
        count_fields = ("low_students", "medium_students", "high_students")
        try:
            cgpa_values = [float(request.form.get(key, "")) for key in cgpa_fields]
            count_values = [int(request.form.get(key, "")) for key in count_fields]
        except ValueError:
            cgpa_values = []
            count_values = []

        if program not in programs:
            error = "Select a valid program."
        elif len(cgpa_values) != 3 or len(count_values) != 3:
            error = "Enter all three CGPA values and all three student counts."
        elif any(value < 0 or value > 10 for value in cgpa_values):
            error = "CGPA values must be between 0 and 10."
        elif cgpa_values != sorted(cgpa_values):
            error = "CGPA values must be ordered from minimum to medium to maximum."
        elif any(value < 0 for value in count_values):
            error = "Student counts cannot be negative."
        else:
            connection.execute("""
                INSERT INTO cgpa_constraints (
                    program, minimum_cgpa, medium_cgpa, maximum_cgpa,
                    low_students, medium_students, high_students
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(program) DO UPDATE SET
                    minimum_cgpa = excluded.minimum_cgpa,
                    medium_cgpa = excluded.medium_cgpa,
                    maximum_cgpa = excluded.maximum_cgpa,
                    low_students = excluded.low_students,
                    medium_students = excluded.medium_students,
                    high_students = excluded.high_students
            """, (program, *cgpa_values, *count_values))
            connection.commit()
            message = f"CGPA bands and student counts for {program} saved successfully."

    saved_constraints = connection.execute("""
        SELECT program, minimum_cgpa, medium_cgpa, maximum_cgpa,
               low_students, medium_students, high_students
        FROM cgpa_constraints
    """).fetchall()
    saved_by_program = {row["program"]: row for row in saved_constraints}
    program_configs = []
    for program in programs:
        saved = saved_by_program.get(program)
        program_configs.append({
            "program": program,
            "minimum_cgpa": saved["minimum_cgpa"] if saved else "",
            "medium_cgpa": saved["medium_cgpa"] if saved else "",
            "maximum_cgpa": saved["maximum_cgpa"] if saved else "",
            "low_students": saved["low_students"] if saved else 20,
            "medium_students": saved["medium_students"] if saved else 20,
            "high_students": saved["high_students"] if saved else 20,
        })
    connection.close()

    return render_template(
        "admin/cgpa_constraints.html",
        program_configs=program_configs,
        message=message,
        error=error
    )


# =========================================================
# FINAL SECTION ALLOCATION
# =========================================================

@app.route("/admin/allocation", methods=["GET", "POST"])
def allocation_management():

    message = None
    error = None
    connection = get_db_connection()

    # Keep the allocation page usable with databases created before these
    # features were added.
    try:
        connection.execute("ALTER TABLE students ADD COLUMN cgpa REAL")
    except sqlite3.OperationalError:
        pass

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            UNIQUE (section_name, program)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS student_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            preference_order INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (student_id, preference_order),
            UNIQUE (student_id, section_name)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS cgpa_constraints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program TEXT NOT NULL UNIQUE,
            minimum_cgpa REAL,
            medium_cgpa REAL,
            maximum_cgpa REAL,
            low_students INTEGER NOT NULL DEFAULT 20,
            medium_students INTEGER NOT NULL DEFAULT 20,
            high_students INTEGER NOT NULL DEFAULT 20
        )
    """)
    for column, definition in (
        ("medium_cgpa", "REAL"),
        ("maximum_cgpa", "REAL"),
        ("low_students", "INTEGER NOT NULL DEFAULT 20"),
        ("medium_students", "INTEGER NOT NULL DEFAULT 20"),
        ("high_students", "INTEGER NOT NULL DEFAULT 20"),
    ):
        try:
            connection.execute(
                f"ALTER TABLE cgpa_constraints ADD COLUMN {column} {definition}"
            )
        except sqlite3.OperationalError:
            pass

    connection.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            section_id INTEGER NOT NULL,
            cgpa_band TEXT NOT NULL,
            allocated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (section_id) REFERENCES sections(id)
        )
    """)

    if request.method == "POST":
        constraints = connection.execute("""
            SELECT * FROM cgpa_constraints ORDER BY program
        """).fetchall()
        if not constraints:
            error = "Set and save CGPA constraints before running allocation."
        else:
            student_programs = {
                row["program"] for row in connection.execute(
                    "SELECT DISTINCT program FROM students"
                ).fetchall()
            }
            configured_programs = {rule["program"] for rule in constraints}
            invalid_programs = [
                rule["program"] for rule in constraints
                if (
                    rule["minimum_cgpa"] is None
                    or rule["medium_cgpa"] is None
                    or rule["maximum_cgpa"] is None
                    or not (
                        0 <= rule["minimum_cgpa"]
                        <= rule["medium_cgpa"]
                        <= rule["maximum_cgpa"]
                        <= 10
                    )
                    or any(
                        rule[key] is None or rule[key] < 0
                        for key in ("low_students", "medium_students", "high_students")
                    )
                )
            ]
            invalid_programs.extend(sorted(student_programs - configured_programs))
            if invalid_programs:
                error = "Save valid CGPA rules for every program with students: " + ", ".join(sorted(set(invalid_programs))) + "."
                constraints = []
            else:
                connection.execute("DELETE FROM allocations")

            allocated_count = 0
            missing_cgpa = 0
            missing_preferences = 0
            unfilled_capacity = 0

            for rule in constraints:
                program = rule["program"]
                minimum = rule["minimum_cgpa"]
                medium = rule["medium_cgpa"]
                maximum = rule["maximum_cgpa"]
                quotas = {
                    "low": rule["low_students"],
                    "medium": rule["medium_students"],
                    "high": rule["high_students"],
                }
                section_rows = connection.execute("""
                    SELECT id, section_name, capacity
                    FROM sections WHERE program = ?
                    ORDER BY section_name
                """, (program,)).fetchall()
                if not section_rows:
                    continue

                sections_by_name = {row["section_name"]: row for row in section_rows}
                seats_left = {row["id"]: row["capacity"] for row in section_rows}
                students = connection.execute("""
                    SELECT id, student_name, enrollment_no, cgpa
                    FROM students WHERE program = ?
                """, (program,)).fetchall()

                preferences_by_student = {}
                if students:
                    student_ids = [student["id"] for student in students]
                    placeholders = ",".join("?" for _ in student_ids)
                    preference_rows = connection.execute(f"""
                        SELECT student_id, section_name, preference_order
                        FROM student_preferences
                        WHERE student_id IN ({placeholders})
                        ORDER BY preference_order
                    """, student_ids).fetchall()
                    for preference in preference_rows:
                        preferences_by_student.setdefault(
                            preference["student_id"], []
                        ).append(preference["section_name"])

                bands = {"low": [], "medium": [], "high": []}
                for student in students:
                    cgpa = student["cgpa"]
                    if cgpa is None:
                        missing_cgpa += 1
                    elif cgpa < minimum:
                        continue
                    elif cgpa < medium:
                        bands["low"].append(student)
                    elif cgpa < maximum:
                        bands["medium"].append(student)
                    else:
                        bands["high"].append(student)

                for band in ("high", "medium", "low"):
                    candidates = sorted(
                        bands[band],
                        key=lambda item: (-item["cgpa"], item["enrollment_no"])
                    )
                    band_allocated = 0

                    for student in candidates:
                        if band_allocated >= quotas[band]:
                            break
                        preferences = preferences_by_student.get(student["id"], [])
                        if not preferences:
                            missing_preferences += 1
                            continue

                        target_section = None
                        for section_name in preferences:
                            section = sections_by_name.get(section_name)
                            if (
                                section
                                and seats_left[section["id"]] > 0
                            ):
                                target_section = section
                                break

                        if target_section is None:
                            unfilled_capacity += 1
                            continue

                        connection.execute("""
                            INSERT INTO allocations (student_id, section_id, cgpa_band)
                            VALUES (?, ?, ?)
                        """, (student["id"], target_section["id"], band))
                        seats_left[target_section["id"]] -= 1
                        allocated_count += 1
                        band_allocated += 1

            connection.commit()
            if not error:
                message = (
                    f"Allocation completed: {allocated_count} student(s) assigned. "
                    f"{missing_cgpa} missing CGPA, {missing_preferences} missing preferences, "
                    f"and {unfilled_capacity} could not fit a preferred section."
                )

    section_summary = connection.execute("""
        SELECT sec.program, sec.section_name, sec.capacity,
               COUNT(a.id) AS allocated,
               sec.capacity - COUNT(a.id) AS available
        FROM sections sec
        LEFT JOIN allocations a ON a.section_id = sec.id
        GROUP BY sec.id
        ORDER BY sec.program, sec.section_name
    """).fetchall()

    allocation_rows = connection.execute("""
        SELECT s.student_name, s.enrollment_no, s.program, s.cgpa,
               sec.section_name, a.cgpa_band
        FROM students s
        LEFT JOIN allocations a ON a.student_id = s.id
        LEFT JOIN sections sec ON sec.id = a.section_id
        ORDER BY s.program, s.student_name COLLATE NOCASE
    """).fetchall()

    connection.close()
    return render_template(
        "admin/alloaction_management.html",
        section_summary=section_summary,
        allocation_rows=allocation_rows,
        message=message,
        error=error
    )

# =========================================================
# EDIT STUDENT
# =========================================================

@app.route("/admin/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    connection = get_db_connection()
    try:
        connection.execute("ALTER TABLE students ADD COLUMN cgpa REAL")
    except sqlite3.OperationalError:
        pass

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if student is None:
        connection.close()
        return "Student not found", 404

    if request.method == "POST":

        student_name = request.form.get("student_name", "").strip()
        enrollment_no = request.form.get("enrollment_no", "").strip()
        program = request.form.get("program", "").strip()
        dob = request.form.get("dob", "").strip()
        email = request.form.get("email", "").strip()
        batch = request.form.get("batch", "").strip()
        password = request.form.get("password", "").strip()
        cgpa_raw = request.form.get("cgpa", "").strip()

        try:
            cgpa = float(cgpa_raw) if cgpa_raw else None
        except ValueError:
            cgpa = -1

        if not student_name or not enrollment_no or not program:
            connection.close()
            return render_template(
                "admin/edit_student.html",
                student=student,
                error="Name, enrollment number and program are required."
            )

        if cgpa is not None and not 0 <= cgpa <= 10:
            connection.close()
            return render_template(
                "admin/edit_student.html",
                student=student,
                error="CGPA must be a number from 0 to 10."
            )

        try:
            if password:
                connection.execute("""
                    UPDATE students
                    SET student_name = ?,
                        enrollment_no = ?,
                        program = ?,
                        dob = ?,
                        email = ?,
                        batch = ?,
                        cgpa = ?,
                        password = ?
                    WHERE id = ?
                """, (
                    student_name, enrollment_no, program,
                    dob, email, batch, cgpa, password, student_id
                ))
            else:
                connection.execute("""
                    UPDATE students
                    SET student_name = ?,
                        enrollment_no = ?,
                        program = ?,
                        dob = ?,
                        email = ?,
                        batch = ?,
                        cgpa = ?
                    WHERE id = ?
                """, (
                    student_name, enrollment_no, program,
                    dob, email, batch, cgpa, student_id
                ))

            connection.commit()
            connection.close()

            return redirect("/admin/student-management")

        except sqlite3.IntegrityError:
            connection.close()
            return render_template(
                "admin/edit_student.html",
                student=student,
                error="That enrollment number already exists."
            )

    connection.close()

    return render_template(
        "admin/edit_student.html",
        student=student
    )


# =========================================================
# DELETE STUDENT
# =========================================================

@app.route("/admin/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):

    connection = get_db_connection()

    student = connection.execute(
        "SELECT id FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if student is None:
        connection.close()
        return "Student not found", 404

    connection.execute(
        "DELETE FROM fee_payments WHERE enrollment_no = "
        "(SELECT enrollment_no FROM students WHERE id = ?)",
        (student_id,)
    )

    connection.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/admin/student-management")
# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student/dashboard")
def student_dashboard():

    student_id = session.get("student_id")
    if not student_id:
        return redirect("/")

    connection = get_db_connection()
    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    if student is None:
        connection.close()
        session.pop("student_id", None)
        return redirect("/")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS student_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            preference_order INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (student_id, preference_order),
            UNIQUE (student_id, section_name)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            UNIQUE (section_name, program)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            section_id INTEGER NOT NULL,
            cgpa_band TEXT NOT NULL,
            allocated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    preferences = connection.execute("""
        SELECT section_name FROM student_preferences
        WHERE student_id = ? ORDER BY preference_order
    """, (student_id,)).fetchall()
    allocation = connection.execute("""
        SELECT sec.section_name
        FROM allocations a
        JOIN sections sec ON sec.id = a.section_id
        WHERE a.student_id = ?
    """, (student_id,)).fetchone()
    fee = connection.execute("""
        SELECT payment_status FROM fee_payments
        WHERE enrollment_no = ? ORDER BY id DESC LIMIT 1
    """, (student["enrollment_no"],)).fetchone()
    connection.close()

    return render_template(
        "student/dashboard.html",
        student=student,
        preferences=preferences,
        allocation=allocation,
        fee_status=fee["payment_status"] if fee else "Not Verified"
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

@app.route("/student/profile")
def student_profile():

    student_id = session.get("student_id")
    if not student_id:
        return redirect("/")

    connection = get_db_connection()

    student = connection.execute("""
        SELECT * FROM students WHERE id = ?
    """, (student_id,)).fetchone()

    connection.close()

    if student is None:
        return "Student profile not found in database."

    return render_template(
        "student/profile.html",
        student=student
    )


# =========================================================
# FEE VERIFICATION
# =========================================================

@app.route(
    "/student/fee-verification",
    methods=["GET", "POST"]
)
def fee_verification():

    error = None
    student_id = session.get("student_id")
    if not student_id:
        return redirect("/")

    connection = get_db_connection()
    student = connection.execute(
        "SELECT id, student_name, enrollment_no FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    if student is None:
        connection.close()
        session.pop("student_id", None)
        return redirect("/")
    connection.close()


    # -----------------------------------------------------
    # STUDENT SUBMITS ORDER ID
    # -----------------------------------------------------

    if request.method == "POST":

        # Get Order ID entered by student
        order_id = request.form.get(
            "order_id",
            ""
        ).strip()


        # Connect to database
        connection = get_db_connection()


        # Search Order ID
        payment = connection.execute("""
            SELECT
                student_name,
                enrollment_no,
                order_id,
                payment_status

            FROM fee_payments

            WHERE order_id = ?
            AND enrollment_no = ?
        """, (
            order_id,
            student["enrollment_no"],
        )).fetchone()


        # Close database
        connection.close()


        # -------------------------------------------------
        # VERIFIED PAYMENT
        # -------------------------------------------------

        if (
            payment
            and
            payment["payment_status"] == "Verified"
        ):

            return render_template(
                "student/fee_status_verified.html",

                student_name=payment["student_name"],

                enrollment_no=payment["enrollment_no"],

                order_id=payment["order_id"]
            )


        # -------------------------------------------------
        # INVALID PAYMENT
        # -------------------------------------------------

        error = (
            "Invalid Order ID. Please enter the Order ID "
            "received from your college email."
        )


    # Display fee verification page
    return render_template(
        "student/fee_verification.html",
        student=student,
        error=error
    )


# =========================================================
# LIVE BASKET FILLING
# =========================================================

@app.route("/student/live-basket-filling")
def live_basket_filling():

    student_id = session.get("student_id")
    if not student_id:
        return redirect("/")

    connection = get_db_connection()
    student = connection.execute(
        "SELECT id, student_name, enrollment_no, program FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    if student is None:
        connection.close()
        session.pop("student_id", None)
        return redirect("/")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            UNIQUE (section_name, program)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            section_id INTEGER NOT NULL,
            cgpa_band TEXT NOT NULL,
            allocated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    section_rows = connection.execute("""
        SELECT sec.section_name, sec.program, sec.capacity,
               COUNT(a.id) AS filled,
               sec.capacity - COUNT(a.id) AS available
        FROM sections sec
        LEFT JOIN allocations a ON a.section_id = sec.id
        GROUP BY sec.id
        ORDER BY sec.program, sec.section_name
    """).fetchall()
    connection.close()

    allowed_sections = {
        "CSE": {"A", "B", "C", "D"},
        "AI&DS": {"E", "F", "G"},
        "AI&ML": {"H", "I"},
        "AI": {"J", "K"},
        "EEE": {"L", "M"},
        "ECE": {"N", "O"},
    }
    program_aliases = {
        "AIDS": "AI&DS", "AIML": "AI&ML",
    }

    # Older section entries may be named both "A" and "section A" for
    # the same program. Normalize those labels and combine them into one row.
    section_groups = {}
    for section in section_rows:
        program = program_aliases.get(section["program"].strip().upper(), section["program"].strip())
        section_name = section["section_name"].strip()
        if section_name.lower().startswith("section "):
            section_name = section_name[8:].strip()
        if section_name not in allowed_sections.get(program, set()):
            continue

        key = (program, section_name)
        group = section_groups.setdefault(key, {
            "program": program,
            "section_name": section_name,
            "capacity": 0,
            "filled": 0,
        })
        group["capacity"] = max(group["capacity"], section["capacity"])
        group["filled"] += section["filled"]

    sections = []
    for section in sorted(section_groups.values(), key=lambda row: (row["program"], row["section_name"])):
        capacity = section["capacity"]
        filled = section["filled"]
        available = max(0, capacity - filled)
        percent = round(filled * 100 / capacity) if capacity else 0
        sections.append({
            **section,
            "available": available,
            "percent": min(percent, 100),
            "status": (
                "Full" if available == 0
                else "Almost Full" if percent >= 85
                else "Available"
            )
        })

    return render_template(
        "student/live_basket_filling.html",
        student=student,
        sections=sections
    )


# =========================================================
# SECTION PREFERENCES
# =========================================================

@app.route("/student/section-preferences", methods=["GET", "POST"])
def section_preferences():

    student_id = session.get("student_id")
    if not student_id:
        return redirect("/")

    connection = get_db_connection()
    student = connection.execute(
        "SELECT id, student_name, enrollment_no, program FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    if student is None:
        connection.close()
        session.pop("student_id", None)
        return redirect("/")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS student_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            preference_order INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (student_id, preference_order),
            UNIQUE (student_id, section_name),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    program_aliases = {
        "AIDS": "AI&DS", "AI&DS": "AI&DS",
        "AIML": "AI&ML", "AI&ML": "AI&ML",
        "CSE": "CSE", "AI": "AI", "EEE": "EEE", "ECE": "ECE",
    }
    program = program_aliases.get(student["program"].strip().upper())
    sections_by_program = {
        "CSE": ["A", "B", "C", "D"],
        "AI&DS": ["E", "F", "G"],
        "AI&ML": ["H", "I"],
        "AI": ["J", "K"],
        "EEE": ["L", "M"],
        "ECE": ["N", "O"],
    }
    section_options = sections_by_program.get(program, [])

    # Ensure the preference choices also exist for allocation, including when
    # the page is opened under a server that did not run create_database().
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            UNIQUE (section_name, program)
        )
    """)
    for section_name in section_options:
        connection.execute("""
            INSERT OR IGNORE INTO sections (section_name, program, capacity)
            VALUES (?, ?, 50)
        """, (section_name, program))

    message = None
    error = None
    if request.method == "POST":
        selections = [
            request.form.get(f"preference_{number}", "").strip()
            for number in range(1, 5)
        ]
        selected = [value for value in selections if value]

        if not selected:
            error = "Choose at least one preferred section."
        elif len(selected) != len(set(selected)):
            error = "Choose each section only once."
        elif any(value not in section_options for value in selected):
            error = "One or more selected sections are not available for your program."
        else:
            connection.execute(
                "DELETE FROM student_preferences WHERE student_id = ?",
                (student_id,)
            )
            connection.executemany("""
                INSERT INTO student_preferences (student_id, preference_order, section_name)
                VALUES (?, ?, ?)
            """, [
                (student_id, order, section)
                for order, section in enumerate(selected, start=1)
            ])
            connection.commit()
            message = "Your section preferences have been saved."

    saved_rows = connection.execute("""
        SELECT preference_order, section_name
        FROM student_preferences
        WHERE student_id = ?
        ORDER BY preference_order
    """, (student_id,)).fetchall()
    saved_preferences = {
        row["preference_order"]: row["section_name"] for row in saved_rows
    }
    connection.close()

    return render_template(
        "student/section_preferences.html",
        student=student,
        section_options=section_options,
        saved_preferences=saved_preferences,
        message=message,
        error=error
    )


@app.route("/admin/preferences")
def admin_preferences():

    search = request.args.get("search", "").strip()
    connection = get_db_connection()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS student_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            preference_order INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (student_id, preference_order),
            UNIQUE (student_id, section_name),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    sql = """
        SELECT s.id, s.student_name, s.enrollment_no, s.program,
               p.preference_order, p.section_name, p.updated_at
        FROM students s
        LEFT JOIN student_preferences p ON p.student_id = s.id
        WHERE 1 = 1
    """
    parameters = []
    if search:
        sql += " AND (s.student_name LIKE ? OR s.enrollment_no LIKE ?)"
        parameters.extend((f"%{search}%", f"%{search}%"))
    sql += " ORDER BY s.student_name COLLATE NOCASE, p.preference_order"
    rows = connection.execute(sql, parameters).fetchall()
    connection.close()

    students_by_id = {}
    for row in rows:
        student_entry = students_by_id.setdefault(row["id"], {
            "student_name": row["student_name"],
            "enrollment_no": row["enrollment_no"],
            "program": row["program"],
            "preferences": []
        })
        if row["section_name"]:
            student_entry["preferences"].append(row["section_name"])

    return render_template(
        "admin/student_preferences.html",
        students=list(students_by_id.values()),
        search=search
    )


# =========================================================
# ALLOCATION STATUS
# =========================================================

@app.route("/student/allocation-status")
def allocation_status():

    student_id = session.get("student_id")
    if not student_id:
        return redirect("/")

    connection = get_db_connection()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT NOT NULL,
            program TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            UNIQUE (section_name, program)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL UNIQUE,
            section_id INTEGER NOT NULL,
            cgpa_band TEXT NOT NULL,
            allocated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    student = connection.execute("""
        SELECT s.student_name, s.enrollment_no, s.program, s.cgpa,
               sec.section_name, a.cgpa_band, a.allocated_at
        FROM students s
        LEFT JOIN allocations a ON a.student_id = s.id
        LEFT JOIN sections sec ON sec.id = a.section_id
        WHERE s.id = ?
    """, (student_id,)).fetchone()
    connection.close()

    if student is None:
        session.pop("student_id", None)
        return redirect("/")

    return render_template(
        "student/allocation_status.html",
        student=student
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    # Local testing shortcut: use this password with any student ID while
    # running app.py directly. It is not enabled by a production WSGI server.
    app.config["LOCAL_STUDENT_TEST_PASSWORD"] = os.environ.get(
        "LOCAL_STUDENT_TEST_PASSWORD",
        "college@123"
    )

    # Create database and tables
    create_database()


    # Display application information
    print()
    print("==============================================")
    print("       SectionSync Flask Application")
    print("==============================================")

    print()
    print("Project Folder:")
    print(BASE_DIR)

    print()
    print("Database:")
    print(DATABASE)

    print()
    print("Templates:")
    print(
        os.path.join(
            BASE_DIR,
            "templates"
        )
    )

    print()
    print("==============================================")
    print("Application starting...")
    print("==============================================")
    print()


    # Start Flask server
    app.run(debug=True)
