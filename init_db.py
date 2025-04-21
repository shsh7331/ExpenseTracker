import psycopg2

# View ER Diagram: https://dbdiagram.io/d/680062581ca52373f54ffd9b


def init_db():

    # Connect to PostgreSQL db on Render
    conn = psycopg2.connect(
        "postgresql://deepfinance_expense_tracker_database_user:NyIrVfklZmymWd79xMHbsfcjeEWbVZP2@dpg-d01g1hadbo4c738nslq0-a.oregon-postgres.render.com/deepfinance_expense_tracker_database"
    )
    cur = conn.cursor()
    # 0) create an account
    cur.execute(
        """
        CREATE TABLE users (
        id INT PRIMARY KEY IDENTITY(1,1),
        Email NVARCHAR(255) NOT NULL UNIQUE,
        PassHash NVARCHAR(255) NOT NULL
        
        CREATE PROCEDURE Register
        @Email NVARCHAR(255),
        @Pass NVARCHAR(255)
        AS
        BEGIN
            DECLARE @PassHash NVARCHAR(255),
            SET @PassHash = HASHBYTES('SHA2_256', @Pass);

            INSERT INTO Users (Email, PassHash)
            VALUES (@Email, @PassHash)
        END;
        );
        """
    )
        
    # 1) users table
    cur.execute(
        """
        CREATE TABLE
            IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # 2) categories table
    cur.execute(
        """
        CREATE TABLE
            IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                category_name TEXT NOT NULL,
                budget NUMERIC(12, 2) DEFAULT 0,
                UNIQUE (user_id, category_name)
            );
        """
    )

    # Add budget column to categories if it doesn't exist (for backwards compatibility)
    try:
        cur.execute(
            """ALTER TABLE categories ADD COLUMN IF NOT EXISTS budget NUMERIC(12, 2) DEFAULT 0;"""
        )
        conn.commit() # Commit this change immediately
    except psycopg2.Error as e:
        print(f"Error adding budget column (may already exist or other issue): {e}")
        conn.rollback() # Rollback if alter fails

    # Add user_id column to categories if it doesn't exist (for backwards compatibility)
    try:
        cur.execute(
            """ALTER TABLE categories ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;"""
        )
        conn.commit() # Commit this change immediately
    except psycopg2.Error as e:
        print(f"Error adding user_id column (may already exist or other issue): {e}")
        conn.rollback() # Rollback if alter fails

    # 3) expenses table
    cur.execute(
        """
        CREATE TABLE
            IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                category_id INTEGER NOT NULL REFERENCES categories (id) ON DELETE RESTRICT,
                expense_name TEXT NOT NULL,
                expense_amount NUMERIC(12,2) NOT NULL,
                expense_date DATE NOT NULL
            );
        """
    )

    # 4) savings_goals table
    cur.execute(
        """
        CREATE TABLE
            IF NOT EXISTS savings_goals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                goal_name TEXT NOT NULL,
                target_amount NUMERIC(12,2) NOT NULL,
                amount_saved NUMERIC(12,2) NOT NULL DEFAULT 0
            );
        """
    )

    # 5) savings_entries
    cur.execute(
        """
        CREATE TABLE
            IF NOT EXISTS savings_entries (
                id SERIAL PRIMARY KEY,
                goal_id INTEGER NOT NULL REFERENCES savings_goals (id) ON DELETE CASCADE,
                amount NUMERIC(12,2) NOT NULL,
                date_added TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """
    )

    # 6) settings table
    cur.execute(
        """
        CREATE TABLE
            IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
                theme TEXT NOT NULL DEFAULT 'default-light',
                notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                email_alerts BOOLEAN NOT NULL DEFAULT TRUE,
                budget_reminder_day INTEGER CHECK (budget_reminder_day BETWEEN 1 AND 31),
                bank_connection TEXT
            );
        """
    )

    # 7) trigger function for updated_at
    cur.execute(
        """
        CREATE OR REPLACE FUNCTION settings_updated_at_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at := CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # 8) trigger binding
    cur.execute(
        """
        DROP TRIGGER IF EXISTS trigger_settings_updated_at ON settings;

        CREATE TRIGGER trigger_settings_updated_at BEFORE
        UPDATE ON settings FOR EACH ROW EXECUTE PROCEDURE settings_updated_at_trigger ();
        """
    )

    # Commit and close
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized!")
