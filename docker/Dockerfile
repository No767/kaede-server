FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  bash \
  netcat-traditional \
  tini \
  && apt-get clean

WORKDIR /kaede
COPY /server /kaede/server/
COPY /docker/wait-for /kaede/wait-for
COPY /requirements.txt /kaede/requirements.txt

RUN adduser --disabled-password --gecos "" kaede \
  && chown -R kaede:kaede /kaede \
  && chmod +x /kaede/wait-for

USER kaede

ENV PATH="${PATH}:/home/kaede/.local/bin"

RUN pip install --user -r requirements.txt

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python3," "/kaede/server/launcher.py", "--no-workers"]

STOPSIGNAL SIGTERM