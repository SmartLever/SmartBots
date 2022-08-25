# SmartBots: Event-Drive Platform.

Cryptocurrencies, financial markets, and betting markets have never been easier. SmartBots is event-driven platform,
meaning both backtesting and live trading follow the same path.

Smartbots is not just a library; it is a platform with all the architecture needed to build a trading bot. 
Backtesting an idea and getting statistics is just the first step, but it is not enough. 
You need to be able to monetize it in real time and monitor it.

SmartBots cover the gaps to make it possible.

Lets see how it works.

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
      Once you have Docker-Compose installed, run the following command:
     
      ```bash
      cd docker/
      docker compose --env-file ./compose.env up -d
      ```
      Once all the containers are up and running. 
      Go to your_server_ip:9000 and enter in Docker Portainer, setup the password and you will enter in a Dashboard 
      where you can manage all the dockers. 
      Once inside, locate JupyterLab docker and click on logs tab, copy the token that you will find on the console.
      Go to your_server_ip:8888 and paste the token on the password field. 
      
      Wellcome to SmartBots, you can now start coding and testing your strategies and run it in real time.
      
      Example for running a strategy with Kucoin go here: ....
     
   6. you can access the JupyterLab on your browser at `http://localhost:8888`.
   7. Activate the virtual environment

      ```bash
      conda activate ebots
      ```

   8. Install dependencies with poetry

      Install the main dependencies with

      ```bash
      poetry install
      ```
      If you are having trouble with Poetry, use install requirements.txt with pip
   
      ```bash
      pip install -r requirements.txt
      ```
## Basktesting a simple strategy in Crypto
      
## Live Trading a simple strategy in Crypto
### Open a account in Kucoin and get the Keys


## Infrastructure
docker/docker-compose.yml have all the elements to run and manage the infrastructure.
You can adapt it to your needs.

### Components:
#### MongoDB docker: Historical data
MongoDB is used to store historical data, here more info: https://github.com/man-group/arctic
For large historical data it use as defaul months chunks, here docs: https://github.com/man-group/arctic/wiki/Chunkstore