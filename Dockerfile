FROM python:alpine3.7
COPY . /app
WORKDIR /app
RUN pip install .
EXPOSE 8080
CMD run-app
# docker build --tag service .
# docker run service
