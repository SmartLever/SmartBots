# SmartBots: Event-Drive Platform.

Cryptocurrencies, financial markets, and betting markets have never been easier. SmartBots is event-driven platform,
meaning both backtesting and live trading follow the same path.

Smartbots is not just a library; it is a platform with all the architecture needed to build a trading bot. 
Backtesting an idea and getting statistics is just the first step, but it is not enough. 
You need to be able to monetize it in real time and monitor it.

SmartBots cover the gaps to make it possible.

Lets see how it works.

## Project Breakdown
```
SmartBots
├── bots                           # folder for bots code
│   ├── bettings_trading           # folder for bots for betting
│   ├── crypto_trading             # folder for bots for crypto trading
│   ├── financial_trading          # folder for bots for  trading in financial markets
│   └── event_keeper.py            # script for saving events.
├── docker                         # folder for docker files 
│   ├── docker-compose_basic.yml   # Configuration for basic components
│   ├── docker-compose_crypto.yml  # Configuration for trading a portfolio of cryptocurrencies
│   ├── smartbot-python.dockerfile # Docker file      
│   ├── compose.env                # Configuration file for setting passwords and other variables
├── smartbots                      # Main folder with the library of the project 
│   ├── betting                    # folder for librery and helpers for betting
│   ├── crypo                      # folder for librery and helpers for crypto trading
│   ├── financial                  # folder for librery and helpers for crypto trading
├── my_smartbots                   # folder with my own strategies, you should create it and put your strategies here
│   ├── my_betting_strategies      # folder with betting strategies
    ├── my_crypto_strategies       # folder with crypto strategies
    ├── my_financial_strategies    # folder with financial strategies
├── conf.env                       # Configuration file for setting passwords and other variables
├── requirements.txt               # requirements for python


```

## Installation
   1. Clone the Project

   - Via HTTPS: `git clone https://github.com/SmartLever/SmartBots.git`
   - via SSH: `git clone https://github.com/SmartLever/SmartBots.git`
 
   2. Navigate into the project's folder

      ```bash
      cd SmartBots/
      ```
   
   3. Easy install and running, with Docker-Compose. You do not need to have Python installed on your machine.
      All will be done on the container and configurations and modifications can be done with JupyterLab.

      Docker installation instructions, please refer to the [Docker-Compose](https://docs.docker.com/compose/install/) documentation.
      Once you have Docker-Compose installed, run the following command for lauching the basics service infrastructure:
     
      ```bash
      cd docker/
      docker compose -f docker-compose_basic.yml --env-file ./compose.env up -d
      ```
      Once running, you will have:
      - portainer: Service for managing dockers. Go to your_server_ip:9000 and enter in Docker Portainer, setup the password and you will enter in a Dashboard 
      where you can manage all the dockers. 
      - mongodb: Mongo database.
      - rabbitmq: service for MQ messages.
      - event_keeper: Service for keeping the events in the database.
      - jupyterlab: service for management the code. Get the Token going  to DashBoard in portainer,
      - localize the jupyterlab container and enter in logs console to copy the token.
        Navigate to your_server_ip:4444 and paste the token. That's all.

      Wellcome to SmartBots, you can now start coding and testing your strategies and run it in real time.
      
      Backtesting an Strategy Example:
      On jupyter Lab, go and open to bots/backtesting.ipynb and run the code.
      
      Live Trading:
      ```bash
      cd docker/
      docker compose -f docker-compose_crypto.yml --env-file ./compose.env up -d
      ```
      
## More than 115 exchages implemented for Crypto.
   Smartbots follows the implementation of ccxt, so you can use all the exchanges that ccxt supports.
   Please, go to https://github.com/ccxt/ccxt/wiki/Manual#markets 

   A short List:
   * Binance
   * Bitmex
   * Bitfinex
   * Bittrex
   * Coinbase
   * Coinbase Pro
   .... and more.

## Basktesting a simple strategy in Crypto

## Updating the code of the repository changing local files
    '''git fetch
       git reset --hard HEAD
       git merge '@{u}' '''
          
## Live Trading a simple strategy in Crypto
### Open a account in Kucoin and get the Keys

## Smartbots Betting
At Smartbots Betting you can automate your sports strategy in any market offered by the broker,
in our case betfair. To make the betting platform work you first need to create an account at www.betfair.com,
once you have an account you should follow these steps to obtain the necessary keys and certs files at that url:
https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni .

When you have account, Api keys and Certs files you can execute this command:
 ```bash
 cd docker/
 docker compose -f docker-compose_betting.yml --env-file ./compose.env up -d
 ```
Your Username, Password and Keys should be put in path docker/compose.env and the certs file in smartbots/betting/certs/

Inside the docker compose we have these services:
 * provider_betting: Connect with the broker and obtain the data that will feed the strategy, in addition to saving in mongodb
 * bot_betting_trading: This service executes the strategy in this case, it is a very simple strategy, feel free to create your own strategy.
   The strategy configuration is found in this location: bots/betting_trading/config_betting.yaml
 * broker_betting: This service receives the bet and sends it to the broker and also manages the pending bets.
 * telegram_betting: For this service to work you must obtain a token by following the first part of this manual: https://www.pragnakalp.com/create-telegram-bot-using-python-tutorial-with-examples/ .
   Once you have the token you should put it in compose.env.
   With this service you will be able to control that the previous services work correctly 
   and your current balance, although many more things could be included, this is just the first version

You can also simulate the basic strategy as an example or any strategy you want to create. In the path bots/betting_trading folder there is a notebook called backtesting_betting, 
there you can download some test data, simulate and see a several of statistical ratios.

## Smartbots Financial
In smartbots financial you can create and automate any financial strategy and apply it to any asset (cfd, forex, future, shares etc...).
In this first version of financial smartbots we have developed all the logic to be able to operate with any broker that offers Metatrader 4,
in our case we have focused on darwinex.

For the financial platform to work, you should first create an account at www.darwinex.com, when you are logged in create an mt4 account in test mode for example.
Follow the steps to download mt4 on your computer, once you have mt4 installed
we have followed this tutorial to run this service and prepare it.
https://github.com/paduel/MT_zeromq_vnc_docker

When we have mt4 running in docker and with the necessary ports open, we are ready to run docker compose with all services.
Also keep in mind to put all the variables necessary for the services work correctly
in the path docker/compose.env

Run this command:
 ```bash
 cd docker/
 docker compose -f docker-compose_financial.yml --env-file ./compose.env up -d
 ```
 
Inside the docker compose we have these services:
 * data_provider_mt4: This service connects to mt4 and generates minute bars of the symbols we want.
 * bot_financial_trading: This service executes the strategy and receives the bars that feed the strategy, 
   the configuration of the strategy is found in this location: bots/financial_trading/config_financial.yaml
 * broker_mt4: Receive the order and send the order to mt4, in addition to saving balance and active positions.
 * telegram_financial: For this service to work you must obtain a token by following the first part of this manual: https://www.pragnakalp.com/create-telegram-bot-using-python-tutorial-with-examples/ .
   Once you have the token you should put it in compose.env.
   With this service you will be able to control that the previous services work correctly, in addition to seeing the real and simulated positions.
   One of the advantages of this service is that if the positions do not match or any service fails, you will receive an alert.
 * update_mongodb_financial: Updates the library where we are saving the data historical, that is, we transfer the data that is being saved in the keeper library to the historical.

You can also simulate the simple_avg_cross as an example or any strategy you want to create. In path bots/ there is a notebook called backtesting,
there you can download data, simulate and see a several of statistical ratios.
To download the data in this case from darwinex you need to have the credentials that darwinex provides you on its website in the
historical_ticks section, those credentials should be put in the docker/compose.env configuration file




## Infrastructure
docker/docker-compose.yml have all the elements to run and manage the infrastructure.
You can adapt it to your needs.

### Components:
#### MongoDB docker: Historical data
MongoDB is used to store historical data, here more info: https://github.com/man-group/arctic
For large historical data it use as defaul months chunks, here docs: https://github.com/man-group/arctic/wiki/Chunkstore


Other Info

### Subscribe to our news!
https://smartlever.substack.com/

### Bugs

Please report any bugs or issues on the GitHub's Issues page.

### Disclaimer 

Trading in financial instruments involves high risks, including the risk of losing some or all of your investment amount. It may not be suitable for all investors. Before trading any financial instrument, it's important to be informed of the risks and costs involved. You should also be aware of your investment objectives and risk levels, as well as how much information you want in order to make a decision. That being said, I recommend that you seek out a professional so they can help you find the best outcome!. The data contained in the SmartBot library is not necessarily accurate. The SmartBot website and its provider will not be liable for any loss or damage as a result of using, or your reliance on the information contained therein.

### Contributing

If you would like to support the project, pull requests are welcome.

### Licensing 

**SmartBots** is distributed under the [**GNU GENERAL PUBLIC LICENSE**]. See the [LICENSE](/LICENSE) for more details.