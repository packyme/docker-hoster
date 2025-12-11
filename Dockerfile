FROM python:3.12-slim

WORKDIR /hoster
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY hoster.py .

CMD ["python3", "-u", "hoster.py"]



