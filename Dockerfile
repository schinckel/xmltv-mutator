FROM python:3.9-alpine AS base

MAINTAINER Matthew Schinckel <matt@schinckel.net>


# FROM base AS builder

RUN apk add --update --no-cache \
        python3-dev \
        g++ \
        libxml2 \
        libxml2-dev \
        libxslt-dev

# RUN mkdir /install
# WORKDIR /install

ADD requirements.txt /

# RUN pip install --prefix=/install --no-warn-script-location -r /requirements.txt

RUN pip install --no-warn-script-location -r /requirements.txt
# FROM base
#
# COPY --from=builder /install /usr/local

EXPOSE 4000
# ADD templates /templates/
# ADD static /static/
ADD app.py /
ADD VERSION /

CMD ["hypercorn", "app:app", "-b", "0.0.0.0:4000"]