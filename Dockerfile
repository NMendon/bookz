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

RUN git clone git@github.com:NMendon/bookz.git /bookz/

RUN pip install -r /bookz/requirements.txt

RUN mkdir -p /var/log/bookz/

EXPOSE 6000

RUN cd /bookz/

RUN . bin/activate

RUN gunicorn --reload --log-level INFO --log-file /var/log/bookz/gunicorn.log --error-logfile /var/log/bookz/gunicorn.error.log  -b 127.0.0.1:5000 app:app
