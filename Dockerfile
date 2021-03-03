FROM python:3-slim-buster

LABEL org.opencontainers.image.source https://github.com/SENERGY-Platform/gosund-connector

RUN apt-get update && apt-get install -y git

WORKDIR /usr/src/app

COPY . .
RUN pip install -r requirements.txt

CMD [ "python", "-u", "./client.py"]
