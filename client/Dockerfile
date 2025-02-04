FROM python:3.12-slim-bullseye AS builder
MAINTAINER datapunt@amsterdam.nl

RUN set -e \
    && sed -i 's+http://archive+http://azure.archive+g' /etc/apt/sources.list \
    && apt -y update && apt install -y git

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Start runtime image.
FROM python:3.12-slim-bullseye

RUN useradd -M -U datapunt

RUN set -e \
    && sed -i 's+http://archive+http://azure.archive+g' /etc/apt/sources.list \
    && apt -y update \
    && apt -y upgrade \
    && apt install -y netcat-openbsd

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

WORKDIR /app
COPY . ./

EXPOSE 8000
USER datapunt
CMD ["python", "__init__.py", "runserver", "0.0.0.0:8000"]
