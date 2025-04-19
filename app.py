from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from datetime import datetime
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "replace_with_a_strong_random_key"

DB_PATH = "db"   # ← make sure this points at the file your creation script produced

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.context_processor
def inject_globals():
    return {
        "logged_in": "user" in session,
        "current_year": datetime.now().year
    }

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        identifier = request.form["username"]   # username or email
        password   = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            """
            SELECT * FROM users
            WHERE username = ?
               OR email = ?
            """,
            (identifier, identifier)
        ).fetchone()
        conn.close()

        # ← change this:
        # if user and check_password_hash(user["password"], password):
        if user and user["password"] == password:
            session["user"] = dict(id=user["id_user"], name=user["username"])
            return redirect(url_for("home"))
        else:
            error = "Invalid username/email or password."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ← Newly added routes ↓

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":
        user_id       = session["user"]["id"]
        name          = request.form["expense_name"]
        date          = request.form["expense_date"]
        category_id   = request.form["category"]
        amount        = request.form["expense_amount"]

        conn.execute(
            """
            INSERT INTO expenses
              (user_id, category_id, expense_name, expense_amount, expense_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, category_id, name, amount, date)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("expense_list"))

    # GET: fetch categories for the dropdown
    categories = conn.execute(
        "SELECT id_category, category_name FROM categories ORDER BY category_name"
    ).fetchall()
    conn.close()
    return render_template("add_expense.html", categories=categories)

@app.route("/expense_list")
def expense_list():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
          e.expense_date,
          e.expense_name,
          c.category_name,
          e.expense_amount
        FROM expenses e
        JOIN categories c
          ON e.category_id = c.id_category
        WHERE e.user_id = ?
        ORDER BY e.expense_date DESC
        """,
        (session["user"]["id"],)
    ).fetchall()
    conn.close()

    # Convert sqlite3.Row objects into plain dicts so Jinja's tojson works smoothly
    expenses = [
        {
            "expense_date":  r["expense_date"],
            "expense_name":  r["expense_name"],
            "category_name": r["category_name"],
            "expense_amount": r["expense_amount"],
        }
        for r in rows
    ]

    return render_template("expense_list.html", expenses=expenses)
@app.route("/savings")
def savings():
    return render_template("savings.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/api/expenses", methods=["GET", "POST"])
def api_expenses():
    if "user" not in session:
        return abort(401)

    conn = get_db_connection()
    user_id = session["user"]["id"]

    if request.method == "GET":
        rows = conn.execute(
            """
            SELECT
              e.id_expense,
              e.expense_name,
              e.expense_amount,
              e.expense_date,
              c.category_name
            FROM expenses e
            JOIN categories c
              ON e.category_id = c.id_category
            WHERE e.user_id = ?
            ORDER BY e.expense_date DESC
            """,
            (user_id,)
        ).fetchall()
        conn.close()

        # convert to list of dicts
        expenses = [
            {
                "id":     r["id_expense"],
                "name":   r["expense_name"],
                "amount": r["expense_amount"],
                "date":   r["expense_date"],
                "category": r["category_name"]
            }
            for r in rows
        ]
        return jsonify(expenses)

    # POST: accept JSON { name, amount, date, category_id }
    data = request.get_json()
    required = ("expense_name", "expense_amount", "expense_date", "category_id")
    if not data or any(field not in data for field in required):
        return abort(400, "Missing one of expense_name, expense_amount, expense_date, category_id")

    cursor = conn.execute(
        """
        INSERT INTO expenses
          (user_id, category_id, expense_name, expense_amount, expense_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data["category_id"],
            data["expense_name"],
            data["expense_amount"],
            data["expense_date"]
        )
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"status": "success", "id": new_id}), 201

# ↑ End of new routes

if __name__ == "__main__":
    app.run(debug=True)