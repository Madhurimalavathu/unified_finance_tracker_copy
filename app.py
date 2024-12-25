from flask import Flask, render_template, request, redirect, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Database Configuration
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Krishna1919@"
DB_NAME = "db1"

app.secret_key = "your_secret_key"  # For session and flash messages

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def initialize_database():
    # Connect to MySQL server (no database yet)
    connection = get_db_connection()
    cursor = connection.cursor()

    # Create the database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    connection.close()

    # Connect to the new database
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
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

# Call database initialization
initialize_database()

@app.route('/')
def home():
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Budgets")
    budgets = cursor.fetchall()
    connection.close()
    return render_template('home.html', budgets=budgets)

# Other routes remain unchanged...
@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        category = request.form['category']
        budget_amount = float(request.form['budget_amount'])
        due_date = request.form['due_date']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Budgets (category, budget_amount, due_date, current_amount, threshold_amount) VALUES (%s, %s, %s, %s, %s)",
            (category, budget_amount, due_date, 0.0, 0.0)
        )
        connection.commit()
        connection.close()

        flash('Budget added successfully!', 'success')
        return redirect('/')
    return render_template('add_budget.html')

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if request.method == 'POST':
        budget_id = int(request.form['budget_id'])
        amount = float(request.form['amount'])
        description = request.form['description']
        date = request.form['date'] or datetime.now().strftime('%Y-%m-%d')

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Update the current amount in the budget
        cursor.execute("SELECT * FROM Budgets WHERE budget_id = %s", (budget_id,))
        budget = cursor.fetchone()
        new_amount = budget['current_amount'] + amount
        cursor.execute("UPDATE Budgets SET current_amount = %s WHERE budget_id = %s", (new_amount, budget_id))

        # Check for threshold alert
        if new_amount > budget['threshold_amount']:
            alert_message = f"Alert: Your expenses for the {budget['category']} category have exceeded the threshold of ${budget['threshold_amount']}"
            cursor.execute(
                "INSERT INTO BudgetAlerts (budget_id, alert_type, alert_message, alert_date) VALUES (%s, %s, %s, %s)",
                (budget_id, "Threshold Exceeded", alert_message, datetime.now())
            )

        # Add the expense
        cursor.execute(
            "INSERT INTO Expenses (budget_id, amount, description, date) VALUES (%s, %s, %s, %s)",
            (budget_id, amount, description, date)
        )

        connection.commit()
        connection.close()

        flash('Expense added successfully!', 'success')
        return redirect('/')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Budgets")
    budgets = cursor.fetchall()
    connection.close()
    return render_template('expenses.html', budgets=budgets)

@app.route('/report')
def report():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Budgets")
    budgets = cursor.fetchall()

    cursor.execute("SELECT * FROM Expenses")
    expenses = cursor.fetchall()

    connection.close()

    # Calculate budget details
    budget_expenses = {}
    for expense in expenses:
        if expense['budget_id'] not in budget_expenses:
            budget_expenses[expense['budget_id']] = 0
        budget_expenses[expense['budget_id']] += expense['amount']

    budget_details = []
    for budget in budgets:
        total_expenses = budget_expenses.get(budget['budget_id'], 0)
        remaining_budget = budget['budget_amount'] - total_expenses
        budget_details.append({
            'category': budget['category'],
            'budget_amount': budget['budget_amount'],
            'current_amount': budget['current_amount'],
            'total_expenses': total_expenses,
            'remaining_budget': remaining_budget,
            'due_date': budget['due_date']
        })

    return render_template('report.html', budget_details=budget_details)

@app.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
def edit_budget(budget_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        category = request.form['category']
        budget_amount = float(request.form['budget_amount'])
        cursor.execute(
            "UPDATE Budgets SET category = %s, budget_amount = %s WHERE budget_id = %s",
            (category, budget_amount, budget_id)
        )
        connection.commit()
        connection.close()
        flash('Budget updated successfully!', 'success')
        return redirect('/')

    cursor.execute("SELECT * FROM Budgets WHERE budget_id = %s", (budget_id,))
    budget = cursor.fetchone()
    connection.close()
    return render_template('edit_budget.html', budget=budget)

if __name__ == 'main':
    app.run(debug=True)