FROM python:3.8.3-slim-buster AS base

RUN apt-get update
RUN apt-get install -y netcat

# Dedicated Workdir for App
WORKDIR /monitoring

# Do not run as root
RUN useradd -m -r monitoring && \
    chown monitoring /monitoring

COPY requirements.txt /monitoring
# RUN pip3 install -r requirements.txt

FROM base AS src
COPY . /monitoring

# install monitoring here as a python package
RUN pip3 install .
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir --use-deprecated=legacy-resolver RainbowMonitoringSDK==0.0.4
# USER monitoring is commented to fix the bug related to permission
# USER monitoring

COPY scripts/docker-entrypoint.sh /entrypoint.sh

# Use the `monitoring` binary as Application
FROM src AS prod

# this is add to fix the bug related to permission
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]

CMD ["monitoring", "-c", "config.yaml"]
