from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import mysql.connector


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "campus_placement_secret_key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="campus_placement_db"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# STUDENT REGISTER
# AUTOMATIC REGISTER NUMBER
# =========================================================

@app.route("/student-register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()
        password = request.form.get("password", "").strip()

        # Check fields
        if not all([
            name,
            email,
            phone,
            department,
            year,
            password
        ]):

            flash(
                "Please fill all fields.",
                "error"
            )

            return redirect(
                url_for("student_register")
            )

        conn = None
        cursor = None

        try:

            conn = get_db_connection()

            cursor = conn.cursor(
                dictionary=True
            )

            # -------------------------------------------------
            # CHECK EMAIL
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM students
                WHERE email = %s
                """,
                (email,)
            )

            existing_student = cursor.fetchone()

            if existing_student:

                flash(
                    "This email is already registered.",
                    "error"
                )

                return redirect(
                    url_for("student_register")
                )

            # -------------------------------------------------
            # GET LAST REGISTER NUMBER
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT register_no
                FROM students
                WHERE register_no LIKE 'STU%'
                ORDER BY id DESC
                LIMIT 1
                """
            )

            last_student = cursor.fetchone()

            if last_student and last_student["register_no"]:

                try:

                    last_number = int(
                        last_student["register_no"]
                        .replace("STU", "")
                    )

                    next_number = last_number + 1

                except ValueError:

                    next_number = 1

            else:

                next_number = 1

            # -------------------------------------------------
            # GENERATE REGISTER NUMBER
            # -------------------------------------------------

            register_no = f"STU{next_number:04d}"

            # -------------------------------------------------
            # CHECK REGISTER NUMBER
            # -------------------------------------------------

            while True:

                cursor.execute(
                    """
                    SELECT id
                    FROM students
                    WHERE register_no = %s
                    """,
                    (register_no,)
                )

                existing_register = cursor.fetchone()

                if not existing_register:
                    break

                next_number += 1

                register_no = f"STU{next_number:04d}"

            # -------------------------------------------------
            # INSERT STUDENT
            # -------------------------------------------------

            cursor.execute(
                """
                INSERT INTO students
                (
                    name,
                    register_no,
                    email,
                    phone,
                    department,
                    year,
                    password
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    register_no,
                    email,
                    phone,
                    department,
                    year,
                    password
                )
            )

            conn.commit()

            flash(
                f"Account created successfully! "
                f"Your Register Number is {register_no}.",
                "success"
            )

            return redirect(
                url_for("student_login")
            )

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "Student registration error:",
                e
            )

            flash(
                f"Registration failed: {e}",
                "error"
            )

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

    return render_template(
        "student_register.html"
    )


# =========================================================
# STUDENT LOGIN
# EMAIL OR REGISTER NUMBER
# =========================================================

@app.route("/student-login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        login_value = request.form.get(
            "login",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if not login_value or not password:

            flash(
                "Please enter email/register number and password.",
                "error"
            )

            return redirect(
                url_for("student_login")
            )

        conn = None
        cursor = None

        try:

            conn = get_db_connection()

            cursor = conn.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM students
                WHERE
                    (
                        email = %s
                        OR register_no = %s
                    )
                    AND password = %s
                """,
                (
                    login_value,
                    login_value,
                    password
                )
            )

            student = cursor.fetchone()

            if student:

                # Clear old student session
                session.pop("student_id", None)
                session.pop("student_name", None)
                session.pop("register_no", None)
                session.pop("student_email", None)

                # Store CURRENT logged-in student
                session["student_id"] = student["id"]
                session["student_name"] = student["name"]
                session["register_no"] = student["register_no"]
                session["student_email"] = student["email"]

                return redirect(
                    url_for("student_dashboard")
                )

            flash(
                "Invalid email/register number or password.",
                "error"
            )

        except Exception as e:

            print(
                "Student login error:",
                e
            )

            flash(
                f"Login error: {e}",
                "error"
            )

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

    return render_template(
        "student_login.html"
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        # Get CURRENT logged-in student
        cursor.execute(
            """
            SELECT *
            FROM students
            WHERE id = %s
            """,
            (
                session["student_id"],
            )
        )

        student = cursor.fetchone()

        if not student:

            session.clear()

            flash(
                "Student account not found.",
                "error"
            )

            return redirect(
                url_for("student_login")
            )

        # Get CURRENT student's applications
        cursor.execute(
            """
            SELECT
                applications.id,
                applications.status,
                applications.applied_at,
                companies.company_name,
                companies.job_role,
                companies.salary

            FROM applications

            INNER JOIN companies
                ON applications.company_id = companies.id

            WHERE applications.student_id = %s

            ORDER BY applications.applied_at DESC
            """,
            (
                session["student_id"],
            )
        )

        applications = cursor.fetchall()

        return render_template(
            "student_dashboard.html",
            student=student,
            applications=applications
        )

    except Exception as e:

        print(
            "Student dashboard error:",
            e
        )

        flash(
            f"Could not load dashboard: {e}",
            "error"
        )

        return redirect(
            url_for("student_login")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# STUDENT PROFILE
# =========================================================

@app.route("/student-profile/<int:student_id>")
def student_profile(student_id):

    # Admin must be logged in
    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # GET STUDENT
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM students
            WHERE id = %s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for("student_management")
            )

        # -------------------------------------------------
        # GET STUDENT APPLICATIONS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                applications.id,
                applications.status,
                applications.applied_at,

                companies.company_name,
                companies.job_role,
                companies.salary

            FROM applications

            INNER JOIN companies
                ON applications.company_id = companies.id

            WHERE applications.student_id = %s

            ORDER BY applications.applied_at DESC
            """,
            (student_id,)
        )

        applications = cursor.fetchall()

        # -------------------------------------------------
        # OPEN PROFILE
        # -------------------------------------------------

        return render_template(
            "student_profile.html",
            student=student,
            applications=applications
        )

    except Exception as e:

        print(
            "Student profile error:",
            e
        )

        flash(
            f"Could not load student profile: {e}",
            "error"
        )

        return redirect(
            url_for("student_management")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# COMPANIES FOR STUDENTS
# =========================================================

@app.route("/companies")
def companies():

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM companies
            ORDER BY id DESC
            """
        )

        companies_list = cursor.fetchall()

        return render_template(
            "companies.html",
            companies=companies_list
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# APPLY FOR COMPANY
# =========================================================

@app.route(
    "/apply/<int:company_id>",
    methods=["POST"]
)
def apply_company(company_id):

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    student_id = session["student_id"]

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        # Check company
        cursor.execute(
            """
            SELECT *
            FROM companies
            WHERE id = %s
            """,
            (company_id,)
        )

        company = cursor.fetchone()

        if not company:

            flash(
                "Company not found.",
                "error"
            )

            return redirect(
                url_for("companies")
            )

        # Check duplicate application
        cursor.execute(
            """
            SELECT id
            FROM applications
            WHERE student_id = %s
            AND company_id = %s
            """,
            (
                student_id,
                company_id
            )
        )

        existing_application = cursor.fetchone()

        if existing_application:

            flash(
                "You have already applied for this company.",
                "error"
            )

            return redirect(
                url_for("companies")
            )

        # Insert application
        cursor.execute(
            """
            INSERT INTO applications
            (
                student_id,
                company_id,
                status
            )
            VALUES
            (%s, %s, %s)
            """,
            (
                student_id,
                company_id,
                "Applied"
            )
        )

        conn.commit()

        flash(
            "Application submitted successfully!",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "Application error:",
            e
        )

        flash(
            f"Application failed: {e}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("companies")
    )


# =========================================================
# MY APPLICATIONS
# =========================================================

@app.route("/my-applications")
def my_applications():

    if "student_id" not in session:

        return redirect(
            url_for("student_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                applications.id,
                applications.status,
                applications.applied_at,
                companies.company_name,
                companies.job_role,
                companies.salary

            FROM applications

            INNER JOIN companies
                ON applications.company_id = companies.id

            WHERE applications.student_id = %s

            ORDER BY applications.applied_at DESC
            """,
            (
                session["student_id"],
            )
        )

        applications = cursor.fetchall()

        return render_template(
            "my_applications.html",
            applications=applications
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# STUDENT LOGOUT
# =========================================================

@app.route("/student-logout")
def student_logout():

    session.clear()

    return redirect(
        url_for("student_login")
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin-login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        conn = None
        cursor = None

        try:

            conn = get_db_connection()

            cursor = conn.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM admins
                WHERE username = %s
                AND password = %s
                """,
                (
                    username,
                    password
                )
            )

            admin = cursor.fetchone()

            if admin:

                session["admin_id"] = admin["id"]
                session["admin_username"] = admin["username"]

                return redirect(
                    url_for("admin_dashboard")
                )

            flash(
                "Invalid username or password.",
                "error"
            )

        except Exception as e:

            print(
                "Admin login error:",
                e
            )

            flash(
                f"Login error: {e}",
                "error"
            )

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        # Total students
        cursor.execute(
            """
            SELECT COUNT(*) AS total_students
            FROM students
            """
        )

        student_count = cursor.fetchone()["total_students"]

        # Total companies
        cursor.execute(
            """
            SELECT COUNT(*) AS total_companies
            FROM companies
            """
        )

        company_count = cursor.fetchone()["total_companies"]

        # Total applications
        cursor.execute(
            """
            SELECT COUNT(*) AS total_applications
            FROM applications
            """
        )

        application_count = cursor.fetchone()["total_applications"]

        return render_template(
            "admin_dashboard.html",
            student_count=student_count,
            company_count=company_count,
            application_count=application_count
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADD COMPANY
# =========================================================

@app.route(
    "/add-company",
    methods=["GET", "POST"]
)
def add_company():

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    if request.method == "POST":

        company_name = request.form.get(
            "company_name",
            ""
        ).strip()

        job_role = request.form.get(
            "job_role",
            ""
        ).strip()

        salary = request.form.get(
            "salary",
            ""
        ).strip()

        min_cgpa = request.form.get(
            "min_cgpa",
            ""
        ).strip()

        eligible_department = request.form.get(
            "eligible_department",
            ""
        ).strip()

        eligible_year = request.form.get(
            "eligible_year",
            ""
        ).strip()

        deadline = request.form.get(
            "deadline",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        conn = None
        cursor = None

        try:

            conn = get_db_connection()

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO companies
                (
                    company_name,
                    job_role,
                    salary,
                    min_cgpa,
                    eligible_department,
                    eligible_year,
                    deadline,
                    description
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    company_name,
                    job_role,
                    salary,
                    min_cgpa if min_cgpa else None,
                    eligible_department,
                    eligible_year,
                    deadline if deadline else None,
                    description
                )
            )

            conn.commit()

            flash(
                "Company added successfully!",
                "success"
            )

            return redirect(
                url_for("company_management")
            )

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                "Company error:",
                e
            )

            flash(
                f"Company could not be added: {e}",
                "error"
            )

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

    return render_template(
        "add_company.html"
    )


# =========================================================
# COMPANY MANAGEMENT
# =========================================================

@app.route("/company-management")
def company_management():

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM companies
            ORDER BY id DESC
            """
        )

        companies_list = cursor.fetchall()

        return render_template(
            "company_management.html",
            companies=companies_list
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# EDIT COMPANY
# =========================================================

@app.route(
    "/edit-company/<int:company_id>",
    methods=["GET", "POST"]
)
def edit_company(company_id):

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM companies
            WHERE id = %s
            """,
            (company_id,)
        )

        company = cursor.fetchone()

        if not company:

            flash(
                "Company not found.",
                "error"
            )

            return redirect(
                url_for("company_management")
            )

        if request.method == "POST":

            company_name = request.form.get(
                "company_name",
                ""
            ).strip()

            job_role = request.form.get(
                "job_role",
                ""
            ).strip()

            salary = request.form.get(
                "salary",
                ""
            ).strip()

            min_cgpa = request.form.get(
                "min_cgpa",
                ""
            ).strip()

            eligible_department = request.form.get(
                "eligible_department",
                ""
            ).strip()

            eligible_year = request.form.get(
                "eligible_year",
                ""
            ).strip()

            deadline = request.form.get(
                "deadline",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            cursor.execute(
                """
                UPDATE companies

                SET
                    company_name = %s,
                    job_role = %s,
                    salary = %s,
                    min_cgpa = %s,
                    eligible_department = %s,
                    eligible_year = %s,
                    deadline = %s,
                    description = %s

                WHERE id = %s
                """,
                (
                    company_name,
                    job_role,
                    salary,
                    min_cgpa if min_cgpa else None,
                    eligible_department,
                    eligible_year,
                    deadline if deadline else None,
                    description,
                    company_id
                )
            )

            conn.commit()

            flash(
                "Company updated successfully!",
                "success"
            )

            return redirect(
                url_for("company_management")
            )

        return render_template(
            "edit_company.html",
            company=company
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "Edit company error:",
            e
        )

        flash(
            f"Company update failed: {e}",
            "error"
        )

        return redirect(
            url_for("company_management")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# DELETE COMPANY
# =========================================================

@app.route(
    "/delete-company/<int:company_id>",
    methods=["POST"]
)
def delete_company(company_id):

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        # Delete applications first
        cursor.execute(
            """
            DELETE FROM applications
            WHERE company_id = %s
            """,
            (company_id,)
        )

        # Delete company
        cursor.execute(
            """
            DELETE FROM companies
            WHERE id = %s
            """,
            (company_id,)
        )

        conn.commit()

        flash(
            "Company deleted successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "Delete company error:",
            e
        )

        flash(
            f"Company could not be deleted: {e}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("company_management")
    )


# =========================================================
# STUDENT MANAGEMENT
# =========================================================

@app.route("/student-management")
def student_management():

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                id,
                name,
                register_no,
                email,
                phone,
                department,
                year

            FROM students

            ORDER BY id DESC
            """
        )

        students = cursor.fetchall()

        return render_template(
            "student_management.html",
            students=students
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# EDIT STUDENT
# =========================================================

@app.route(
    "/edit-student/<int:student_id>",
    methods=["GET", "POST"]
)
def edit_student(student_id):

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM students
            WHERE id = %s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if not student:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for("student_management")
            )

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            department = request.form.get(
                "department",
                ""
            ).strip()

            year = request.form.get(
                "year",
                ""
            ).strip()

            cursor.execute(
                """
                UPDATE students

                SET
                    name = %s,
                    email = %s,
                    phone = %s,
                    department = %s,
                    year = %s

                WHERE id = %s
                """,
                (
                    name,
                    email,
                    phone,
                    department,
                    year,
                    student_id
                )
            )

            conn.commit()

            flash(
                "Student updated successfully.",
                "success"
            )

            return redirect(
                url_for("student_management")
            )

        return render_template(
            "edit_student.html",
            student=student
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "Edit student error:",
            e
        )

        flash(
            f"Student update failed: {e}",
            "error"
        )

        return redirect(
            url_for("student_management")
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# DELETE STUDENT
# =========================================================

@app.route(
    "/delete-student/<int:student_id>",
    methods=["POST"]
)
def delete_student(student_id):

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        # Delete applications first
        cursor.execute(
            """
            DELETE FROM applications
            WHERE student_id = %s
            """,
            (student_id,)
        )

        # Delete student
        cursor.execute(
            """
            DELETE FROM students
            WHERE id = %s
            """,
            (student_id,)
        )

        conn.commit()

        flash(
            "Student deleted successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "Delete student error:",
            e
        )

        flash(
            f"Student could not be deleted: {e}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("student_management")
    )


# =========================================================
# ADMIN APPLICATIONS
# =========================================================

@app.route("/admin-applications")
def admin_applications():

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                applications.id,
                applications.status,
                applications.applied_at,

                students.name AS student_name,
                students.register_no,

                companies.company_name,
                companies.job_role,
                companies.salary

            FROM applications

            INNER JOIN students
                ON applications.student_id = students.id

            INNER JOIN companies
                ON applications.company_id = companies.id

            ORDER BY applications.applied_at DESC
            """
        )

        applications = cursor.fetchall()

        return render_template(
            "admin_applications.html",
            applications=applications
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# UPDATE APPLICATION STATUS
# =========================================================

@app.route(
    "/update-application-status/<int:application_id>",
    methods=["POST"]
)
def update_application_status(application_id):

    if "admin_id" not in session:

        return redirect(
            url_for("admin_login")
        )

    status = request.form.get(
        "status",
        ""
    )

    allowed_statuses = [
        "Applied",
        "Shortlisted",
        "Selected",
        "Rejected"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid application status.",
            "error"
        )

        return redirect(
            url_for("admin_applications")
        )

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE applications

            SET status = %s

            WHERE id = %s
            """,
            (
                status,
                application_id
            )
        )

        conn.commit()

        flash(
            "Application status updated successfully.",
            "success"
        )

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "Status update error:",
            e
        )

        flash(
            f"Could not update status: {e}",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    return redirect(
        url_for("admin_applications")
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin-logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )