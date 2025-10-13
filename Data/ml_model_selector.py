# AlgoAgent/Data/ml_model_selector.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import numpy as np
import joblib

class MLModelSelector:
    def __init__(self, model_path="ml_model.joblib"):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Loads a pre-trained model if it exists."""
        try:
            self.model = joblib.load(self.model_path)
            print(f"ML model loaded from {self.model_path}")
        except FileNotFoundError:
            print("No pre-trained ML model found. A new one will be trained if `train_model` is called.")
        except Exception as e:
            print(f"Error loading ML model: {e}")

    def train_model(self, data: pd.DataFrame, target_column: str, feature_columns: list):
        """
        Trains a machine learning model to select optimal indicators.

        Args:
            data (pd.DataFrame): DataFrame containing features (indicators) and a target.
            target_column (str): The name of the target column (e.g., 'Future_Direction').
            feature_columns (list): A list of column names to be used as features.
        """
        if data.empty or target_column not in data.columns or not feature_columns:
            print("Insufficient data or columns to train the model.")
            return

        X = data[feature_columns]
        y = data[target_column]

        # Handle NaN values by filling with mean or median, or dropping rows
        X = X.fillna(X.mean())
        # Drop rows where target is NaN
        combined = pd.concat([X, y], axis=1).dropna()
        X = combined[feature_columns]
        y = combined[target_column]

        if X.empty or y.empty:
            print("No valid data after handling NaNs for model training.")
            return

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model trained with accuracy: {accuracy:.4f}")

        # Save the trained model
        joblib.dump(self.model, self.model_path)
        print(f"ML model saved to {self.model_path}")

    def predict_optimal_indicators(self, current_data: pd.DataFrame, feature_columns: list) -> dict:
        """
        Predicts optimal indicators or parameters based on the trained model.
        This is a placeholder for a more sophisticated selection mechanism.

        Args:
            current_data (pd.DataFrame): The latest financial data with calculated indicators.
            feature_columns (list): The feature columns used during training.

        Returns:
            dict: A dictionary suggesting optimal indicators and their parameters.
        """
        if self.model is None:
            print("No ML model available. Please train the model first.")
            return {}

        if current_data.empty or not feature_columns:
            print("Insufficient data or feature columns for prediction.")
            return {}

        # Ensure current_data has the same feature columns as used in training
        X_predict = current_data[feature_columns].tail(1) # Predict based on the latest data point
        X_predict = X_predict.fillna(X_predict.mean()) # Fill NaNs for prediction

        if X_predict.empty:
            print("No valid data for prediction after handling NaNs.")
            return {}

        prediction = self.model.predict(X_predict)
        probabilities = self.model.predict_proba(X_predict)

        # This is a simplified example. In a real scenario, you'd use the model's
        # output to infer which indicators are performing best or which parameters
        # to adjust. For now, we'll return a dummy suggestion.
        print(f"Model prediction: {prediction[0]}")
        print(f"Prediction probabilities: {probabilities[0]}")

        # Example of dynamic indicator suggestion based on a simple rule or model output
        if prediction[0] == 1: # Assuming 1 means "bullish" or "strong trend"
            return {'suggested_indicators': [{'name': 'RSI', 'timeperiod': 14}, {'name': 'ADX', 'timeperiod': 14}]}
        else: # Assuming 0 means "bearish" or "ranging"
            return {'suggested_indicators': [{'name': 'SMA', 'timeperiod': 20}, {'name': 'BBANDS', 'timeperiod': 20}]}

if __name__ == "__main__":
    # Create dummy data for demonstration
    np.random.seed(42)
    data_size = 200
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=data_size, freq='D'))
    close_prices = np.random.randn(data_size).cumsum() + 100
    df = pd.DataFrame({'Close': close_prices}, index=dates)

    # Add some dummy indicators
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['RSI_14'] = np.random.rand(data_size) * 100 # Dummy RSI
    df['MACD'] = np.random.rand(data_size) # Dummy MACD

    # Create a dummy target variable: 1 if price increased next day, 0 otherwise
    df['Future_Direction'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df = df.dropna()

    feature_cols = ['SMA_20', 'RSI_14', 'MACD']
    target_col = 'Future_Direction'

    selector = MLModelSelector()

    # Train the model
    selector.train_model(df, target_col, feature_cols)

    # Simulate new data for prediction
    new_data = pd.DataFrame({
        'Close': [105],
        'SMA_20': [103],
        'RSI_14': [60],
        'MACD': [0.5]
    }, index=[pd.to_datetime('2023-07-19')])

    # Predict optimal indicators
    optimal_indicators = selector.predict_optimal_indicators(new_data, feature_cols)
    print("\nSuggested optimal indicators:", optimal_indicators)