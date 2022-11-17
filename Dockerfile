FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.9

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        git \
        cmake \
        tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces

COPY requirements_test.txt ./
COPY requirements_component.txt ./
RUN pip3 install -r requirements_test.txt --use-deprecated=legacy-resolver
RUN pip3 install -r requirements_component.txt --use-deprecated=legacy-resolver
RUN rm -rf requirements_test.txt requirements_component.txt

# Set the default shell to bash instead of sh
ENV SHELL /bin/bash
