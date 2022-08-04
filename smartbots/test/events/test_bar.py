""" Create unitest for Bar class"""
import unittest as ut
from smartbots.events import Bar
import datetime as dt


class TestBar(ut.TestCase):
    def test_bar(self):
        bar = Bar(
            datetime=dt.datetime.now(),
            ticker="GBL",
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.0,
            volume=100.0,
            open_interest=100.0,
            bid=100.0,
            ask=101.0,
            multiplier=1.0,
            contract_size=1.0,
            contract_month_year=201912,
            contract="GBL201912",
            freq="1m",
            exchange="EURONEXT",
            currency="EUR",
            provider="INTERACTIVEBROKERS",
            type_bar="FUT",
        )
        self.assertEqual(bar.datetime, dt.datetime.now())
        self.assertEqual(bar.ticker, "GBL")
        self.assertEqual(bar.open, 100.0)
        self.assertEqual(bar.high, 101.0)
        self.assertEqual(bar.low, 99.0)
        self.assertEqual(bar.close, 100.0)
        self.assertEqual(bar.volume, 100.0)
        self.assertEqual(bar.open_interest, 100.0)
        self.assertEqual(bar.bid, 100.0)
        self.assertEqual(bar.ask, 101.0)
        self.assertEqual(bar.multiplier, 1.0)
        self.assertEqual(bar.contract_size, 1.0)
        self.assertEqual(bar.contract_month_year, 201912)
        self.assertEqual(bar.contract, "GBL201912")
        self.assertEqual(bar.freq, "1m")
        self.assertEqual(bar.exchange, "EURONEXT")
        self.assertEqual(bar.currency, "EUR")
        self.assertEqual(bar.provider, "INTERACTIVEBROKERS")
        self.assertEqual(bar.type_bar, "FUT")



if __name__ == '__main__':
    ut.main()