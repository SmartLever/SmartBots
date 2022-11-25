import pandas as pd
import numpy as np


class BetsToEquity(object):
    def __init__(self, bets=[], list_result={}, capital_init=40000, risk=0.005, commission=0.02):
        """
        Calculate equity for received bets

        :param bets: bets events
        :param capital_init
        :param risk
        :param commission
         """

        self.capital_init = capital_init
        self.risk = risk
        self.capitan_risk = self.capital_init
        self.equity = []
        self.datetime = []
        self.commission = commission
        self.bets = []
        self.list_result = list_result
        self.success = 0
        self.failed = 0
        self.sum_odds = 0

        if len(bets) > 0:
            self.bets = sorted(bets, key=lambda x: x.datetime)
            for bet in self.bets:
                self.add(bet)

    def add(self, bet):
        """
        add bet y calculate equity
        :param bet:
        :return:
        """

        result = self.get_result(bet)
        if len(self.equity) > 0:  # sum result
            equity = round(self.equity[-1] + result, 2)
        else:  # first bet
            self.equity.append(self.capital_init)
            self.datetime.append(bet.datetime)
            equity = self.capital_init + result

        # update equity
        self.equity.append(equity)
        self.datetime.append(bet.datetime)

    def get_result(self, bet):
        """
        Calculate result
        :return:
        """
        result_before_tax = 0
        total_comission = 0
        self.sum_odds += bet.odds
        if bet.unique_name in self.list_result:
            result = self.list_result[bet.unique_name ]
            if bet.action == 'back' and result == 1:  # bet back and win
                result_before_tax = (bet.odds - 1) * bet.quantity
                total_comission = result_before_tax * self.commission
                self.success += 1
            elif bet.action == 'back' and result == 0:  # bet back and lost
                result_before_tax = (-1) * bet.quantity
                self.failed += 1
            elif bet.action == 'lay' and result == 1:  # bet lay and lost
                result_before_tax = -(bet.odds - 1) * bet.quantity
                self.failed += 1
            elif bet.action == 'lay' and result == 0:  # bet lay and win
                result_before_tax = self.quantity
                total_comission = result_before_tax * self.commission
                self.success += 1

        return float(result_before_tax - abs(total_comission))


def drawdown(dates, prices):
    """
    calculate max draw_down and duration

    Input:
        pnl
    Returns:
        draw_down : vector of drawdwon values
        duration : vector of draw_down duration

    """
    total = len(dates)
    highwatermark = np.zeros(total)
    draw_down = np.zeros(total)
    drawdown_dur = np.zeros(total)

    for t in range(1, total):
        highwatermark[t] = max(highwatermark[t - 1], prices[t])
        draw_down[t] = (highwatermark[t] - prices[t]) / highwatermark[t]
        drawdown_dur[t] = (0 if draw_down[t] == 0 else drawdown_dur[t - 1] + 1)

    return pd.DataFrame({'draw_down': draw_down, 'drawdowndur': drawdown_dur}, index=dates)


def total_return(equity):
    start = equity.index[0]
    end = equity.index[-1]
    return (equity[end] - equity[start]) / equity[start] * 100


def annual_return(equity, difference_prices=True):
    """calculates annual return from daily prices"""
    start = equity.index[0]
    end = equity.index[-1]
    if difference_prices:
        difference = float((end - start).days)
    else:
        difference = len(equity)
    days = 365.0
    return ((equity[end] / equity[start]) ** (days / difference) - 1) * 100


def equity_to_variations_month_year(equities, _type='M'):
    """calculate the monthly and annual variations from equity:
       _type : M for month , A per year """
    data = equities.resample(_type).last()
    data = pd.concat([data, equities[equities.index == equities.index[0]]]).sort_index()
    dates = data.index
    data.index = range(len(data))
    variations = data.pct_change()
    variations.index = dates
    variations = variations[1:]
    return variations * 100

