FROM public.ecr.aws/ubuntu/ubuntu:24.04
ARG BTAP_BATCH_BRANCH

ENV BTAP_BATCH_BRANCH=$BTAP_BATCH_BRANCH

# Install BTAP Batch, python, git, and network related packages.
RUN apt-get -y update
RUN apt-get install -y python3-pip python3-venv git ca-certificates curl wget
RUN echo "Cloning btap_batch"
RUN git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/btap_batch.git --depth 1 --branch ${BTAP_BATCH_BRANCH} --single-branch /btap_batch
RUN cd /btap_batch && echo 'btap_batch revision' && git rev-parse --short HEAD
RUN python3 -m venv /btap_batch/venv
RUN /btap_batch/venv/bin/pip install -r /btap_batch/requirements.txt

# Install Docker-related packages by retrieving and signing the appropriate
# package list.
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

CMD ["/bin/bash"]

# Sample invocation commands
# aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin 834599497928.dkr.ecr.ca-central-1.amazonaws.com
# docker build -t --no-cache --build-arg GIT_API_TOKEN=$GIT_API_TOKEN --build-arg BUILD_ENV_NAME=$BUILD_ENV_NAME --build-arg  BTAP_BATCH_BRANCH=$BTAP_BATCH_BRANCH .
# Test locally.
# docker run -it --rm -v "//var/run/docker.sock:/var/run/docker.sock" -v "//c/Users/plopez/.aws:/root/.aws"  btap_batch /bin/bash

# docker run -it --rm -v "//var/run/docker.sock:/var/run/docker.sock" -v "//c/Users/plopez/.aws:/root/.aws"  834599497928.dkr.ecr.ca-central-1.amazonaws.com/phylroy_lopez_btap_batch  /bin/bash



