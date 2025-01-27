FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install pymysql

COPY . /app

COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh

WORKDIR /app

EXPOSE 8000

CMD ["/bin/sh", "-c", "/wait-for-db.sh db python server.py"]
