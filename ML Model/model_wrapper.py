import pandas as pd
from xgboost import XGBClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split


class WrappedXGBModel:
    def __init__(self, input_cols, cat_cols, target_cols, drop_cols=None):
        self.input_cols = input_cols
        self.cat_cols = cat_cols
        self.target_cols = target_cols
        self.drop_cols = drop_cols if drop_cols is not None else []

        self.model = MultiOutputClassifier(
            XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                enable_categorical=True,
                random_state=42
            )
        )

    def _preprocess(self, df):
        X = df.copy()

        # remove unwanted columns if they exist
        X = X.drop(columns=self.drop_cols, errors="ignore")

        # keep only the input columns in the correct order
        X = X[self.input_cols].copy()

        # convert categorical columns
        for col in self.cat_cols:
            if col in X.columns:
                X[col] = X[col].astype("category")

        return X

    def fit(self, df, y):
        X = self._preprocess(df)
        self.model.fit(X, y)
        return self

    def predict(self, df):
        X = self._preprocess(df)
        preds = self.model.predict(X)

        pred_df = pd.DataFrame(
            preds,
            columns=self.target_cols,
            index=df.index
        )

        return pred_df