# Stage 1: Build Frontend
FROM node:20-slim AS frontend-build
WORKDIR /app
COPY frontend/package.json ./
RUN npm install
COPY frontend ./
RUN npm run build

# Stage 2: Runtime
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

# Copy python app
COPY ./ /app
# Copy built frontend assets
COPY --from=frontend-build /app/dist /app/frontend/dist

RUN cd /app && uv sync
VOLUME [ "/app/var" ]
WORKDIR "/app"
ENTRYPOINT [ "uv", "run", "telegram-rutor-bot" ]
CMD [ "bot" ]
