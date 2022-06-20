#!/bin/bash
# user configuration for local development
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER apikeyserv WITH PASSWORD 'insecure';
	CREATE DATABASE apikeyserv;
	GRANT ALL PRIVILEGES ON DATABASE apikeyserv TO apikeyserv;
EOSQL