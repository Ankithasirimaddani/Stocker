from flask import Flask, render_template, request, redirect, url_for, flash, session
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "stocker_secret_2024"


# ================= AWS CONFIG =================

AWS_REGION = "us-east-1"

session_aws = boto3.Session(region_name=AWS_REGION)

dynamodb = session_aws.resource("dynamodb")

sns = session_aws.client("sns")


USER_TABLE = "stocker_users"
STOCK_TABLE = "stocker_stocks"
TRANSACTION_TABLE = "stocker_transactions"
PORTFOLIO_TABLE = "stocker_portfolio"


# ================= DATABASE FUNCTIONS =================


def get_user_by_email(email):

    table = dynamodb.Table(USER_TABLE)

    response = table.get_item(Key={"email": email})

    return response.get("Item")


def get_user_by_id(user_id):

    table = dynamodb.Table(USER_TABLE)

    response = table.scan(
        FilterExpression=Attr("id").eq(user_id)
    )

    users = response.get("Items", [])

    return users[0] if users else None


def create_user(username, email, password, role):

    table = dynamodb.Table(USER_TABLE)

    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }

    table.put_item(Item=user)

    return user


def get_all_stocks():

    table = dynamodb.Table(STOCK_TABLE)

    response = table.scan()

    return response.get("Items", [])


def get_stock_by_id(stock_id):

    table = dynamodb.Table(STOCK_TABLE)

    response = table.get_item(Key={"id": stock_id})

    return response.get("Item")


# ================= PORTFOLIO =================


def get_portfolio(user_id):

    table = dynamodb.Table(PORTFOLIO_TABLE)

    response = table.scan(
        FilterExpression=Attr("user_id").eq(user_id)
    )

    portfolio = response.get("Items", [])

    for p in portfolio:

        p["stock"] = get_stock_by_id(p["stock_id"])

    return portfolio


def get_portfolio_item(user_id, stock_id):

    table = dynamodb.Table(PORTFOLIO_TABLE)

    response = table.get_item(
        Key={
            "user_id": user_id,
            "stock_id": stock_id
        }
    )

    return response.get("Item")


def update_portfolio(user_id, stock_id, quantity, avg_price):

    table = dynamodb.Table(PORTFOLIO_TABLE)

    if quantity <= 0:

        table.delete_item(
            Key={"user_id": user_id, "stock_id": stock_id}
        )

    else:

        table.put_item(
            Item={
                "user_id": user_id,
                "stock_id": stock_id,
                "quantity": quantity,
                "average_price": Decimal(str(avg_price))
            }
        )


# ================= TRANSACTIONS =================


def create_transaction(user_id, stock_id, action, quantity, price):

    table = dynamodb.Table(TRANSACTION_TABLE)

    transaction = {

        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "stock_id": stock_id,
        "action": action,
        "quantity": quantity,
        "price": Decimal(str(price)),
        "status": "completed",
        "transaction_date": datetime.now().isoformat()

    }

    table.put_item(Item=transaction)


# ================= ROUTES =================


@app.route("/")
def index():
    return render_template("index.html")


# ================= LOGIN =================


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        user = get_user_by_email(email)

        if user and user["password"] == password and user["role"] == role:

            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            if role == "admin":
                return redirect(url_for("dashboard_admin"))

            return redirect(url_for("dashboard_trader"))

        flash("Invalid credentials")

    return render_template("login.html")


# ================= SIGNUP =================


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        if get_user_by_email(email):

            flash("User already exists")

            return redirect(url_for("login"))

        create_user(username, email, password, role)

        flash("Account created successfully")

        return redirect(url_for("login"))

    return render_template("signup.html")


# ================= DASHBOARDS =================


@app.route("/dashboard_admin")
def dashboard_admin():

    user = get_user_by_email(session["email"])

    return render_template("dashboard_admin.html", user=user)


@app.route("/dashboard_trader")
def dashboard_trader():

    stocks = get_all_stocks()

    user = get_user_by_email(session["email"])

    return render_template(
        "dashboard_trader.html",
        user=user,
        market_data=stocks
    )


# ================= LOGOUT =================


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# ================= ADMIN SERVICES =================


@app.route("/service01")
def service01():

    table = dynamodb.Table(USER_TABLE)

    traders = table.scan(
        FilterExpression=Attr("role").eq("trader")
    ).get("Items", [])

    for trader in traders:
        trader["total_portfolio_value"] = 0

    return render_template("service-details-1.html", traders=traders)


@app.route("/delete_trader/<trader_id>", methods=["POST"])
def delete_trader(trader_id):

    table = dynamodb.Table(USER_TABLE)

    table.delete_item(Key={"id": trader_id})

    flash("Trader deleted")

    return redirect(url_for("service01"))


@app.route("/service02")
def service02():

    table = dynamodb.Table(TRANSACTION_TABLE)

    transactions = table.scan().get("Items", [])

    for t in transactions:

        t["user"] = get_user_by_id(t["user_id"])
        t["stock"] = get_stock_by_id(t["stock_id"])

    return render_template(
        "service-details-2.html",
        transactions=transactions
    )


@app.route("/service03")
def service03():

    table = dynamodb.Table(PORTFOLIO_TABLE)

    portfolios = table.scan().get("Items", [])

    total_portfolio_value = 0

    for p in portfolios:

        p["user"] = get_user_by_id(p["user_id"])
        p["stock"] = get_stock_by_id(p["stock_id"])

        total_portfolio_value += p["quantity"] * p["stock"]["price"]

    return render_template(
        "service-details-3.html",
        portfolios=portfolios,
        total_portfolio_value=total_portfolio_value
    )


# ================= STOCK BROWSING =================


@app.route("/service04")
def service04():

    stocks = get_all_stocks()

    user = get_user_by_email(session["email"])

    return render_template(
        "service-details-4.html",
        stocks=stocks,
        user=user
    )


# ================= USER PORTFOLIO =================


@app.route("/service05")
def service05():

    user_id = session["user_id"]

    portfolio = get_portfolio(user_id)

    table = dynamodb.Table(TRANSACTION_TABLE)

    transactions = table.scan(
        FilterExpression=Attr("user_id").eq(user_id)
    ).get("Items", [])

    for t in transactions:
        t["stock"] = get_stock_by_id(t["stock_id"])

    total_value = sum(
        item["quantity"] * item["stock"]["price"]
        for item in portfolio
    )

    return render_template(
        "service-details-5.html",
        portfolio=portfolio,
        transactions=transactions,
        total_value=total_value
    )


# ================= BUY STOCK =================


@app.route("/buy_stock/<stock_id>", methods=["GET", "POST"])
def buy_stock(stock_id):

    stock = get_stock_by_id(stock_id)

    if not stock:
        flash("Stock not found")
        return redirect(url_for("dashboard_trader"))

    if request.method == "POST":

        quantity = int(request.form["quantity"])

        user_id = session["user_id"]

        price = stock["price"]

        create_transaction(user_id, stock_id, "buy", quantity, price)

        portfolio_item = get_portfolio_item(user_id, stock_id)

        if portfolio_item:

            new_qty = portfolio_item["quantity"] + quantity

        else:

            new_qty = quantity

        update_portfolio(user_id, stock_id, new_qty, price)

        flash("Stock purchased successfully")

        return redirect(url_for("service05"))

    return render_template("buy_stock.html", stock=stock)


# ================= SELL STOCK =================


@app.route("/sell_stock/<stock_id>", methods=["GET", "POST"])
def sell_stock(stock_id):

    user_id = session["user_id"]

    stock = get_stock_by_id(stock_id)

    portfolio_item = get_portfolio_item(user_id, stock_id)

    if not portfolio_item:

        flash("You do not own this stock")

        return redirect(url_for("service05"))

    if request.method == "POST":

        quantity = int(request.form["quantity"])

        price = stock["price"]

        create_transaction(user_id, stock_id, "sell", quantity, price)

        new_qty = portfolio_item["quantity"] - quantity

        update_portfolio(
            user_id,
            stock_id,
            new_qty,
            portfolio_item["average_price"]
        )

        flash("Stock sold successfully")

        return redirect(url_for("service05"))

    return render_template(
        "sell_stock.html",
        stock=stock,
        portfolio_entry=portfolio_item
    )


# ================= RUN =================


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)