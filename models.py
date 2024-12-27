from config import get_db_connection

def initialize_database():
    """Create necessary tables in the database."""
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            phone_number VARCHAR(15),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Families (
            family_id INT AUTO_INCREMENT PRIMARY KEY,
            family_name VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            primary_user_id INT,
            FOREIGN KEY (primary_user_id) REFERENCES Users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Budgets (
            budget_id INT AUTO_INCREMENT PRIMARY KEY,
            family_id INT,
            category VARCHAR(255) NOT NULL,
            budget_amount FLOAT NOT NULL,
            current_amount FLOAT DEFAULT 0.0,
            threshold_amount FLOAT DEFAULT 0.0,
            is_recurring BOOLEAN DEFAULT FALSE,
            due_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (family_id) REFERENCES Families(family_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS BudgetAlerts (
            alert_id INT AUTO_INCREMENT PRIMARY KEY,
            budget_id INT,
            alert_type VARCHAR(100),
            alert_message TEXT,
            alert_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (budget_id) REFERENCES Budgets(budget_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Expenses (
            expense_id INT AUTO_INCREMENT PRIMARY KEY,
            budget_id INT NOT NULL,
            amount FLOAT NOT NULL,
            date DATE NOT NULL,
            description VARCHAR(255),
            receipt_url VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (budget_id) REFERENCES Budgets(budget_id)
        )
    """)

    connection.commit()
    connection.close()