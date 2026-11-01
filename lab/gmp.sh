#!/bin/sh
# Send a GMP XML command to gvmd through the gvm-tools container.
# Usage: GMP_PASSWORD=... ./gmp.sh '<get_version/>'
# The password is read from the environment so it never ends up in the repo.
: "${GMP_PASSWORD:?set GMP_PASSWORD to the gvmd admin password}"
docker compose run --rm -T gvm-tools \
  gvm-cli --gmp-username "${GMP_USERNAME:-admin}" --gmp-password "$GMP_PASSWORD" \
  socket --xml "$1"
