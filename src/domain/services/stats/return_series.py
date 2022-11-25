from collections import OrderedDict
from datetime import date

import numpy as np
import pandas as pd

from src.domain.services.stats.drawdown import drawdown
from src.domain.services.stats.month import monthlytable
from src.domain.services.stats.periods import period_returns
from src.domain.services.stats.var import VaR


def from_nav(nav):
    return _ReturnSeries(last_nav=nav.dropna().values[-1], series=nav.dropna().pct_change().fillna(0.0))


def from_returns(returns):
    r = returns.dropna()
    nav = (r + 1.0).prod()
    return _ReturnSeries(last_nav=nav, series=r)


def performance(nav, alpha=0.95, periods=None):
    return from_nav(nav).summary(alpha=alpha, periods=periods)


class _ReturnSeries(pd.Series):
    def __init__(self, last_nav, series):
        super(_ReturnSeries, self).__init__(series)
        self.__n = last_nav

        if not self.empty:
            # change to DateTime
            if isinstance(self.index[0], date):
                self.rename(index=lambda x: pd.Timestamp(x), inplace=True)

            # check that all indices are increasing
            assert self.index.is_monotonic_increasing

    @property
    def last_nav(self):
        return self.__n

    @property
    def nav(self):
        cumprod = (self + 1.0).cumprod()
        return self.last_nav/cumprod.values[-1]*cumprod

    @property
    def periods_per_year(self):
        if len(self.index) >= 2:
            x = pd.Series(data=self.index)
            return np.round(365 * 24 * 60 * 60 / x.diff().mean().total_seconds(), decimals=0)
        else:
            return 256

    @property
    def annual_returns(self):
        return (self + 1.0).groupby(self.index.year).prod() - 1.0

    @property
    def monthly_returns(self):
        return (self + 1.0).groupby([self.index.year, self.index.month]).prod() - 1.0

    @property
    def tail_month(self):
        first_day_of_month = (self.index[-1] + pd.offsets.MonthBegin(-1)).date()
        return self.truncate(before=first_day_of_month)

    @property
    def tail_year(self):
        first_day_of_year = (self.index[-1] + pd.offsets.YearBegin(-1)).date()
        return self.truncate(before=first_day_of_year)

    def resample(self, rule, **kwargs):
        return (self + 1.0).resample(rule=rule).prod() - 1.0

    @property
    def positive_events(self):
        return (self >= 0).sum()

    @property
    def negative_events(self):
        return (self < 0).sum()

    @property
    def events(self):
        return self.size

    @staticmethod
    def __gmean(a):
        # geometric mean A
        # Prod [a_i] == A^n
        # Apply log on both sides
        # Sum [log a_i] = n log A
        # => A = exp(Sum [log a_i] // n)
        return np.exp(np.mean(np.log(a)))

    def recent(self, n=15) -> pd.Series:
        return self.tail(n).dropna()

    def var(self, alpha=0.95):
        return VaR(returns=self, alpha=alpha).var

    def cvar(self, alpha=0.95):
        return VaR(returns=self, alpha=alpha).cvar

    def truncate(self, before=None, after=None, axis=None, copy=True):
        r = super().truncate(before=before, after=after, axis=axis, copy=copy)
        last = self.nav[r.index[-1]]

        return _ReturnSeries(last_nav=last, series=r)

    def ewm_volatility(self, com=50, min_periods=50, periods=None):
        periods = periods or self.periods_per_year
        return np.sqrt(periods) * self.ewm(com=com, min_periods=min_periods).std(bias=False)

    @property
    def monthlytable(self) -> pd.DataFrame:
        return monthlytable(self)

    @property
    def drawdown(self) -> pd.Series:
        return drawdown(series=self)

    @property
    def period_returns(self):
        # check series is indeed a series
        # assert isinstance(returns, pd.Series)
        # check that all indices are increasing
        # assert returns.index.is_monotonic_increasing
        # make sure all entries non-negative
        # assert not (prices < 0).any()

        return period_returns(returns=self, today=self.index[-1])

    def to_frame(self, name=""):
        frame = self.nav.to_frame("{name}-nav".format(name=name))
        frame["{name}-drawdown".format(name=name)] = self.drawdown
        return frame

    def annualized_volatility(self, periods=None):
        t = periods or self.periods_per_year
        return np.sqrt(t) * self.dropna().std()

    def sharpe_ratio(self, periods=None, r_f=0):
        return self.__mean_r(periods, r_f=r_f) / self.annualized_volatility(periods)

    def __mean_r(self, periods=None, r_f=0):
        # annualized stats over a risk_free rate r_f (annualized)
        periods = periods or self.periods_per_year
        return periods * (self.__gmean(self + 1.0) - 1.0) - r_f

    def sortino_ratio(self, periods=None, r_f=0):
        periods = periods or self.periods_per_year
        # cover the unrealistic case of 0 drawdown
        m = self.drawdown.max()
        if m == 0:
            return np.inf
        else:
            return self.__mean_r(periods, r_f=r_f) / m

    def calmar_ratio(self, periods=None, r_f=0):
        periods = periods or self.periods_per_year
        start = self.index[-1] - pd.DateOffset(years=3)
        # truncate the nav
        return self.truncate(before=start).sortino_ratio(periods=periods, r_f=r_f)

    def summary_format(self, alpha=0.95, periods=None, r_f=0):
        perf = self.summary(alpha=alpha, periods=periods, r_f=r_f)
        print(perf)

        f = lambda x: "{0:.2f}%".format(float(x))
        for name in ["Return", "Annua Return", "Annua Volatility", "Max Drawdown", "Max % return", "Min % return",
                     "MTD", "YTD", "Current Drawdown", "Value at Risk (alpha = 95)",
                     "Conditional Value at Risk (alpha = 95)"]:
            perf[name] = f(perf[name])

        f = lambda x: "{0:.2f}".format(float(x))
        for name in ["Annua Sharpe Ratio (r_f = 0)", "Calmar Ratio (3Y)", "Current Nav", "Max Nav", "Kurtosis"]:
            perf[name] = f(perf[name])

        f = lambda x: "{:d}".format(int(x))
        for name in ["# Events", "# Events per year", "# Positive Events", "# Negative Events"]:
            perf[name] = f(perf[name])

        return perf



    def summary(self, alpha=0.95, periods=None, r_f=0):
        periods = periods or self.periods_per_year

        d = OrderedDict()

        d["Return"] = 100 * ((self + 1).cumprod() - 1.0).tail(1).values[0]
        d["# Events"] = self.events
        d["# Events per year"] = periods

        d["Annua Return"] = 100 * self.__mean_r(periods=periods)
        d["Annua Volatility"] = 100 * self.annualized_volatility(periods=periods)
        d["Annua Sharpe Ratio (r_f = {0})".format(r_f)] = self.sharpe_ratio(periods=periods, r_f=r_f)

        dd = self.drawdown
        d["Max Drawdown"] = 100 * dd.max()
        d["Max % return"] = 100 * self.max()
        d["Min % return"] = 100 * self.min()

        d["MTD"] = 100 * ((self.tail_month + 1.0).prod() - 1.0)
        d["YTD"] = 100 * ((self.tail_year + 1.0).prod() - 1.0)
        #
        d["Current Nav"] = self.nav.values[-1]
        d["Max Nav"] = self.nav.max()
        d["Current Drawdown"] = 100 * dd[dd.index[-1]]
        #
        d["Calmar Ratio (3Y)"] = self.calmar_ratio(periods=periods, r_f=r_f)
        #
        d["# Positive Events"] = self.positive_events
        d["# Negative Events"] = self.negative_events
        #
        d["Value at Risk (alpha = {alpha})".format(alpha=int(100 * alpha))] = 100 * self.var(alpha=alpha)
        d["Conditional Value at Risk (alpha = {alpha})".format(alpha=int(100 * alpha))] = 100 * self.cvar(alpha=alpha)
        d["First at"] = self.index[0].date()
        d["Last at"] = self.index[-1].date()
        d["Kurtosis"] = self.kurtosis()

        x = pd.Series(d)
        x.index.name = "Performance number"
        #print(x)
        return x

