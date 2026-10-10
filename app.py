from flask import Flask, render_template, request, redirect
import sqlite3
import os


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


        # Check credentials in students table
        student = connection.execute("""
            SELECT *
            FROM students

            WHERE enrollment_no = ?
            AND password = ?
        """, (
            enrollment_no,
            password
        )).fetchone()


        # Close connection
        connection.close()


        # Successful login
        if student:

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

@app.route("/admin/student-management")
def student_management():

    search = request.args.get(
        "search",
        ""
    ).strip()

    program = request.args.get(
        "program",
        ""
    ).strip()


    connection = get_db_connection()


    query = """
        SELECT
            s.*,
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

        parameters.append(
            "%" + search + "%"
        )

        parameters.append(
            "%" + search + "%"
        )


    if program:

        query += """
            AND s.program = ?
        """

        parameters.append(program)


    query += """
        ORDER BY s.id ASC
    """


    students = connection.execute(
        query,
        parameters
    ).fetchall()


    connection.close()


    return render_template(
        "admin/manage_std.html",
        students=students,
        search=search,
        program=program
    )
# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student/dashboard")
def student_dashboard():

    return render_template(
        "student/dashboard.html"
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

@app.route("/student/profile")
def student_profile():

    connection = get_db_connection()

    student = connection.execute("""
        SELECT
            student_name,
            enrollment_no,
            dob,
            email,
            program,
            batch
        FROM students
        WHERE enrollment_no = ?
    """, ("24STUCHH010618",)).fetchone()

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
        """, (
            order_id,
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
        error=error
    )


# =========================================================
# LIVE BASKET FILLING
# =========================================================

@app.route("/student/live-basket-filling")
def live_basket_filling():

    return render_template(
        "student/live_basket_filling.html"
    )


# =========================================================
# SECTION PREFERENCES
# =========================================================

@app.route("/student/section-preferences")
def section_preferences():

    return render_template(
        "student/section_preferences.html"
    )


# =========================================================
# ALLOCATION STATUS
# =========================================================

@app.route("/student/allocation-status")
def allocation_status():

    return render_template(
        "student/allocation_status.html"
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

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