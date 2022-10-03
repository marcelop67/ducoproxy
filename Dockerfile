FROM tiangolo/uwsgi-nginx-flask:python3.8

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LISTEN_PORT=8510

EXPOSE 8510

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY ./app /app

