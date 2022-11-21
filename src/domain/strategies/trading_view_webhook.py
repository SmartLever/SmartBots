from src.domain.abstractions.abstract_strategy import Abstract_Strategy, dataclass
import datetime as dt

class Trading_View_Webhook(Abstract_Strategy):
    """ Read signals from Trading View and send orders

        Format of the message in tradingview for strategies :
        {"exchange":"{{exchange}}","price": {{strategy.order.price}} ,"key":"1234ase",
        "type":"strategy","ticker":"{{ticker}}",
        "name":"MA2",
        "action":"{{strategy.order.action}}" ,
        "contracts":{{strategy.order.contracts}},
        "interval":"{{interval}}",
        "position_size":{{strategy.position_size}},
        "market_position":
        "{{strategy.market_position}}",
        "prev_market_position":
        "{{strategy.prev_market_position}}"}

        This msg is sent to the webhook, and transform to a webhook event

        Position could be 1 Long, 0 out of the market, or -1 Short
        Parameters
        ----------
        params: dict
            Parameters of the strategy
            ticker: str - ticker of the asset
            quantity: float  Quantity of the asset to buy or sell for a signal
    """

    def __init__(self, params, id_strategy=None, callback=None, set_basic=False):
        super().__init__(params, id_strategy, callback, set_basic)
        self.saves_values = {'datetime': [], 'position':[], 'close':[],'contracts':[]}
        self.quantity_from_hook = 0
        if 'quantity_from_hook' in params: # if quantity is not set, use the quantity from the hook
            self.quantity_from_hook = params['quantity_from_hook']
        self.name = params['name'] # unique name of the strategy that connect with the webhook message
    def add_event(self,  event: dataclass):
        """ Logic of the Strategy goes here """
        name = event.msg["name"]
        if event.event_type == 'webhook' and name == self.name: # logic for webhook messages
            market_position = event.msg["market_position"]
            if self.quantity_from_hook > 0: # tradingview webhook message has the quantity
                quantity = abs(event.msg["contracts"])
                action = event.msg["action"]
                price = event.msg["price"]
                self.contracts = quantity
            else: # quantity manage by the strategy
                quantity = self.quantity
                price = event.msg["price"]
                if market_position == 'long':
                    action = 'buy'
                    quantity = quantity - self.contracts
                elif market_position == 'short':
                    action = 'sell'
                    quantity = quantity + self.contracts
                elif market_position == 'flat':
                    if self.position == 1:
                        action = 'sell'
                        self.position = 1
                        quantity = self.contracts
                    elif self.position == -1:
                        action = 'buy'
                        self.position = -1
                        quantity = -self.contracts
            # send order
            self.send_order(ticker=self.ticker, price=price, quantity=quantity,
                            action=action, type='market', datetime=dt.datetime.utcnow())

            # Save list of values
            self.saves_values['datetime'].append(event.datetime)
            self.saves_values['position'].append(self.position)
            self.saves_values['close'].append(price)
            self.saves_values['contracts'].append(self.contracts)

