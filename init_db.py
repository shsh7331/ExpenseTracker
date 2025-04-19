import sqlite3

# View ER Diagram: https://dbdiagram.io/d/680062581ca52373f54ffd9b

mydb = "db"
def create(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Enable foreign key enforcement
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create users table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id_user INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,              -- hashed passwords
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    )

    # Create categories table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS categories (
        id_category INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE
    );
    """
    )

    # Create expenses table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS expenses (
        id_expense INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        expense_name TEXT NOT NULL,
        expense_amount REAL NOT NULL,
        expense_date DATE NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id_user),
        FOREIGN KEY(category_id) REFERENCES categories(id_category)
    );
    """
    )

    # Create savings_goals table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS savings_goals (
        id_goal INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        goal_name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        amount_saved REAL DEFAULT 0,
        priority INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(user_id) REFERENCES users(id_user)
    );
    """
    )

    # Create budgets table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS budgets (
        id_budget INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id_user),
        FOREIGN KEY(category_id) REFERENCES categories(id_category)
    );
    """
    )

    # Create settings table with constraints and trigger for updated_at
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        theme TEXT NOT NULL DEFAULT 'default-light',
        notifications_enabled INTEGER NOT NULL DEFAULT 1,
        email_alerts INTEGER NOT NULL DEFAULT 1,
        budget_reminder_day INTEGER CHECK (budget_reminder_day BETWEEN 1 AND 31) DEFAULT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        bank_connection TEXT,               -- encrypted data stored as TEXT or BLOB
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """
    )

    # Trigger to auto-update "updated_at" on settings table UPDATE
    cursor.execute(
        """
    CREATE TRIGGER IF NOT EXISTS trg_settings_updated_at
    AFTER UPDATE ON settings
    FOR EACH ROW
    BEGIN
      UPDATE settings
      SET updated_at = CURRENT_TIMESTAMP
      WHERE id = OLD.id;
    END;
    """
    )

    conn.commit()
    conn.close()

def fill_users(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    test_user = [
            (101, 'alice', 'alice@expensetracker.com', 'alice123'),
            (102, 'bob', 'bob@expensetracker.com', 'bob123'),
            (103, 'carol', 'carol@expensetracker.com', 'carol123'),
        ]
    cursor.executemany('''
        INSERT INTO users (id_user, username, email, password)
        VALUES (?, ?, ?, ?)
        ''', test_user)
    conn.commit()
    conn.close()
    return "DB users filled with sample data"

def fill_categories(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    test_categories = [
            (1001, 'Food'),
            (1002, 'Transport'),
            (1003, 'Rent'),
            (1004, 'Entertainment'),
            (1005, 'Utilities'),
            (1006, 'Healthcare'),
            (1007, 'Other'),
        ]
    cursor.executemany('''
        INSERT INTO categories (id_category, category_name)
        VALUES (?, ?)
        ''', test_categories)
    conn.commit()
    conn.close()
    return "DB categories filled with sample data"

def fill_expenses(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    test_expenses = [
            (201, 101, 1001, 'Groceries at Walmart', 85.50, "2025/03/15"),
            (202, 101, 1002, 'Uber to office', 13.25, "2025/03/16"),
            (203, 101, 1003, 'Monthly Rent', 1250.00, "2025/03/1"),
            (204, 102, 1001, 'Dinner with friends', 42.00, "2025/03/10"),
            (205, 102, 1004, 'Netflix Subscription', 15.99, "2025/03/05"),
            (206, 102, 1002, 'Bus Pass', 50.00, "2025/03/06"),
            (207, 103, 1001, 'Doctor Appointment', 120.00, "2025/03/08"),
            (208, 103, 1004, 'Electricity Bill', 60.75, "2025/03/04"),
            (209, 103, 1002, 'Groceries', 72.40, "2025/03/09"),
        ]
    cursor.executemany('''
        INSERT INTO expenses (id_expense, user_id, category_id, expense_name, expense_amount, expense_date)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', test_expenses)
    conn.commit()
    conn.close()
    return "DB expense filled with sample data"


def fill_goals(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    test_goals = [
            (301, 101, 'Emergency Fund', 5000.00, 1200.00, 1,'active'),
            (302, 101, 'Vacation to India', 3000.00, 750.00, 3,'active'),
            (303, 101, 'New Laptop', 1500.00, 550.00, 1,'active'),
            (304, 102, 'Health Fund', 9000.00, 5600.00, 1,'active'),
            (305, 102, 'Home Renovation', 20000.00, 11500.00, 1,'active'),
            (306, 102, 'Vacation to China', 5000.00, 4300.00, 2,'active'),
            (307, 103, 'Wedding Fund', 25000.00, 18000.00, 1,'active'),
            (308, 103, 'Vacation to Hawaii', 8000.00, 3400.00, 1,'active'),
            (309, 103, 'New Furniture', 3500.00, 1150.00, 2,'active'),
        ]
    cursor.executemany('''
        INSERT INTO savings_goals (id_goal, user_id, goal_name, target_amount, amount_saved, priority, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', test_goals)
    conn.commit()
    conn.close()
    return "DB goals filled with sample data"

# def fill_budget(db):
#     conn = sqlite3.connect(db)
#     cursor = conn.cursor()

#     test_budgets = [
#             (301, 101, 'Emergency Fund', 5000.00, 1200.00, 1,'active'),
#             (302, 101, 'Vacation to India', 3000.00, 750.00, 3,'active'),
#             (303, 101, 'New Laptop', 1500.00, 550.00, 1,'active'),
#             (304, 102, 'Health Fund', 9000.00, 5600.00, 1,'active'),
#             (305, 102, 'Home Renovation', 20000.00, 11500.00, 1,'active'),
#             (306, 102, 'Vacation to China', 5000.00, 4300.00, 2,'active'),
#             (307, 103, 'Wedding Fund', 25000.00, 18000.00, 1,'active'),
#             (308, 103, 'Vacation to Hawaii', 8000.00, 3400.00, 1,'active'),
#             (309, 103, 'New Furniture', 3500.00, 1150.00, 2,'active'),
#         ]
#     cursor.executemany('''
#         INSERT INTO budgets (id_budget, user_id, category_id, amount, start_date, end_date)
#         VALUES (?, ?, ?, ?, ?, ?)
#         ''', test_budgets)
#     conn.commit()
#     conn.close()
#     return "DB budgets filled with sample data"


def check_user_credentials(db, username, password):
    """
    Checks if the given username and password match a user in the database.
    Returns True if credentials are valid, otherwise False.
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None


if __name__ == "__main__":
    create(mydb)
    fill_users(mydb)
    fill_categories(mydb)
    fill_expenses(mydb)
    fill_goals(mydb)
