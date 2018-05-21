FROM alpine:3.7

RUN apk add --no-cache python3 git gcc gfortran python3-dev build-base openblas-dev docker \
 && python3 -m ensurepip \
 && rm -r /usr/lib/python*/ensurepip \
 && pip3 install --no-cache --upgrade pip==9.0.3 setuptools \
 && if [[ ! -e /usr/bin/pip ]]; then ln -s pip3 /usr/bin/pip ; fi \
 && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi

WORKDIR /tmp/bugzoo
COPY setup.py .
COPY test/ test/
COPY bugzoo/ bugzoo/
RUN pip install . --no-cache \
 && rm -rf /tmp/*

ENTRYPOINT ["bugzood"]
CMD ["-p", "6060", "--log-file", "/var/log/bugzoo/bugzood.log"]
