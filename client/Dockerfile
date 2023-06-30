FROM python:3.11-slim-bullseye AS builder
MAINTAINER datapunt@amsterdam.nl

RUN apt -y update && apt install -y git netcat

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Start runtime image.
FROM python:3.11-slim-bullseye

RUN useradd -M -U datapunt

RUN apt -y update && apt -y upgrade

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/bin/ /usr/bin/
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

WORKDIR /app
COPY . ./

EXPOSE 8000
USER datapunt
CMD ["python", "__init__.py", "runserver", "0.0.0.0:8000"]
