FROM cs50/cli

RUN sudo apt update && sudo apt install --yes libmysqlclient-dev pgloader postgresql pkg-config && sudo rm -rf /var/lib/apt/lists/*
RUN sudo pip3 install mysqlclient psycopg2-binary

WORKDIR /mnt
