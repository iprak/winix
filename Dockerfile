FROM ghcr.io/iprak/custom-integration-image:main

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /workspaces

COPY requirements_component.txt ./
RUN pip3 install -r requirements_component.txt --use-deprecated=legacy-resolver
RUN rm -rf requirements_component.txt

# Set the default shell to bash instead of sh
ENV SHELL /bin/bash
