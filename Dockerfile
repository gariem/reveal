FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Europe/London
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV DISPLAY=:99
ENV DISPLAY_CONFIGURATION=1024x768x24

ENV PATH="/miniconda3/envs/reveal/bin:/miniconda3/bin:${PATH}"
ARG PATH="/miniconda3/envs/reveal/bin:/miniconda3/bin:${PATH}"

SHELL ["/bin/bash", "--login", "-c"]

RUN apt-get update && apt-get install -y wget git build-essential autoconf  \
    zlib1g-dev libbz2-dev liblzma-dev libcurl4-gnutls-dev libncurses5-dev \
    bedtools \
    xvfb xorg x11-utils

RUN wget https://data.broadinstitute.org/igv/projects/downloads/2.12/IGV_Linux_2.12.2_WithJava.zip -O IGV_Linux_2.12.2_WithJava.zip && \
    unzip IGV_Linux_2.12.2_WithJava.zip && rm IGV_Linux_2.12.2_WithJava.zip

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-py37_4.12.0-Linux-x86_64.sh -O miniconda.sh &&  \
    yes | bash miniconda.sh -b -p /miniconda3 && rm -f miniconda.sh && conda init bash

COPY environment.yml environment.yml

RUN conda env create -f environment.yml && echo "conda activate reveal" >> ~/.bashrc

# htslib, bcftools, and samtools
RUN git clone -b 1.13 https://github.com/samtools/htslib.git && \
    cd htslib && git submodule update --init --recursive && make -j `nproc` && make install && \
    cd .. && rm -rf htslib

RUN git clone -b 1.13 https://github.com/samtools/bcftools.git && \
    cd bcftools && autoheader && autoconf && ./configure && make -j `nproc` && make install && \
    cd .. && rm -rf bcftools

RUN git clone -b 1.13 https://github.com/samtools/samtools.git && \
    cd samtools && autoheader && autoconf && ./configure && make -j `nproc` && make install && \
    cd .. && rm -rf samtools

ENV PATH="$PATH:/IGV_Linux_2.12.2/jdk-11/bin"
