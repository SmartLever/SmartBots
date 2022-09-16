FROM debian:latest
MAINTAINER Conda Development Team <conda@continuum.io>

RUN apt-get -qq update && apt-get -qq -y install curl bzip2 \
    && curl -sSL https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -bfp /usr/local \
    && rm -rf /tmp/miniconda.sh \
    && conda install -y python=3.8 \
    && conda install git \
    && conda update conda \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && conda clean --all --yes

ENV PATH /opt/conda/bin:$PATH
RUN mkdir /app
WORKDIR /app
RUN apt-get update
RUN apt-get -y install gcc
RUN apt-get -y install g++
COPY ./requirements.txt requirements.txt
COPY ./proyect_modules.py proyect_modules.py
RUN pip install -r requirements.txt
RUN python proyect_modules.py
