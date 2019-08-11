FROM python:alpine3.7
COPY . /app
WORKDIR /app
RUN pip install .
EXPOSE 8080
CMD run-app
# docker build --tag service-image .
# docker run --rm -it --name service-instance -p 8080:8080 service-instance
