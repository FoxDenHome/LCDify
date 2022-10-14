FROM alpine

RUN apk --no-cache add python3 py3-pyserial py3-yaml py3-requests

COPY . /app
WORKDIR /app

ENV PUID=1000
ENV PGID=1000
ENV MAKE_TTY_DEVS=10

CMD ["python3", "."]
