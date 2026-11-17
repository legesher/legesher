# A container image for the legesher-mcp server: the published package from
# PyPI in its own virtual environment, on Python 3.13.
#
# Glama (glama.ai/mcp/servers/legesher/legesher) builds the server into a
# container before it lists it, from build settings saved on the listing. This
# file runs those build steps on a pinned base, so the build can be reproduced
# and checked on a laptop before the settings change there.
# docs/registry-listings.md, "Glama", has the settings and the check;
# tests/test_container_image.py holds this file to what it says here, and
# `make test-mcp-docker` builds it and drives a session.
#
# The file needs no build context:
#
#   docker build -t legesher-mcp - < libs/mcp/Dockerfile
#
# What the build downloads, and how each is fixed:
#   - the base image and the uv image, by digest;
#   - Python, mcp-proxy and legesher-mcp, by exact version;
#   - the packages mcp-proxy and legesher-mcp depend on, by date: both
#     installs take only releases published before the start of
#     RESOLVED_BEFORE (UTC), so the same file resolves the same set on any
#     later day, unless one of those releases is later yanked or removed.
#
# By default the container runs the server over stdio, the way a desktop
# client starts it:
#
#   docker run --interactive --rm legesher-mcp
#
# The listing's command puts mcp-proxy in front, which serves the same server
# over HTTP on port 8080. mcp-proxy listens on every interface, asks for no
# credentials and answers any origin, which suits a directory's sandbox and
# nothing wider. Publish the port on loopback only:
#
#   docker run --rm --publish 127.0.0.1:8080:8080 legesher-mcp \
#       mcp-proxy -- /opt/legesher-mcp/bin/legesher-mcp

# Debian 13 (trixie) slim with Node.js, which mcp-proxy runs on.
FROM node:24.22.3-trixie-slim@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0

# uv, copied from its own image; it installs Python and the server.
COPY --from=ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 /uv /uvx /usr/local/bin/

# Dependencies resolve as the indexes stood at the start of this day (UTC).
# It has to be later than the day the pinned legesher-mcp was published, and
# no later than the day of the change.
ARG RESOLVED_BEFORE=2026-11-10
ARG PYTHON_VERSION=3.13.18
ARG MCP_PROXY_VERSION=6.10.0

ENV UV_PYTHON=${PYTHON_VERSION} \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_NO_CACHE=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

RUN npm install --global --before="${RESOLVED_BEFORE}" "mcp-proxy@${MCP_PROXY_VERSION}" \
    && npm cache clean --force \
    && uv python install "${PYTHON_VERSION}"

# The newest legesher-mcp on PyPI. Raise it after each publish, never before:
# a version that is not on the index yet cannot be installed.
ARG LEGESHER_MCP_VERSION=0.3.0

# The listing's two build steps, with the version and the date named.
RUN uv venv /opt/legesher-mcp \
    && uv pip install --python /opt/legesher-mcp/bin/python --exclude-newer "${RESOLVED_BEFORE}T00:00:00Z" "legesher-mcp==${LEGESHER_MCP_VERSION}"

# The server reads nothing outside its own install and keeps no state, so it
# needs no privileges.
USER node
WORKDIR /home/node

CMD ["/opt/legesher-mcp/bin/legesher-mcp"]
