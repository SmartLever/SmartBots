import pandas as pd


def Normalize(ts: pd.Series, value=100.0) -> pd.Series:
    """
    Normalize a time series to a value
        
    """
    try:
        return value * ts / (ts.dropna().iloc[0])
    except IndexError:
        # can happen if the series is empty (after droping all NaNs)
        return None

