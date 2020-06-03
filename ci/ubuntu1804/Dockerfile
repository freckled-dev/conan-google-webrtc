FROM ubuntu:18.04

COPY install-build-deps.sh install-build-deps.sh
RUN apt-get update \
  && apt-get install -y \
    lsb-release python python3-setuptools python3-wheel python3-pip fish sudo \
  && pip3 install conan \
  && ./install-build-deps.sh --no-arm --no-chromeos-fonts --no-nacl \
  && rm -rf /var/lib/apt/lists/*

