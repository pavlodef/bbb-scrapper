FROM python:3.11-slim

WORKDIR /scrapper

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scrapper/ .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["./entrypoint.sh"]
