


class Simple_Average(object):
    def __init__(self, period: int):
        """ Compute simple average by events

        Parameters
        ----------
        period: int
            Period of the average

        """
        self.period = period
        self.value = None

    def add(self, close: float):
        self.value = (self.value * (self.period - 1) + close) / self.period
        return self.value

    def set_initial_value(self, close: float):
        self.value = close
        return self.value

    def get_value(self):
        return self.value
