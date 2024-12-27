from flask import Blueprint, render_template, request, redirect, flash
from datetime import datetime
from models import Budget, Expense, BudgetAlert, db

budgeting_bp = Blueprint('budgeting', __name__)

@budgeting_bp.route('/')
def home():
    budgets = Budget.query.all()
    return render_template('home.html', budgets=budgets)

@budgeting_bp.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        category = request.form['category']
        budget_amount = float(request.form['budget_amount'])
        threshold_amount = float(request.form['threshold_amount'])
        due_date = request.form['due_date']
        
        # Save to database
        new_budget = Budget(category=category, budget_amount=budget_amount, 
                            threshold_amount=threshold_amount, due_date=due_date)
        db.session.add(new_budget)
        db.session.commit()
        
        flash('Budget added successfully!', 'success')
        return redirect('/budgeting')
    return render_template('add_budget.html')

@budgeting_bp.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if request.method == 'POST':
        budget_id = int(request.form['budget_id'])
        amount = float(request.form['amount'])
        description = request.form['description']
        date = request.form['date']
        
        if date:
            date = datetime.strptime(date, '%Y-%m-%d')
        else:
            date = datetime.now()
        
        # Fetch the budget
        budget = Budget.query.get(budget_id)

        # Add the expense to the Expenses table
        new_expense = Expense(budget_id=budget_id, amount=amount, description=description, date=date)
        db.session.add(new_expense)
        db.session.commit()

        # Subtract the expense from the current amount
        budget.current_amount += amount
        db.session.commit()

        # Check if the expense exceeds the threshold
        if budget.current_amount > budget.threshold_amount:
            alert_message = f"Alert: Your expenses for the {budget.category} category have exceeded the threshold of ${budget.threshold_amount}."
            new_alert = BudgetAlert(budget_id=budget_id, alert_type="Threshold Exceeded", alert_message=alert_message)
            db.session.add(new_alert)
            db.session.commit()

        flash('Expense added successfully!', 'success')
        return redirect('/budgeting')

    budgets = Budget.query.all()  # Get all budgets for the dropdown
    return render_template('expenses.html', budgets=budgets)

@budgeting_bp.route('/report')
def report():
    budgets = Budget.query.all()
    expenses = Expense.query.all()

    # Create a dictionary to store total expenses for each budget
    budget_expenses = {}
    
    for expense in expenses:
        if expense.budget_id not in budget_expenses:
            budget_expenses[expense.budget_id] = 0
        budget_expenses[expense.budget_id] += expense.amount

    budget_details = []
    for budget in budgets:
        total_expenses = budget_expenses.get(budget.budget_id, 0)
        remaining_budget = budget.budget_amount - total_expenses
        budget_details.append({
            'category': budget.category,
            'budget_amount': budget.budget_amount,
            'current_amount': budget.current_amount,
            'total_expenses': total_expenses,
            'remaining_budget': remaining_budget,
            'due_date': budget.due_date
        })

    return render_template('report.html', budget_details=budget_details)

@budgeting_bp.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
def edit_budget(budget_id):
    budget = Budget.query.get(budget_id)
    if request.method == 'POST':
        budget.category = request.form['category']
        budget.budget_amount = float(request.form['budget_amount'])
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect('/budgeting')
    return render_template('edit_budget.html', budget=budget)