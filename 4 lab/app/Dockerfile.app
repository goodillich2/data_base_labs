FROM python:3.10.7-slim-buster

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y libpq-dev

COPY . .

# Create a subdirectory for output files
RUN mkdir files

CMD ["python", "main.py"]
