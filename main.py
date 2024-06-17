import json
import os
import random
import yfinance as yf
import datetime as dt
import plotly.graph_objs as go
import plotly.express as px
from tabulate import tabulate
import bcrypt
import warnings

warnings.filterwarnings("ignore")



def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    price = stock.history(period="1d")["Close"].iloc[-1]
    return price


def get_historical_data(ticker, period="1mo"):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    hist['20d_ma'] = hist['Close'].rolling(window=20).mean()
    hist['50d_ma'] = hist['Close'].rolling(window=50).mean()
    return hist


def create_account(accounts):
    email = input("Enter your email: ")
    if email in accounts:
        print("An account with this email already exists.")
        return None

    password = input("Enter your password: ")
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_id = str(random.randint(1000, 9999))
    while user_id in accounts:
        user_id = str(random.randint(1000, 9999))

    accounts[email] = {
        "user_id": user_id,
        "password": hashed_password.decode('utf-8'),
        "balance": 10000.0,
        "portfolio": {},
        "history": []
    }
    save_accounts(accounts)
    return email


def load_accounts():
    if os.path.exists("accounts.txt"):
        with open("accounts.txt", "r") as file:
            return json.load(file)
    else:
        return {}


def save_accounts(accounts):
    with open("accounts.txt", "w") as file:
        json.dump(accounts, file)


def buy_stock(accounts, email, ticker, amount):
    try:
        price = get_stock_price(ticker)
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return False

    cost = price * amount
    if accounts[email]["balance"] >= cost:
        accounts[email]["balance"] -= cost
        if ticker in accounts[email]["portfolio"]:
            accounts[email]["portfolio"][ticker] += amount
        else:
            accounts[email]["portfolio"][ticker] = amount
        accounts[email].setdefault("history", []).append(
            {"type": "buy", "ticker": ticker, "amount": amount, "price": price, "date": str(dt.datetime.now())})
        save_accounts(accounts)
        return True
    else:
        return False


def sell_stock(accounts, email, ticker, amount):
    if ticker in accounts[email]["portfolio"] and accounts[email]["portfolio"][ticker] >= amount:
        try:
            price = get_stock_price(ticker)
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return False

        revenue = price * amount
        accounts[email]["portfolio"][ticker] -= amount
        if accounts[email]["portfolio"][ticker] == 0:
            del accounts[email]["portfolio"][ticker]
        accounts[email]["balance"] += revenue
        accounts[email].setdefault("history", []).append(
            {"type": "sell", "ticker": ticker, "amount": amount, "price": price, "date": str(dt.datetime.now())})
        save_accounts(accounts)
        return True
    else:
        return False


def view_portfolio(accounts, email):
    portfolio = accounts[email]["portfolio"]
    balance = accounts[email]["balance"]
    portfolio_data = []
    total_invested = 0
    total_value = 0
    for ticker, amount in portfolio.items():
        try:
            price = get_stock_price(ticker)
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            continue

        value = price * amount
        total_value += value
        for transaction in accounts[email]["history"]:
            if transaction["ticker"] == ticker:
                if transaction["type"] == "buy":
                    total_invested += transaction["amount"] * transaction["price"]
        portfolio_data.append([ticker, amount, f"${price:.2f}", f"${value:.2f}"])

    roi = (total_value - total_invested) / total_invested * 100 if total_invested != 0 else 0
    balance_str = f"${balance:.2f}"
    headers = ["Ticker", "Amount", "Current Price", "Total Value"]

    print("Portfolio:")
    print(tabulate(portfolio_data, headers=headers, tablefmt="pretty"))
    print(f"\nBalance: {balance_str}")
    print(f"Total Invested: ${total_invested:.2f}")
    print(f"Total Value: ${total_value:.2f}")
    print(f"Return on Investment (ROI): {roi:.2f}%")


def view_stock_prices():
    tickers = ["GOOGL", "AAPL", "AMZN", "BCOV", "LMT"]
    stock_data = []
    for ticker in tickers:
        try:
            price = get_stock_price(ticker)
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            continue

        stock_data.append([ticker, f"${price:.2f}"])

    headers = ["Ticker", "Current Price"]

    print("Stock Prices:")
    print(tabulate(stock_data, headers=headers, tablefmt="pretty"))


def view_historical_data(ticker):
    while True:
        try:
            hist = get_historical_data(ticker)
            if hist.empty:
                print(f"No historical data found for {ticker}.")
                return
        except Exception as e:
            print(f"Error fetching historical data for {ticker}: {e}")
            return

        hist_data = hist[['Close', '20d_ma', '50d_ma']].tail(30).reset_index()
        hist_data['Date'] = hist_data['Date'].dt.strftime('%Y-%m-%d')
        hist_data = hist_data.round(3)
        print(f"\nHistorical Data and Moving Averages for {ticker}:")
        print(tabulate(hist_data, headers="keys", tablefmt="pretty"))


        fig = px.line(hist_data, x='Date', y=['Close', '20d_ma', '50d_ma'],
                      labels={'value': 'Price', 'variable': 'Indicator'},
                      title=f'Historical Price and Moving Averages for {ticker}')
        fig.update_traces(mode='lines+markers')
        fig.show()

        choice = input("Press 'b' to go back to the main menu: ")
        if choice.lower() == 'b':
            return


def login(accounts):
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    if email in accounts and bcrypt.checkpw(password.encode('utf-8'), accounts[email]['password'].encode('utf-8')):
        return email
    else:
        print("Invalid email or password.")
        return None


def main():
    accounts = load_accounts()
    email = None

    while True:
        if not email:
            print("1. Create a new account")
            print("2. Login to existing account")
            choice = input("Choose an option: ")
            if choice == "1":
                email = create_account(accounts)
                if email:
                    print(f"Account created. Logged in as {email}.")
            elif choice == "2":
                email = login(accounts)
                if email:
                    print(f"Logged in as {email}.")
            else:
                print("Invalid choice.")
        else:
            print("\n1. View portfolio")
            print("2. Buy stocks")
            print("3. Sell stocks")
            print("4. View stock prices")
            print("5. View historical data")
            print("6. Logout")
            choice = input("Choose an option: ")
            if choice == "1":
                view_portfolio(accounts, email)
            elif choice == "2":
                ticker = input("Enter stock ticker: ")
                amount = int(input("Enter amount to buy: "))
                if buy_stock(accounts, email, ticker, amount):
                    print(f"Bought {amount} shares of {ticker}.")
                else:
                    print("Insufficient funds or invalid ticker.")
            elif choice == "3":
                ticker = input("Enter stock ticker: ")
                amount = int(input("Enter amount to sell: "))
                if sell_stock(accounts, email, ticker, amount):
                    print(f"Sold {amount} shares of {ticker}.")
                else:
                    print("Insufficient shares or invalid ticker.")
            elif choice == "4":
                view_stock_prices()
            elif choice == "5":
                ticker = input("Enter stock ticker: ")
                view_historical_data(ticker)
            elif choice == "6":
                email = None
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    main()

