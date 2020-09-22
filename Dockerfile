FROM ubuntu
RUN apt-get update
RUN apt-get --assume-yes install \
    librrd-dev \
    libxml2-dev \
    libglib2.0 \
    libcairo2-dev \
    libpango1.0-dev \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-venv \
    build-essential
WORKDIR /build/
COPY . /build/
RUN pip3 install -r requirements.txt && python3 setup.py install
EXPOSE 5000
CMD ["./manage.py", "runserver"]
