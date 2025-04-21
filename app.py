from flask import Flask, render_template, redirect, session, request, url_for
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime


app = Flask(__name__)
app.secret_key = "dev-secret-key"

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

def get_conn():
    return psycopg2.connect(
        "postgresql://deepfinance_expense_tracker_database_user:NyIrVfklZmymWd79xMHbsfcjeEWbVZP2@dpg-d01g1hadbo4c738nslq0-a.oregon-postgres.render.com/deepfinance_expense_tracker_database",
        cursor_factory=RealDictCursor)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/create_account")
def create():
    return render_template("create_account.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, password from users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

        if user and password == user["password"]:
            session["user_id"] = user["id"]
            return redirect("/")
        else:
            return "Invalid username or password", 403

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    user_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        date = request.form.get("date")
        category_id = request.form.get("category_id")
        expense_name = request.form.get("expense_name")
        amount = request.form.get("amount")

        if date and category_id and expense_name and amount:
            try:
                amount_float = float(amount)

                # Insert using DB column names, including the expense_name from form
                cur.execute(
                    """INSERT INTO expenses (user_id, expense_date, category_id, expense_amount, expense_name)
                       VALUES (%s, %s, %s, %s, %s);""",
                    (user_id, date, category_id, amount_float, expense_name)
                )
                conn.commit()
                cur.close()
                conn.close()
                return redirect("/expense_list")
            except (ValueError, psycopg2.Error) as e:
                 conn.rollback() 
                 # Fall through to render form again
                 # TODO: Add user feedback/logging if desired

        # Fetch categories using DB column name for display if POST fails
        cur.execute("SELECT id, category_name FROM categories WHERE user_id = %s ORDER BY category_name;", (user_id,))
        categories = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("add_expense.html", categories=categories)

    # GET Request: Fetch categories using DB column name for display
    cur.execute("SELECT id, category_name FROM categories WHERE user_id = %s ORDER BY category_name;", (user_id,))
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("add_expense.html", categories=categories)


@app.route("/expense_list", methods=["GET", "POST"])
@login_required
def expense_list():
    user_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "add_category":
                category_name = request.form.get("category_name")
                if category_name:
                    # Insert using DB column name
                    cur.execute(
                        """INSERT INTO categories (user_id, category_name) VALUES (%s, %s);""",
                        (user_id, category_name)
                    )
            elif action == "set_budget":
                category_id = request.form.get("category_id")
                budget = request.form.get("budget")
                if category_id and budget is not None:
                    budget_float = float(budget)
                    # Update using DB column name
                    cur.execute(
                        """UPDATE categories SET budget = %s WHERE id = %s AND user_id = %s;""",
                        (budget_float, category_id, user_id)
                    )
            # TODO: Handle deleting categories
            conn.commit()
        except (ValueError, psycopg2.Error) as e:
            conn.rollback()
            # TODO: Add user feedback/logging if desired
        
        cur.close()
        conn.close()
        return redirect("/expense_list")

    # GET Request: Fetch categories
    cur.execute(
        """
        SELECT id, category_name, budget 
        FROM categories 
        WHERE user_id = %s 
        ORDER BY category_name;
        """, 
        (user_id,)
    )
    categories = cur.fetchall()

    # Calculate recent spending (current month) for each category
    today = datetime.date.today()
    start_of_month = today.replace(day=1)
    categories_with_spending = []
    for category in categories:
        cur.execute(
            """
            SELECT COALESCE(SUM(expense_amount), 0) as monthly_total
            FROM expenses
            WHERE user_id = %s 
              AND category_id = %s 
              AND expense_date >= %s;
            """,
            (user_id, category['id'], start_of_month)
        )
        spending_result = cur.fetchone()
        category['recent_spending'] = spending_result['monthly_total']
        categories_with_spending.append(category)

    # Fetch recent transactions (e.g., last 5)
    cur.execute(
        """
        SELECT 
            e.expense_date, 
            e.expense_name, 
            e.expense_amount,
            c.category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        ORDER BY e.expense_date DESC
        LIMIT 5;
        """,
        (user_id,)
    )
    recent_expenses = cur.fetchall()

    cur.close()
    conn.close()

    # Pass enhanced data to template
    return render_template(
        "expense_list.html", 
        categories=categories_with_spending,
        expenses=recent_expenses
    )


@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    user_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        # Create a new goal
        if request.form.get("goal_name"):
            goal_name = request.form["goal_name"]
            target_amount = float(request.form["target_amount"])
            # Insert new goal in db
            cur.execute(
                """
                INSERT INTO
                    savings_goals (user_id, goal_name, target_amount)
                VALUES
                    (%s,%s,%s);
                """,
                (user_id, goal_name, target_amount)
            )
        
        # Add a savings entry
        elif request.form.get("entry_amount"):
            goal_id = int(request.form["entry_goal_id"])
            amount = float(request.form["entry_amount"])
            # Insert savings entry into database
            cur.execute(
                """
                INSERT INTO
                    savings_entries (goal_id, amount)
                VALUES (%s,%s);
                """, 
                (goal_id, amount)
            )
            # Update goal total
            cur.execute(
                """
                UPDATE
                    savings_goals
                SET
                    amount_saved = amount_saved + %s WHERE id = %s;
                """,
                (amount, goal_id)
            )
        conn.commit()

    # Fetch all goals
    cur.execute(
        """
        SELECT
            id, goal_name, target_amount, amount_saved
        FROM
            savings_goals
        WHERE
            user_id = %s
        ORDER BY
            id;
        """,
        (user_id,))
    goals = cur.fetchall()

    # Fetch all savings entries having a goal name
    cur.execute(
        """
        SELECT
            savings_entries.amount,
            savings_entries.date_added,
            savings_goals.goal_name
        FROM
            savings_entries
        JOIN savings_goals ON
            savings_entries.goal_id = savings_goals.id
        WHERE
            savings_goals.user_id = %s
        ORDER BY
            savings_entries.date_added DESC;
        """,
        (user_id,)
    )
    entries = cur.fetchall()


    cur.close()
    conn.close()

    return render_template("savings.html",
                           goals=goals,
                           entries=entries)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        currency = request.form.get("currency")
        dark_mode = request.form.get("dark_mode") == 'on'
        notifications = request.form.get("notifications") == 'on'
        bank_account = request.form.get("bank_account")
        
        user_id = session['user_id']
        conn = get_conn()
        cur = conn.cursor()

        theme = 'dark' if dark_mode else 'default-light' 
        
        try:
            cur.execute("""
                INSERT INTO settings (user_id, theme, notifications_enabled, bank_connection)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    theme = EXCLUDED.theme,
                    notifications_enabled = EXCLUDED.notifications_enabled,
                    bank_connection = EXCLUDED.bank_connection;
            """, (user_id, theme, notifications, bank_account))
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Error saving settings: {e}")
            
        cur.close()
        conn.close()
        return redirect(url_for('settings'))

    user_id = session['user_id']
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT theme, notifications_enabled, bank_connection FROM settings WHERE user_id = %s", (user_id,))
    user_settings = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user_settings:
        user_settings = {'theme': 'default-light', 'notifications_enabled': True, 'bank_connection': ''}

    return render_template("settings.html", user_settings=user_settings)


if __name__ == "__main__":
    app.run(debug=True)
