FROM python:3.11-slim-bullseye AS builder
MAINTAINER datapunt@amsterdam.nl

RUN apt -y update && apt install -y gcc libffi-dev python3-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Start runtime image.
FROM python:3.11-slim-bullseye

RUN useradd -M -U datapunt

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

RUN mkdir /static && chown datapunt:datapunt /static
WORKDIR /app
COPY . ./

ENV DJANGO_SETTINGS_MODULE=apikeyserv.settings

RUN python manage.py collectstatic --noinput

EXPOSE 8000
USER datapunt
CMD ["uwsgi"]
