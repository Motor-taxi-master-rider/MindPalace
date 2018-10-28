FROM python:3.6-alpine

RUN adduser -D mindpalace

WORKDIR /home/mindpalace

RUN apk add alpine-sdk
RUN apk add --no-cache \
    libsass \
    sassc \
    supervisor

RUN pip install pipenv==2018.10.9 -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install pip==18.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY Pipfile.lock Pipfile ./
RUN pipenv install -v --deploy --system --ignore-pipfile --pypi-mirror https://pypi.tuna.tsinghua.edu.cn/simple

RUN chown -R mindpalace:mindpalace ./

EXPOSE 8000
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/home/mindpalace/deploy/supervisor/supervisord.conf"]
