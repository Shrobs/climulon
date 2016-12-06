FROM alpine:3.3
MAINTAINER achref.gharyeni@gmail.com

RUN \
   apk update && \
   apk upgrade

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache

RUN pip3 install boto3 --upgrade --ignore-installed

ADD climulon /code

RUN ln -s /code/climulon /usr/bin/climulon

WORKDIR /code
