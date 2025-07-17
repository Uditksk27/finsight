import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.schema import Transaction, Category, Budget, User
import pandas as pd
import datetime
from collections import defaultdict
# from datetime import datetime
import hashlib
from database.schema import User

st.set_page_config(page_title="Finsight 💸", layout="centered")

#DB setup
engine = create_engine('sqlite:///database/finsight.db')
Session = sessionmaker(bind=engine)
session = Session()


# Simple password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Check if user is logged in
if "user_id" not in st.session_state:


    st.markdown("## 🔐 Login or Sign Up")

    auth_mode = st.radio("Select Mode", ["Login", "Sign Up"])

    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Submit"):
        if auth_mode == "Sign Up":
            # Check if username already exists
            if session.query(User).filter_by(username=username_input).first():
                st.error("Username already taken.")
            else:
                new_user = User(
                    username=username_input,
                    password=hash_password(password_input)
                )
                session.add(new_user)
                session.commit()
                st.success("✅ Account created! You can now log in.")
        else:
            # Login mode
            user = session.query(User).filter_by(
                username=username_input,
                password=hash_password(password_input)
            ).first()
            if user:
                st.session_state.user_id = user.id
                st.success(f"Welcome, {user.username}!")
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    st.stop()


def show_dashboard():
    st.title("📊 Insights Dashboard")

    # Put all your dashboard logic here
    # (like selected_month, transactions_dash, bar chart, pie chart, line trend etc.)
    st.markdown("### 💰 Monthly Summary")
    # Get current month and year
    import datetime
    today = datetime.date.today()
    months = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    col1, col2 = st.columns(2)

    with col1:
        selected_month = st.selectbox("Select Month", list(months.values()), index=today.month - 1)

    with col2:
        selected_year = st.selectbox("Select Year", list(range(2022, today.year + 1)),
                                     index=list(range(2022, today.year + 1)).index(today.year))

    # Convert selection to actual month number
    selected_month_number = list(months.keys())[list(months.values()).index(selected_month)]

    # Start and end date range for that month
    start_date_dash = datetime.datetime(selected_year, selected_month_number, 1)
    if selected_month_number == 12:
        end_date_dash = datetime.datetime(selected_year + 1, 1, 1) - datetime.timedelta(seconds=1)
    else:
        end_date_dash = datetime.datetime(selected_year, selected_month_number + 1, 1) - datetime.timedelta(seconds=1)

    # Fetching all transactions for the selected month and plots to create a bar chart
    import plotly.graph_objects as go

    # Query transactions for the selected month
    transactions_dash = session.query(Transaction).filter(
        Transaction.timestamp >= start_date_dash,
        Transaction.timestamp <= end_date_dash,
        Transaction.user_id == st.session_state.user_id
    ).all()

    income_total = sum(t.amount for t in transactions_dash if t.type == "income")
    expense_total = sum(t.amount for t in transactions_dash if t.type == "expense")

    # Plotting with Plotly
    fig_bar = go.Figure(data=[
        go.Bar(name='Income', x=['Income'], y=[income_total], marker_color='green'),
        go.Bar(name='Expense', x=['Expense'], y=[expense_total], marker_color='red')
    ])

    fig_bar.update_layout(
        title_text=f"💰 Income vs Expense — {selected_month} {selected_year}",
        barmode='group',
        yaxis_title='Amount (₹)',
        xaxis_title=''
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # Category Pie Chart
    st.markdown("### 🧾 Category-wise Breakdown")

    # Group expenses by category
    category_expenses = defaultdict(float)
    for t in transactions_dash:
        if t.type == "expense":
            category_expenses[t.category.name] += t.amount

    if category_expenses:
        fig_pie = go.Figure(data=[
            go.Pie(
                labels=list(category_expenses.keys()),
                values=list(category_expenses.values()),
                hole=0.4  # donut style
            )
        ])

        fig_pie.update_layout(
            title_text=f"🧾 Category-wise Expenses — {selected_month} {selected_year}",
        )

        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expenses to show for selected month.")

    # setting up warnings for budget overspending
    st.markdown("## 🚨 Budget Alerts")

    # Reuse: start_date_dash and end_date_dash already defined from Step 1
    # Step 1: Get category-wise spend for selected month
    category_spends = defaultdict(float)

    for t in transactions_dash:
        if t.type == "expense":
            category_spends[t.category.name] += t.amount

    # Step 2: Fetch budgets from DB for selected month


    budgets = session.query(Budget).filter_by(
        month=selected_month_number,
        year=selected_year,
        user_id=st.session_state.user_id
    ).all()

    budgets_by_category = {b.category.name: b.amount for b in budgets}

    # Step 3: Compare spend vs budget
    for cat, spent in category_spends.items():
        budget = budgets_by_category.get(cat)
        if budget:
            if spent == budget:
                st.warning(f"⚠️ Bro no more spending in this category! Spent ₹{spent:.0f} / Budget ₹{budget:.0f}")
            if spent > budget:
                st.error(f"❌ Over budget in **{cat}**: Spent ₹{spent:.0f} / Budget ₹{budget:.0f}")
            elif spent >= 0.8 * budget:
                st.warning(f"⚠️ Approaching limit in **{cat}**: Spent ₹{spent:.0f} / Budget ₹{budget:.0f}")
            else:
                st.info(f"✅ On track in **{cat}**: Spent ₹{spent:.0f} / Budget ₹{budget:.0f}")
        else:
            st.info(f"ℹ️ No budget set for **{cat}**")

    # Sort transactions by date
    transactions_sorted = sorted(transactions_dash, key=lambda x: x.timestamp)

    # Daily Balance Trend
    st.markdown("### 📈 Daily Balance Over Time")

    # Prepare data for trend
    dates = []
    balances = []
    current_balance = 0

    for t in transactions_sorted:
        if t.type == "income":
            current_balance += t.amount
        elif t.type == "expense":
            current_balance -= t.amount
        dates.append(t.timestamp.date())
        balances.append(current_balance)

    if balances:
        fig_line = go.Figure()

        fig_line.add_trace(go.Scatter(
            x=dates,
            y=balances,
            mode='lines+markers',
            name='Balance',
            line=dict(color='royalblue', width=3),
            marker=dict(size=6)
        ))

        fig_line.update_layout(
            title=f"📈 Daily Balance Trend — {selected_month} {selected_year}",
            xaxis_title="Date",
            yaxis_title="Balance (₹)",
            showlegend=False
        )

        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No transactions to show balance trend.")


def load_transactions(type_filter=None, category_filter=None, start_date=None, end_date=None):
    query = session.query(Transaction)
    query = query.filter(Transaction.user_id == st.session_state.user_id)

    if type_filter:
        query = query.filter(Transaction.type == type_filter)

    if category_filter:
        query = query.join(Transaction.category).filter(Category.name == category_filter)

    # Only apply date filter if both dates are provided and start <= end
    if start_date and end_date and start_date <= end_date:
        from datetime import datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Transaction.timestamp.between(start_datetime, end_datetime))

    transactions = query.all()

    data = []
    for t in transactions:
        data.append({
            "Amount": t.amount,
            "Category": t.category.name,
            "Type": t.type,
            "Date": t.timestamp.strftime("%Y/%m/%d"),
            "Notes": t.notes
        })
    return pd.DataFrame(data)


def show_transactions():
    st.title("📋 All Transactions")

    st.sidebar.header("🔍 Filter Transactions")

    # Type filter
    type_filter = st.sidebar.selectbox("Transaction Type", ["All", "income", "expense"])
    type_filter = None if type_filter == "All" else type_filter

    # Category filter (from DB)
    category_names = [c.name for c in session.query(Category).all()]
    category_filter = st.sidebar.selectbox("Category", ["All"] + category_names)
    category_filter = None if category_filter == "All" else category_filter

    # Date filter
    today = datetime.date.today()
    start_date = st.sidebar.date_input("Start Date", value=today - datetime.timedelta(days=30))
    end_date = st.sidebar.date_input("End Date", value=today)

    # Add New Transaction Form
    st.header("➕ Add New Transaction")

    with st.form(key="transaction_form"):
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        type_ = st.selectbox("Type", ["income", "expense"])
        category_names = [c.name for c in session.query(Category).all()]
        category_name = st.selectbox("Category", category_names)
        date = st.date_input("Date")
        notes = st.text_input("Notes (optional)")

        submit_button = st.form_submit_button(label="Add Transaction")

        if submit_button:
            category = session.query(Category).filter_by(name=category_name).first()
            new_txn = Transaction(
                amount=amount,
                type=type_,
                category=category,
                timestamp=datetime.datetime.combine(date, datetime.datetime.min.time()),
                notes=notes,
                user_id=st.session_state.user_id
            )

            session.add(new_txn)
            session.commit()
            st.success("✅ Transaction added successfully!")

    # Load filtered transactions
    df = load_transactions(type_filter, category_filter, start_date, end_date)
    st.write("DEBUG: Transactions fetched →", len(df))
    # st.dataframe(df)  # temporary, to check data

    # Show Table
    edited_index = st.session_state.get("edited_index", None)

    for index, row in df.iterrows():
        col1, col2, col3 = st.columns([5, 1, 1])

        if edited_index == index:
            with st.form(f"edit_form_{index}"):
                new_amount = st.number_input("Amount", value=row["Amount"])
                new_type = st.selectbox("Type", ["income", "expense"], index=0 if row["Type"] == "income" else 1)
                new_category = st.selectbox("Category", category_names, index=category_names.index(row["Category"]))
                new_date = st.date_input("Date", value=datetime.datetime.strptime(row["Date"], "%Y/%m/%d").date())
                new_notes = st.text_input("Notes", value=row["Notes"])
                submitted = st.form_submit_button("Save Changes")

                if submitted:
                    # Convert date back
                    original_date = datetime.datetime.strptime(row["Date"], "%Y/%m/%d").date()

                    # Fetch and update
                    txn_to_update = session.query(Transaction).join(Transaction.category).filter(
                        Transaction.amount == row["Amount"],
                        Transaction.type == row["Type"],
                        Transaction.notes == row["Notes"],
                        Category.name == row["Category"],
                        Transaction.timestamp >= datetime.datetime.combine(original_date, datetime.datetime.min.time()),
                        Transaction.timestamp <= datetime.datetime.combine(original_date, datetime.datetime.max.time())
                    ).first()

                    if txn_to_update:
                        txn_to_update.amount = new_amount
                        txn_to_update.type = new_type
                        txn_to_update.category = session.query(Category).filter(Category.name == new_category).first()
                        txn_to_update.timestamp = datetime.datetime.combine(new_date, datetime.datetime.min.time())
                        txn_to_update.notes = new_notes

                        session.commit()
                        st.success("Transaction updated successfully!")
                        st.session_state.edited_index = None
                    else:
                        st.error("Could not find the transaction.")

        else:
            with col1:
                st.write(
                    f"💸 ₹{row['Amount']} | {row['Category']} | {row['Type']} | {row['Date']} | {row['Notes']}"
                )
            with col2:
                if st.button("✏️ Edit", key=f"edit_{index}"):
                    st.session_state.edited_index = index
                    st.rerun()
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{index}"):
                    row_date = datetime.datetime.strptime(row["Date"], "%Y/%m/%d").date()
                    to_delete = session.query(Transaction).join(Transaction.category).filter(
                        Transaction.amount == row["Amount"],
                        Transaction.type == row["Type"],
                        Transaction.notes == row["Notes"],
                        Category.name == row["Category"],
                        Transaction.timestamp >= datetime.datetime.combine(row_date, datetime.datetime.min.time()),
                        Transaction.timestamp <= datetime.datetime.combine(row_date, datetime.datetime.max.time())
                    ).first()

                    if to_delete:
                        session.delete(to_delete)
                        session.commit()
                        st.success("Transaction deleted! Refresh to see changes.")
                    else:
                        st.error("Could not find this transaction.")


def show_budgets():
    st.title("💸 Set Monthly Budgets")

    # Fetch category list from DB (don't use global list)
    category_names = [c.name for c in session.query(Category).all()]

    with st.form(key="budget_form"):
        today = datetime.date.today()
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            budget_category = st.selectbox("Select Category", category_names)
            budget_month = st.selectbox(
                "Month",
                list(range(1, 13)),
                index=today.month - 1,
                format_func=lambda x: datetime.date(1900, x, 1).strftime('%B')
            )
        with b_col2:
            budget_year = st.selectbox(
                "Year",
                list(range(2022, today.year + 1)),
                index=list(range(2022, today.year + 1)).index(today.year)
            )
            budget_amount = st.number_input("Budget Amount (₹)", min_value=0.0, step=100.0)

        submit_budget = st.form_submit_button(label="💾 Save Budget")

        if submit_budget:
            # Import Budget model only if not already imported at top


            cat = session.query(Category).filter_by(name=budget_category).first()

            existing = session.query(Budget).filter_by(
                category_id=cat.id,
                month=budget_month,
                year=budget_year,
                user_id=st.session_state.user_id
            ).first()

            if existing:
                existing.amount = budget_amount
                st.success("✅ Budget updated successfully!")
            else:
                new_budget = Budget(
                    category_id=cat.id,
                    month=budget_month,
                    year=budget_year,
                    amount=budget_amount,
                    user_id=st.session_state.user_id
                )
                session.add(new_budget)
                st.success("✅ Budget set successfully!")

            session.commit()

    st.markdown("### 📅 View Budgets For:")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        view_month = st.selectbox(
            "Select Month",
            list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda x: datetime.date(1900, x, 1).strftime('%B'),
            key="view_month"
        )

    with filter_col2:
        view_year = st.selectbox(
            "Select Year",
            list(range(2022, today.year + 1)),
            index=list(range(2022, today.year + 1)).index(today.year),
            key="view_year"
        )

    # Show current budgets for the selected year and month
    budgets = session.query(Budget).filter_by(
        month=view_month,
        year=view_year,
        user_id=st.session_state.user_id
    ).all()

    if budgets:
        st.markdown("### 📑 Your Budgets")


        cols_per_row = 3
        for i in range(0, len(budgets), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, b in enumerate(budgets[i:i + cols_per_row]):
                with cols[j]:
                    st.markdown(
                        f"""
                        <div style="
                            background-color:#1e1e1e;
                            padding: 1em;
                            margin-bottom: 0.7em;
                            border-radius: 0.7em;
                            border: 1px solid #444;
                            color: white;
                        ">
                            <b style="font-size: 1.1rem;">{b.category.name}</b><br>
                            <span style="color: #aaa;">🗓 {datetime.date(year=1900, month=b.month, day=1).strftime('%B')} {b.year}</span><br>
                            <span style="font-size: 1.2rem;">💰 ₹{b.amount:.0f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    else:
        st.info("No budgets set yet.")


# Only show UI if user is logged in
if "user_id" in st.session_state:
    user_obj = session.query(User).get(st.session_state.user_id)
    st.sidebar.markdown(f"👤 Logged in as: **{user_obj.username}**")

    if st.sidebar.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Navigation
    st.sidebar.markdown("## 🔧 Navigation")
    selected_page = st.sidebar.radio(
        "Go to",
        ["📊 Dashboard", "📋 Transactions", "💸 Budgets"]
    )

    # Render selected page
    if selected_page == "📊 Dashboard":
        show_dashboard()
    elif selected_page == "📋 Transactions":
        show_transactions()
    elif selected_page == "💸 Budgets":
        show_budgets()

    session.close()




session.close()