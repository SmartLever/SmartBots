import numpy as np


def var(series, alpha=0.99):
    return VaR(series, alpha).var


def cvar(series, alpha=0.99):
    return VaR(series, alpha).cvar


class VaR(object):
    def __init__(self, returns, alpha=0.99):
        self.__series = returns.dropna()
        self.__alpha = alpha

    @property
    def __losses(self):
        return self.__series * (-1)

    @property
    def __tail(self):
        losses = self.__losses
        return np.sort(losses.values)[int(len(losses) * self.alpha):]

    @property
    def cvar(self):
        return self.__tail.mean()

    @property
    def var(self):
        return self.__tail[0]

    @property
    def alpha(self):
        return self.__alpha