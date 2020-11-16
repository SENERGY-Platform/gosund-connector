FROM python:3-alpine

LABEL org.opencontainers.image.source https://github.com/SENERGY-Platform/gosund-connector

RUN apk update && apk upgrade && apk add git

WORKDIR /usr/src/app

COPY . .
RUN pip install -r requirements.txt

CMD [ "python", "-u", "./client.py"]
