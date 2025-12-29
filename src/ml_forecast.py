import pandas as pd
from sklearn.ensemble import RandomForestRegressor

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering từ timestamp
    """
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month
    return df


def train_and_predict(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list,
    predict_row: dict
):
    """
    Huấn luyện RandomForest và dự báo 1 giá trị
    """
    df = df.dropna(subset=feature_cols + [target_col])
    if len(df) < 30:
        return None

    X = df[feature_cols]
    y = df[target_col]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        random_state=42
    )
    model.fit(X, y)

    X_pred = pd.DataFrame(
        [[predict_row[col] for col in feature_cols]],
        columns=feature_cols
    )
    
    return float(model.predict(X_pred)[0])