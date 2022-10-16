""" Bot for saving events to DataBase, recieve all events from rabbitMQ and save them
    """
import dataclasses

def main(_name_library='events_keeper') -> None:
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
            return f'{event.ticker}_{event.datetime}_{event.event_type}_{saved_variable["events"]}'
        elif event.event_type == 'order':
            return event.order_id_sender
        elif event.event_type == 'health':  # always the same for service
            return f'{event.ticker}_{event.event_type}'
        elif event.event_type == 'positions':  # always the same for account
            return f'{event.account}'
        elif event.event_type == 'odds':
            return f'{event.unique_name}_{event.datetime}_{saved_variable["events"]}'
        elif event.event_type == 'bet':
            return f'{event.unique_name}_{event.bet_id}'
        else:
            print(f'Event type {event.event_type}  saving as default')
            return f'{event.ticker}_{event.datetime}_{event.event_type}_{saved_variable["events"]}'

    def callback(event : dataclasses.dataclass) -> None:
        """Callback for saving events to DataBase"""
        saved_variable['events'] += 1
        ticker = event.ticker
        unique = get_unique(event)
        # check if a string is in ASCII
        if unique.isascii() is False:
            unique = unique.encode('ascii', 'ignore').decode('ascii')

        saved_variable['lib'].write(unique, event, metadata={'datetime': event.datetime,
                                    'event_type': event.event_type, 'ticker': ticker})

        print(f'Event saved {event.event_type} {event.datetime}', )

        name = f'{_name_library}_{event.datetime.strftime("%Y%m%d")}'
        if name != saved_variable['name']:
            saved_variable['lib'] = store.get_library(name, type_library=False)
            saved_variable['name'] = name
            print('New library created', name)

    # variable
    saved_variable = {'events': 0}
    # Create connection  to DataBase
    store = Universe()
    # Create library for saving events
    name = f'{_name_library}_{dt.datetime.utcnow().strftime("%Y%m%d")}'
    saved_variable['lib'] = store.get_library(name, type_library=False)
    saved_variable['name'] = name

    # Connect to brokerMQ for receiving events
    receive_events(routing_key='#', callback=callback)


if __name__ == '__main__':
    main()
