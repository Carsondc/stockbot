import yfinance as yf
import pandas as pd

class SmarterTradingBot:
    def __init__(self, symbols, short_window, long_window, initial_cash, position_fraction=0.1, stop_loss=0.9):
        self.symbols = symbols
        self.short_window = short_window
        self.long_window = long_window
        self.cash = initial_cash
        self.position_fraction = position_fraction  # fraction of cash to invest per buy
        self.stop_loss = stop_loss                  # e.g., 0.9 = sell if price drops 10%
        self.stock_balances = {symbol: 0 for symbol in symbols}
        self.avg_price = {symbol: 0 for symbol in symbols}
        self.data = {}
        self.history = []

    def get_stock_data(self, start_date, end_date):
        for symbol in self.symbols:
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if df.empty:
                print(f"Warning: No data for {symbol}")
            else:
                df['EMA_short'] = df['Close'].ewm(span=self.short_window, adjust=False).mean()
                df['EMA_long'] = df['Close'].ewm(span=self.long_window, adjust=False).mean()
                df['RSI'] = self.calculate_rsi(df)
                self.data[symbol] = df

    def calculate_rsi(self, data, window=14):
        delta = data['Close'].diff()
        gain = delta.clip(lower=0).rolling(window).mean()
        loss = -delta.clip(upper=0).rolling(window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def buy(self, symbol, price):
        amount_to_invest = self.cash * self.position_fraction
        shares = int(amount_to_invest // price)
        if shares > 0 and float(self.cash) >= shares * price:
            self.cash -= shares * price
            total_cost = self.avg_price[symbol] * self.stock_balances[symbol] + shares * price
            self.stock_balances[symbol] += shares
            self.avg_price[symbol] = total_cost / self.stock_balances[symbol]
            #self.history.append(f"BUY {shares} {symbol} @ ${price:.2f}")

    def sell(self, symbol, price, shares=None):
        if shares is None:
            shares = self.stock_balances[symbol]  # sell all
        if self.stock_balances[symbol] >= shares:
            self.cash += shares * price
            self.stock_balances[symbol] -= shares
            if self.stock_balances[symbol] == 0:
                self.avg_price[symbol] = 0
            #self.history.append(f"SELL {shares} {symbol} @ ${price:.2f}")

    def execute_strategy(self):
        for symbol, df in self.data.items():
            for i in range(self.long_window, len(df)):
                short_val = float(df['EMA_short'].iloc[i])
                long_val = float(df['EMA_long'].iloc[i])
                rsi = float(df['RSI'].iloc[i])
                price = float(df['Close'].iloc[i])

                if pd.notna(short_val) and pd.notna(long_val) and pd.notna(rsi):
                    # Buy rule: short EMA > long EMA AND RSI < 70
                    if short_val > long_val and rsi < 70:
                        self.buy(symbol, price)

                    # Sell rule: short EMA < long EMA OR RSI > 80 OR stop-loss triggered
                    elif (short_val < long_val) or (rsi > 80) or (
                        self.stock_balances[symbol] > 0 and price < self.avg_price[symbol] * self.stop_loss
                    ):
                        self.sell(symbol, price)

    def display_portfolio(self):
        print("\n=== Portfolio Summary ===")
        print(f"Cash: ${self.cash:.2f}")
        total_value = self.cash

        for symbol in self.symbols:
            shares = self.stock_balances[symbol]
            if symbol in self.data and not self.data[symbol].empty:
                latest_price = float(self.data[symbol]['Close'].iloc[-1])
                value = shares * latest_price
                total_value += value
                print(f"{symbol}: {shares} shares @ ${latest_price:.2f} = ${value:.2f}")
            else:
                print(f"{symbol}: No data")

        print(f"Total Portfolio Value: ${total_value:.2f}")

        print("\n=== Trade History ===")
        for entry in self.history:
            print(entry)

        return total_value

    def run(self, start_date="2023-06-01", end_date="2025-06-01"):
        self.get_stock_data(start_date, end_date)
        if not self.data:
            print("Error: No valid stock data retrieved.")
            return
        self.execute_strategy()
        portfolio_value = self.display_portfolio()

        # Benchmark vs SPY
        spy = yf.download("SPY", start=start_date, end=end_date, progress=False)
        spy_return = spy['Close'].iloc[-1] / spy['Close'].iloc[0] - 1
        bot_return = portfolio_value / 100000 - 1
        print(f"\nSPY Benchmark Return: {f'spy_return:.2%'}")
        print(f"Bot Return: {bot_return:.2%}")


if __name__ == "__main__":
    bot = SmarterTradingBot(
        symbols=["AMZN", "WMT", "UNH", "AAPL", "CVS", "GOOGL", "XOM", "MCK", "CNO"],
        short_window=20,
        long_window=50,
        initial_cash=100000,
        position_fraction=0.1,
        stop_loss=0.9
    )
    bot.run()
