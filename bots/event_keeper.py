""" Bot for saving events to DataBase, recieve all events from rabbitMQ and save them
    """
import dataclasses


def main(name_library='events_keeper') -> None:
    import time
    time.sleep(10) # wait until MQ and Database are running
    from smartbots.brokerMQ import receive_events
    from smartbots.database_handler import Universe
    from smartbots import conf
    import datetime as dt

    def get_unique(event: dataclasses.dataclass) -> str:
        """ Get unique key for event """
        # Get first key from dict
        if event.event_type == 'bar':
            return f'{event.ticker}_{event.datetime}_{event.event_type}_{n_saved["events"]}'
        elif event.event_type == 'order':
            return event.order_id_sender
        elif event.event_type == 'health': #always the same for service
            return f'{event.ticker}_{event.event_type}'
        else:
            print(f'Event type {event.event_type}  saving as default')
            return f'{event.ticker}_{event.datetime}_{event.event_type}_{n_saved["events"]}'


    def callback(event : dataclasses.dataclass) -> None:
        """Callback for saving events to DataBase"""
        n_saved['events'] += 1
        ticker = event.ticker
        unique = get_unique(event)
        lib.write(unique, event, metadata={'datetime': event.datetime,
                                           'event_type':event.event_type, 'ticker': ticker})
        print('Event saved', event.event_type)

    # variable
    n_saved = {'events': 0}
    # Create connection  to DataBase
    store = Universe()
    lib = store.get_library(name_library)

    # Connect to brokerMQ for receiving events
    receive_events(routing_key='#', callback=callback)


if __name__ == '__main__':
    main()
