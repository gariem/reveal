FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Europe/London
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV DISPLAY=:99
ENV DISPLAY_CONFIGURATION=1024x768x24

ENV PATH="/miniconda3/bin:${PATH}"
ARG PATH="/miniconda3/bin:${PATH}"

SHELL ["/bin/bash", "--login", "-c"]

RUN apt-get update && apt-get install -y xvfb xorg x11-utils wget

RUN wget https://data.broadinstitute.org/igv/projects/downloads/2.12/IGV_Linux_2.12.2_WithJava.zip -O IGV_Linux_2.12.2_WithJava.zip && \
    unzip IGV_Linux_2.12.2_WithJava.zip && rm IGV_Linux_2.12.2_WithJava.zip

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-py37_4.12.0-Linux-x86_64.sh -O miniconda.sh &&  \
    yes | bash miniconda.sh -b -p /miniconda3 && rm -f miniconda.sh && conda init bash

COPY environment.yml environment.yml

RUN conda env create -f environment.yml && echo "conda activate reveal" >> ~/.bashrc

ENV PATH="/miniconda3/envs/reveal/bin:${PATH}"
ARG PATH="/miniconda3/envs/reveal/bin:${PATH}"
