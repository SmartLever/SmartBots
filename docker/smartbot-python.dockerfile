FROM python:3.8-slim-buster

RUN apt-get update
RUN apt-get -y install gcc
RUN apt-get -y install g++
RUN apt-get -y install git-all


RUN mkdir /app
WORKDIR /app

ENV PATH="/home/python/.local/bin:${PATH}"

RUN pip install --upgrade pip
RUN pip install "poetry==1.1.12"
COPY ./requirements.txt requirements.txt
COPY ./proyect_modules.py proyect_modules.py
RUN pip install -r requirements.txt


RUN python proyect_modules.py # add smartbot the project as a module
