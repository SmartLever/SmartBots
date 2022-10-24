""" Historical data from Financial"""
import pandas as pd
import datetime as dt
from smartbots.financial.utils import read_historical, save_historical, get_day_per_month
from smartbots import conf
import darwinex_ticks

dwt = darwinex_ticks.DarwinexTicksConnection(dwx_ftp_user=conf.DWT_FTP_USER,
                                             dwx_ftp_pass=conf.DWT_FTP_PASS,
                                             dwx_ftp_hostname=conf.DWT_FTP_HOSTNAME,
                                             dwx_ftp_port=conf.DWT_FTP_PORT)

def _get_historical_data(name_library, start_date=dt.datetime(2022, 7, 1), end_date=dt.datetime.utcnow(),
                         interval='1min'):
    """ Read historical data save in file, and Saving in MongoDB"""

    for ticker in tickers:
        print(dt.datetime.utcnow())
        # Read historical data from darwinex
        _start_date = start_date.strftime("%Y-%m-%d")
        _end_date = end_date.strftime("%Y-%m-%d")
        data = dwt.ticks_from_darwinex(ticker, start=_start_date,
                                       end=_end_date)

        print(dt.datetime.utcnow())
        if len(data) > 0:
            data.index = data.index.tz_localize(None)
            data['datetime'] = data.index
            data['date'] = data['datetime'].dt.floor('Min')
            data['price'] = (data['Ask'] + data['Bid']) / 2
            data['volume'] = data['Ask_size'] + data['Bid_size']
            # Get open, low, high and close
            ohlc = data['price'].astype(float).resample(interval).ohlc()
            # Group by volume, bid and ask and get this values
            groupby_volume = data.groupby(["date"])["volume"].sum().to_frame()
            groupby_volume.index.name = 'datetime'
            groupby_ask = data.groupby(["date"])["Ask"].last().to_frame()
            groupby_ask.index.name = 'datetime'
            groupby_bid = data.groupby(["date"])["Bid"].last().to_frame()
            groupby_bid.index.name = 'datetime'
            # Fill columns
            ohlc['volume'] = groupby_volume['volume']
            ohlc['bid'] = groupby_bid['Bid']
            ohlc['ask'] = groupby_ask['Ask']
            ohlc['ticker'] = ticker
            ohlc['symbol'] = ticker
            ohlc['datetime'] = ohlc.index
            ohlc['dtime_zone'] = 'UTC'
            ohlc['exchange'] = 'mt4_darwinex'
            ohlc['provider'] = 'mt4_darwinex'
            ohlc['freq'] = interval
            ohlc['multiplier'] = 1
            ohlc['month'] = ohlc['datetime'].dt.month.astype(str) + '_' + ohlc['datetime'].dt.year.astype(str)
            ohlc = ohlc.fillna(method="ffill")
            if len(ohlc) >0:  # save data
                # for each month
                for m in ohlc['month'].unique():
                    # Read historical data for this month
                    ohlc_per_month = ohlc[ohlc['month'] == m]
                    month = int(m.split('_')[0])
                    year = int(m.split('_')[1])
                    start = dt.datetime(year, month, 1)
                    end = dt.datetime(year, month, get_day_per_month(month, year))
                    data_last = read_historical(ticker, name_library, start_date=start, end_date=end)
                    if len(data_last) > 1:
                        final_data = ohlc_per_month[ohlc_per_month.index > data_last.index.max() - dt.timedelta(days=1)]
                        final_data = pd.concat([data_last, final_data])
                    else:
                        final_data = ohlc_per_month
                    save_historical(ticker, final_data, name_library=name_library)
            print(f'* Historical data for {ticker} saved')

def main():
    """ Main function """
    global tickers

    provider = 'darwinex'
    name_library = f'{provider}_historical_1min'
    tickers = conf.FINANCIAL_SYMBOLS
    start_date = dt.datetime(2022, 10, 1)
    end_date = dt.datetime(2022, 10, 30)
    _get_historical_data(name_library, start_date=start_date, end_date=end_date,
                         interval='1min')


if __name__ == '__main__':
    main()