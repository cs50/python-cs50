FROM cs50/cli

RUN sudo apt update && sudo apt install --yes libmysqlclient-dev pgloader postgresql build-essential pkg-config libpq-dev
RUN sudo pip3 install mysqlclient psycopg2-binary
RUN sudo rm -rf /var/lib/apt/lists/*

WORKDIR /mnt
