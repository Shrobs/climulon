FROM alpine:3.3
MAINTAINER achref.gharyeni@gmail.com

RUN \
   apk update && \
   apk upgrade && \
   apk add py-pip

RUN \
   pip install pip --upgrade --ignore-installed && \
   pip install boto3 --upgrade --ignore-installed

ADD climulon /code
WORKDIR /code
