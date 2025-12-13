#!/bin/bash
set -e
./scripts/build.sh
docker compose up -d ${1:---profile gpu}
docker compose logs -f
