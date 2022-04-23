FROM python:3.9.12-buster

RUN apt-get update &&\
 apt-get install locales &&\
 sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen &&\
 sed -i 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen &&\
 locale-gen &&\
 python -m pip install pipenv &&\
 mkdir /app && mkdir /app/var
ENV LC_ALL "en_US.UTF-8"
COPY ./ /app
RUN cd /app && python -m pipenv install &&\
 mv /app/contrib/entrypoint.sh /entrypoint.sh
VOLUME [ "/app/var" ]
WORKDIR "/app"
ENTRYPOINT [ "/entrypoint.sh" ]
