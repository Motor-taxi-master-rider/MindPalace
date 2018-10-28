FROM python:3.6-alpine

RUN adduser -D mindpalace

WORKDIR /home/mindpalace

RUN apk add alpine-sdk
RUN apk add --no-cache \
    libsass \
    sassc

RUN pip install pipenv -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install pip==18.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY Pipfile.lock Pipfile ./
RUN pipenv install -v --deploy --system --ignore-pipfile --pypi-mirror https://pypi.tuna.tsinghua.edu.cn/simple

RUN chown -R mindpalace:mindpalace ./

EXPOSE 8000
