import pandas as pd



def drawdown(series) -> pd.Series:
    """
    Compute the drawdown for a return series. The drawdown is defined as 1 - price/highwatermark.
    The highwatermark at time t is the highest price that has been achieved before or at time t.

    Args:
        series:

    Returns: Drawdown as a pandas series
    """
    return Drawdown(series).drawdown


class Drawdown(object):
    """
        Class for computing drawdowns
        
        :param returns: pandas Series
        :param eps: a day is down day if the drawdown (positive) is larger than eps
        
    """
    def __init__(self, returns: pd.Series, eps: float = 0) -> object:
        
        # check series is indeed a series
        assert isinstance(returns, pd.Series)
        # check that all indices are increasing
        assert returns.index.is_monotonic_increasing
        # make sure all entries non-negative
        # assert not (series < 0).any()

        self.__series = (returns + 1.0).cumprod()

        # make sure all entries non-negative
        assert not (self.__series < 0).any()

        self.__eps = eps

    @property
    def eps(self):
        return self.__eps

    @property
    def price_series(self) -> pd.Series:
        return self.__series

    @property
    def highwatermark(self) -> pd.Series:
        x = self.price_series.expanding(min_periods=1).max()
        x[x <= 1.0] = 1.0
        return x

    @property
    def drawdown(self) -> pd.Series:
        return 1 - self.price_series / self.highwatermark
