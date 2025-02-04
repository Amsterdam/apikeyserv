FROM python:3.12-slim-bullseye AS builder
MAINTAINER datapunt@amsterdam.nl

RUN set -e \
    && sed -i 's+http://archive+http://azure.archive+g' /etc/apt/sources.list \
    && apt -y update --allow-releaseinfo-change \
    && apt install -y gcc libffi-dev python3-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Start runtime image.
FROM python:3.12-slim-bullseye

RUN useradd -M -U datapunt

RUN set -e \
    && sed -i 's+http://archive+http://azure.archive+g' /etc/apt/sources.list \
    && apt -y update --allow-releaseinfo-change \
    && apt -y upgrade

# Install libexpat1 for uwsgi
RUN apt -y install libexpat1

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

RUN mkdir /static && chown datapunt:datapunt /static
WORKDIR /app
COPY . ./

ENV DJANGO_SETTINGS_MODULE=apikeyserv.settings

RUN python manage.py collectstatic --noinput

EXPOSE 8000
USER datapunt
CMD ["uwsgi"]
