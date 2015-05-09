############################################################
# Dockerfile to build Python WSGI Application Containers
# Based on Ubuntu
############################################################

# Set the base image to Ubuntu
FROM ubuntu

# File Author / Maintainer
MAINTAINER Namrata and Sid

# Add the application resources URL
RUN echo "deb http://archive.ubuntu.com/ubuntu/ $(lsb_release -sc) main universe" >> /etc/apt/sources.list

# Update the sources list
RUN apt-get update

# Install basic applications
RUN apt-get install -y tar git curl nano wget dialog net-tools build-essential

# Install Python and Basic Python Tools
RUN apt-get install -y python python-dev python-distribute python-pip

RUN mkdir /bookz/

# If SSH access needs to be granted to private repos
# we need to use the ADD command.
#git clone https://github.com/NMendon/bookz.git /bookz/
# For this we need another script to git clone the dir on the machine..
ADD . /bookz/
RUN cd /bookz/

RUN pip install -r /bookz/requirements.txt

RUN mkdir -p /var/log/bookz/

EXPOSE 6000
WORKDIR /bookz

ENV APP_CONFIG_FILE config/prod
