FROM python:3.8-slim-buster
WORKDIR /code

COPY master/requirements.txt .
RUN pip install -r requirements.txt

COPY master/src/ .
COPY shared/ ./shared

CMD [ "python", "./main.py" ]