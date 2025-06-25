import yfinance as yf
import pandas as pd
class StockTradingBot:
    def __init__(self, symbol, short_window, long_window, initial_cash):
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.cash = initial_cash
        self.stock_balance = 0
        self.history = []


    def get_stock_data(self, start_date, end_date):
        data = yf.download(self.symbol, start=start_date, end=end_date)
        return data


    def calculate_sma(self, data, window):
        return data['Close'].rolling(window=window).mean()


    def buy(self, price, amount):
        total_cost = price * amount
        if self.cash >= total_cost:
            self.cash -= total_cost
            self.stock_balance += amount
            self.history.append(f"Bought {amount} shares at ${price:.2f} each") 


    def sell(self, price, amount):
        if self.stock_balance >= amount:
            total_sale = price * amount
            self.cash += total_sale
            self.stock_balance -= amount
            self.history.append(f"Sold {amount} shares at ${price:.2f} each")


    def execute_strategy(self, data):
        short_sma = self.calculate_sma(data, self.short_window)
        long_sma = self.calculate_sma(data, self.long_window)
        for i in range(self.long_window, len(data)):
            short_val = short_sma.iloc[i].item()
            long_val = long_sma.iloc[i].item()
            close_price = data['Close'].iloc[i].item()
            #print(f"Date: {data.index[i]}, Short SMA: {short_val}, Long SMA: {long_val}")
            if pd.notna(short_val) and pd.notna(long_val):
                if short_val > long_val:
                    self.buy(close_price, 10)
                elif short_val < long_val:
                    self.sell(close_price, 10)


    def run(self):
        self.data = self.get_stock_data("2023-06-01", "2025-06-01")
        if self.data.empty:
            print("Error: No data downloaded. Please check symbol or date range.")
            return
        self.execute_strategy(self.data)
        self.display_portfolio()



    def display_portfolio(self):
        print("Portfolio Summary:")
        print(f"Cash: ${self.cash:.2f}")
        print(f"Stock Balance: {self.stock_balance} shares")
        if not self.data.empty:
            latest_price = float(self.data['Close'].iloc[-1].item())
            print(f"Portfolio Value: ${(self.cash + self.stock_balance * latest_price):.2f}")
        else:
            print("Portfolio Value: Cannot compute (no data)")


#data = yf.download("AAPL", start="2024-01-01", end="2025-01-01")
#print(data)
if __name__ == "__main__":
    bot = StockTradingBot(symbol="MA", short_window=50, long_window=200, initial_cash=10000)
bot.run()