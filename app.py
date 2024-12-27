from flask import Flask, render_template, request, redirect, flash
from config import app, get_db_connection
from models import initialize_database
from datetime import datetime

# Initialize the database
initialize_database()

@app.route('/')
def home():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Budgets")
    budgets = cursor.fetchall()
    connection.close()
    return render_template('home.html', budgets=budgets)

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

        # Update budget current amount
        cursor.execute("SELECT * FROM Budgets WHERE budget_id = %s", (budget_id,))
        budget = cursor.fetchone()
        new_amount = budget['current_amount'] + amount
        cursor.execute("UPDATE Budgets SET current_amount = %s WHERE budget_id = %s", (new_amount, budget_id))

        # Insert alert if threshold is exceeded
        if new_amount > budget['threshold_amount']:
            alert_message = f"Alert: Your expenses for the {budget['category']} category have exceeded the threshold of ${budget['threshold_amount']}"
            cursor.execute(
                "INSERT INTO BudgetAlerts (budget_id, alert_type, alert_message, alert_date) VALUES (%s, %s, %s, %s)",
                (budget_id, "Threshold Exceeded", alert_message, datetime.now())
            )

        # Insert the expense
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

    # Process data for report
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

if __name__ == '__main__':
    app.run(debug=True)
