""" Bot for saving events to DataBase, recieve all events from rabbitMQ and save them
    """

def main(name_library='events_keeper') -> None:
    from smartbots.brokerMQ import receive_events
    from arctic import Arctic
    from smartbots import conf
    import datetime as dt

    def get_unique(event: dict) -> str:
        """ Get unique key for event """
        # Get first key from dict
        event_type = list(event.keys())[0]
        if event_type == 'bar':
            return f'{event[event_type].ticker}_{event[event_type].datetime}_{event_type}_{n_saved["events"]}'
        elif 'order' in event_type:
            return event[event_type].order_id_sender
        else:
            print(f'Event type {event_type}  saving as default')
            return f'{event[event_type].ticker}_{event[event_type].datetime}_{event_type}_{n_saved["events"]}'


    def callback(event: dict) -> None:
        """Callback for saving events to DataBase"""
        n_saved['events'] += 1
        event_type = list(event.keys())[0]
        ticker = event[event_type].ticker
        unique = get_unique(event)
        lib.write(unique, event, metadata={'datetime': event[event_type].datetime,
                                           'event_type':event_type, 'ticker': ticker})
        print('Event saved', event[event_type])

    # variable
    n_saved = {'events': 0}
    # Create connection  to DataBase
    store = Arctic(f'{conf.MONGO_HOST}:{conf.MONGO_PORT}', username=conf.MONGO_INITDB_ROOT_USERNAME,
                   password=conf.MONGO_INITDB_ROOT_PASSWORD)
    if not store.library_exists(name_library):
        store.initialize_library(name_library)
    lib = store[name_library]
    # Connect to brokerMQ for receiving events
    receive_events(routing_key='#', callback=callback)


if __name__ == '__main__':
    main()
