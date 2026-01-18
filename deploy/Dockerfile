FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update &&\
    apt-get install -y locales &&\
    sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen &&\
    sed -i 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen &&\
    locale-gen &&\
    mkdir /app && mkdir /app/var
ENV LC_ALL "en_US.UTF-8"
COPY ./ /app
RUN cd /app && uv sync
VOLUME [ "/app/var" ]
WORKDIR "/app"
ENTRYPOINT [ "uv", "run", "telegram-rutor-bot" ]
CMD [ "bot" ]
