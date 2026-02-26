# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update &&\
    apt-get install -y locales &&\
    sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen &&\
    sed -i 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen &&\
    locale-gen &&\
    mkdir /app && mkdir /app/var &&\
    useradd -m rutor && \
    chown -R rutor:rutor /app
ENV LC_ALL "en_US.UTF-8"
COPY --chown=rutor:rutor ./ /app
# Copy built frontend from stage 1
COPY --from=frontend-builder --chown=rutor:rutor /frontend/dist /app/frontend/dist
USER rutor
RUN cd /app && uv sync
VOLUME [ "/app/var" ]
WORKDIR "/app"
ENTRYPOINT [ "uv", "run", "telegram-rutor-bot" ]
CMD [ "bot" ]
