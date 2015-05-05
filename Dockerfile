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
RUN git clone https://github.com/NMendon/bookz.git /bookz/
RUN cd /bookz/

RUN pip install -r /bookz/requirements.txt

RUN mkdir -p /var/log/bookz/

RUN . bin/activate

EXPOSE 6000

CMD gunicorn --reload --log-level INFO --log-file /var/log/bookz/gunicorn.log --error-logfile /var/log/bookz/gunicorn.error.log  -b 127.0.0.1:6000 wsgi:app
