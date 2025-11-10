import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import joblib

class MLModelSelector:
    def __init__(self, model_path="ml_model.joblib"):
        self.model = None
        self.feature_columns = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Loads a pre-trained model and its feature columns."""
        try:
            saved_state = joblib.load(self.model_path)
            self.model = saved_state['model']
            self.feature_columns = saved_state['feature_columns']
            print(f"ML model loaded from {self.model_path}")
        except FileNotFoundError:
            print("No pre-trained ML model found. A new one will be trained if `train_model` is called.")
        except Exception as e:
            print(f"Error loading ML model: {e}")

    def train_model(self, df: pd.DataFrame, target_column: str, feature_columns: list):
        """
        Trains a RandomForestClassifier and saves it.

        Args:
            df (pd.DataFrame): DataFrame containing features and a target.
            target_column (str): The name of the target column.
            feature_columns (list): A list of column names to be used as features.
        """
        if df.empty or target_column not in df.columns or not feature_columns:
            print("Insufficient data or columns to train the model.")
            return

        X = df[feature_columns]
        y = df[target_column]

        # Simple NaN handling
        X = X.fillna(X.mean())
        combined = pd.concat([X, y], axis=1).dropna()
        X = combined[feature_columns]
        y = combined[target_column]

        if X.empty or y.empty:
            print("No valid data after handling NaNs for model training.")
            return

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        self.feature_columns = feature_columns

        # Save the trained model and feature columns
        saved_state = {'model': self.model, 'feature_columns': self.feature_columns}
        joblib.dump(saved_state, self.model_path)
        print(f"ML model trained and saved to {self.model_path}")

    def suggest_indicators(self, k: int = 5) -> list:
        """
        Suggests the top k indicators based on feature importance.

        Args:
            k (int): The number of top indicators to suggest.

        Returns:
            list: A list of the top k indicator names.
        """
        if self.model is None or self.feature_columns is None:
            print("No ML model available. Please train the model first.")
            return []

        importances = self.model.feature_importances_
        feature_importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importances
        }).sort_values(by='importance', ascending=False)

        print("\nFeature Importances:")
        print(feature_importance_df)

        return feature_importance_df['feature'].head(k).tolist()
