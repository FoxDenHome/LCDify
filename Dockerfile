FROM alpine

RUN apk --no-cache add python3 py3-pyserial

COPY . /app
WORKDIR /app

USER nobody:nobody

CMD ["python3", "."]
