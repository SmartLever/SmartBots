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
      On jupyter Lab, go and open to bots/crypto_trading/backtesting.ipynb and run the code.
      
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