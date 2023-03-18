# worker/Dockerfile
FROM python:3.9
WORKDIR /worker
COPY ./requirements.txt /worker
RUN pip install --trusted-host pypi.python.org -r requirements.txt
COPY . /worker
EXPOSE 8080
CMD ["python", "worker_server.py"]
