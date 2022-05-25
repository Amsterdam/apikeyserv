FROM amsterdam/python:3.9-buster AS builder
MAINTAINER datapunt@amsterdam.nl

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Start runtime image.
FROM amsterdam/python:3.9-slim-buster

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/

WORKDIR /app
COPY . ./
RUN python manage.py makemigrations apikeys && python manage.py migrate

ENV DJANGO_SETTINGS_MODULE=apikeyserv.settings

EXPOSE 8000
USER datapunt
CMD ["uwsgi"]
