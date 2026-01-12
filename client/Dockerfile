FROM python:3.14-slim-trixie AS builder
MAINTAINER datapunt@amsterdam.nl

RUN apt -y update && apt install -y git

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Start runtime image.
FROM python:3.14-slim-trixie

RUN useradd -M -U datapunt

RUN apt -y update && apt -y upgrade && apt install -y netcat-openbsd

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/

WORKDIR /app
COPY . ./

EXPOSE 8000
USER datapunt
CMD ["python", "__init__.py", "runserver", "0.0.0.0:8000"]
