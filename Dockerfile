FROM python:3.6-alpine

RUN adduser -D mindpalace 

WORKDIR /home/mindpalace

RUN apk add alpine-sdk

RUN pip install pipenv -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --ignore-pipfile -v --pypi-mirror https://pypi.tuna.tsinghua.edu.cn/simple

COPY manage.py .env ./
COPY app ./
RUN chmod +x manage.py

RUN chown -R mindpalace:mindpalace ./
USER mindpalace

EXPOSE 8000
ENTRYPOINT ["pipenv run python ./manager.py runserver"]
