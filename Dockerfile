FROM alpine

RUN apk --no-cache add python3 py3-pyserial py3-yaml

COPY . /app
WORKDIR /app

USER 1000:1000

CMD ["python3", "."]
