FROM python:3.8-slim-buster
WORKDIR /code

COPY secondary/requirements.txt .
RUN pip install -r requirements.txt

COPY secondary/src/ .
COPY shared/ ./shared

CMD [ "python", "./main.py" ]