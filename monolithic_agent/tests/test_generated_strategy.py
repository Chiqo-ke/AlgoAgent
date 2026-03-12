import yfinance as yf
from backtesting import Strategy, Backtest
import talib as ta

class MeanReversionStrategy(Strategy):
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    
    def init(self):
        close = self.data.Close
        self.rsi = self.I(ta.RSI, close, self.rsi_period)
    
    def next(self):
        if self.rsi < self.rsi_oversold:
            if not self.position:
                self.buy()
        elif self.rsi > self.rsi_overbought:
            if self.position:
                self.position.close()

if __name__ == "__main__":
    # Download historical data
    data = yf.download('AAPL', period='1y', interval='1d', progress=False)
    
    # Run backtest
    bt = Backtest(data, MeanReversionStrategy, cash=10000, commission=0.002)
    stats = bt.run()
    
    # Print metrics in parseable format
    print(f"Return [Avg]: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats.get('Sharpe Ratio', 0):.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats.get('Win Rate [%]', 0):.2f}%")
    print(f"Total Trades: {stats['# Trades']}")
