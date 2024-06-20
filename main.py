import json
import os
import random
import yfinance as yf
import datetime as dt
import plotly.graph_objects as go
from tabulate import tabulate
import warnings
import re
import pandas as pd

warnings.filterwarnings("ignore")

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print(f"{bcolors.FAIL}Invalid email address.{bcolors.ENDC}")
        return None
    if email in accounts:
        print(f"{bcolors.FAIL}An account with this email already exists.{bcolors.ENDC}")
        return None
    password = input("Enter your password (at least 6 characters): ")
    if not password or len(password) < 6:
        print(f"{bcolors.FAIL}Password must be at least 6 characters long.{bcolors.ENDC}")
        return None
    user_id = str(random.randint(1000, 9999))
    while user_id in accounts:
        user_id = str(random.randint(1000, 9999))
    accounts[email] = {
        "user_id": user_id,
        "password": password,
        "balance": 10000.0,
        "portfolio": {},
        "history": []
    }
    save_accounts(accounts)
    return email

def load_accounts():
    accounts = {}
    if os.path.exists("accounts.txt"):
        with open("accounts.txt", "r") as file:
            lines = file.readlines()
            headers = lines[0].strip().split('\t')
            for line in lines[1:]:
                data = line.strip().split('\t')
                email = data[0]
                accounts[email] = {
                    "user_id": data[1],
                    "password": data[2],
                    "balance": float(data[3]),
                    "portfolio": json.loads(data[4]),
                    "history": json.loads(data[5])
                }
    return accounts

def save_accounts(accounts):
    headers = ["email", "user_id", "password", "balance", "portfolio", "history"]
    with open("accounts.txt", "w") as file:
        file.write('\t'.join(headers) + '\n')
        for email, info in accounts.items():
            line = [
                email,
                info["user_id"],
                info["password"],
                f'{info["balance"]:.2f}',
                json.dumps(info["portfolio"]),
                json.dumps(info["history"])
            ]
            file.write('\t'.join(line) + '\n')

def buy_stock(accounts, email, ticker, amount):
    try:
        price = get_stock_price(ticker)
    except Exception as e:
        print(f"{bcolors.FAIL}Error fetching price for {ticker}: {e}{bcolors.ENDC}")
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
            print(f"{bcolors.FAIL}Error fetching price for {ticker}: {e}{bcolors.ENDC}")
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
            print(f"{bcolors.FAIL}Error fetching price for {ticker}: {e}{bcolors.ENDC}")
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
    print(f"{bcolors.OKBLUE}Portfolio:{bcolors.ENDC}")
    print(tabulate(portfolio_data, headers=headers, tablefmt="pretty"))
    print(f"\n{bcolors.OKGREEN}Balance: {balance_str}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}Total Invested: ${total_invested:.2f}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}Total Value: ${total_value:.2f}{bcolors.ENDC}")
    print(f"{bcolors.OKCYAN}Return on Investment (ROI): {roi:.2f}%{bcolors.ENDC}")

def view_stock_prices():
    tickers = ["GOOGL", "AAPL", "AMZN", "BCOV", "LMT"]
    stock_data = []
    for ticker in tickers:
        try:
            price = get_stock_price(ticker)
        except Exception as e:
            print(f"{bcolors.FAIL}Error fetching price for {ticker}: {e}{bcolors.ENDC}")
            continue
        stock_data.append([ticker, f"${price:.2f}"])
    headers = ["Ticker", "Current Price"]
    print(f"{bcolors.OKBLUE}Stock Prices:{bcolors.ENDC}")
    print(tabulate(stock_data, headers=headers, tablefmt="pretty"))

def display_stock_chart(ticker):
    end_date = pd.Timestamp.today()
    start_date = end_date - pd.DateOffset(months=6)
    print(f"{bcolors.OKBLUE}Getting data...{bcolors.ENDC}")
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        print(f"{bcolors.FAIL}No data found for ticker {ticker}.{bcolors.ENDC}")
        return
    data['10_day_MA'] = data['Close'].rolling(window=10).mean()
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'])])
    fig.add_trace(go.Scatter(x=data.index, y=data['10_day_MA'], 
                             mode='lines', 
                             name='10 Day MA',
                             line=dict(color='blue')))
    fig.update_layout(
        title=f'{ticker} Candlestick Chart (Last 6 Months)',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False
    )
    print(f"{bcolors.OKBLUE}Displaying candlestick chart{bcolors.ENDC}")
    fig.show()

def view_leaderboard(accounts):
    leaderboard = []
    for email, info in accounts.items():
        portfolio_value = info['balance']
        for ticker, amount in info['portfolio'].items():
            try:
                price = get_stock_price(ticker)
            except Exception as e:
                print(f"{bcolors.FAIL}Error fetching price for {ticker}: {e}{bcolors.ENDC}")
                continue
            portfolio_value += price * amount
        leaderboard.append((email, portfolio_value))
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    leaderboard_data = [[email, f"${value:.2f}"] for email, value in leaderboard]
    headers = ["Email", "Total Portfolio Value"]
    print(f"{bcolors.OKBLUE}Leaderboard:{bcolors.ENDC}")
    print(tabulate(leaderboard_data, headers=headers, tablefmt="pretty"))

def main():
    accounts = load_accounts()
    email = None
    print(f"{bcolors.HEADER}Welcome to the Stock Trading Game!{bcolors.ENDC}")
    while True:
        if email is None:
            print(f"\n{bcolors.HEADER}Main Menu:{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}1. Create an account{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}2. Login{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}3. View leaderboard{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}4. Exit{bcolors.ENDC}")
            choice = input("Choose an option: ")
            match choice:
                case "1":
                    email = create_account(accounts)
                case "2":
                    email = input("Enter your email: ")
                    if email in accounts:
                        password = input("Enter your password: ")
                        if accounts[email]["password"] == password:
                            print(f"{bcolors.OKGREEN}Login successful.{bcolors.ENDC}")
                        else:
                            print(f"{bcolors.FAIL}Incorrect password.{bcolors.ENDC}")
                            email = None
                    else:
                        print(f"{bcolors.FAIL}No account found with this email.{bcolors.ENDC}")
                        email = None
                case "3":
                    view_leaderboard(accounts)
                case "4":
                    print(f"{bcolors.OKCYAN}Exiting the game. Goodbye!{bcolors.ENDC}")
                    break
                case _:
                    print(f"{bcolors.FAIL}Invalid choice.{bcolors.ENDC}")
        else:
            print(f"\n{bcolors.HEADER}Main Menu:{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}1. View portfolio{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}2. Buy stocks{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}3. Sell stocks{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}4. View stock prices{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}5. Display stock chart{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}6. Logout{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}7. Exit{bcolors.ENDC}")
            choice = input("Choose an option: ")
            match choice:
                case "1":
                    view_portfolio(accounts, email)
                case "2":
                    ticker = input("Enter stock ticker: ")
                    amount = int(input("Enter amount to buy: "))
                    if buy_stock(accounts, email, ticker, amount):
                        print(f"{bcolors.OKGREEN}Bought {amount} shares of {ticker}.{bcolors.ENDC}")
                    else:
                        print(f"{bcolors.FAIL}Insufficient funds or invalid ticker.{bcolors.ENDC}")
                case "3":
                    ticker = input("Enter stock ticker: ")
                    amount = int(input("Enter amount to sell: "))
                    if sell_stock(accounts, email, ticker, amount):
                        print(f"{bcolors.OKGREEN}Sold {amount} shares of {ticker}.{bcolors.ENDC}")
                    else:
                        print(f"{bcolors.FAIL}Insufficient shares or invalid ticker.{bcolors.ENDC}")
                case "4":
                    view_stock_prices()
                case "5":
                    ticker = input("Enter stock ticker: ")
                    display_stock_chart(ticker)
                case "6":
                    email = None
                case "7":
                    print(f"{bcolors.OKCYAN}Exiting the game. Goodbye!{bcolors.ENDC}")
                    break
                case _:
                    print(f"{bcolors.FAIL}Invalid choice.{bcolors.ENDC}")

if __name__ == "__main__":
    main()
