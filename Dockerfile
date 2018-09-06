FROM python:3.6-alpine

RUN adduser -D mindpalace 

WORKDIR /home/mindpalace

RUN apk add alpine-sdk
RUN apk add --no-cache \
    libsass \
    sassc

RUN pip install pipenv -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY Pipfile.lock Pipfile ./
RUN pipenv install -v --deploy --system --ignore-pipfile --pypi-mirror https://pypi.tuna.tsinghua.edu.cn/simple

COPY manage.py config.py .env ./
COPY app app
RUN chmod 777 manage.py

RUN chown -R mindpalace:mindpalace ./
USER mindpalace

EXPOSE 8000
ENTRYPOINT ["gunicorn", "-w", "4", "manage:app", "-b", "0.0.0.0:8000"]
