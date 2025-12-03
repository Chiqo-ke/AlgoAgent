"""
Generated Trading Strategy - RSI Strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime

class RSIStrategy:
    """Simple RSI-based trading strategy"""
    
    def __init__(self, period=14):
        self.period = period
        self.prices = []
    
    def calculate_rsi(self, prices):
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        seed = deltas[:self.period+1]
        up = seed[seed >= 0].sum() / self.period
        down = -seed[seed < 0].sum() / self.period
        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:self.period] = 100. - 100. / (1. + rs)
        
        for i in range(self.period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (self.period - 1) + upval) / self.period
            down = (down * (self.period - 1) + downval) / self.period
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi
    
    def signal(self, price):
        """Generate trading signal"""
        self.prices.append(price)
        
        if len(self.prices) < self.period:
            return 0
        
        rsi = self.calculate_rsi(np.array(self.prices))[-1]
        
        if rsi < 30:
            return 1  # Buy signal
        elif rsi > 70:
            return -1  # Sell signal
        else:
            return 0  # Hold

if __name__ == "__main__":
    print("Strategy loaded successfully")
