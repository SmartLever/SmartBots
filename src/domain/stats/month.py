import calendar
import numpy as np
import pandas as pd


def monthlytable(returns) -> pd.DataFrame:
    """
    monthly returns

    :param returns: Serie temporal

    :return: Dataframe
    """

    def _cumulate(x):
        return (1 + x).prod() - 1.0

    # r = nav.pct_change().dropna()
    # Works better in the first month
    # Compute all the intramonth-returns, instead of reapplying some monthly resampling of the NAV
    return_monthly = returns.groupby([returns.index.year, returns.index.month]).apply(_cumulate)
    frame = return_monthly.unstack(level=1).rename(columns=lambda x: calendar.month_abbr[x])
    ytd = frame.apply(_cumulate, axis=1)
    frame["STDev"] = np.sqrt(12) * frame.std(axis=1)
    # make sure that you don't include the column for the STDev in your computation
    frame["YTD"] = ytd
    frame.index.name = "Year"
    frame.columns.name = None
    # most recent years on top
    return frame.iloc[::-1]

