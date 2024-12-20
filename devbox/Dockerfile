FROM ubuntu:24.04 AS OSBuild

RUN apt-get update && apt-get install -y openssh-server
RUN mkdir /var/run/sshd
# change to something else, instead of password
RUN echo 'root:password' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN echo "ChallengeResponseAuthentication no" >> /etc/ssh/sshd_config
RUN echo "AddressFamily any" >> /etc/ssh/sshd_config
RUN echo "ListenAddress 0.0.0.0" >> /etc/ssh/sshd_config
RUN echo "PermitTTY yes" >> /etc/ssh/sshd_config

WORKDIR /code

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    nano \
    openjdk-11-jdk

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /code

RUN echo "cd /code" >> ~/.bashrc

CMD ["/usr/sbin/sshd", "-D"]

