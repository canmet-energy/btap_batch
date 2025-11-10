FROM public.ecr.aws/ubuntu/ubuntu:22.04
ARG BTAP_BATCH_BRANCH
ARG GIT_API_TOKEN
ARG BUILD_ENV_NAME

ENV BUILD_ENV_NAME=$BUILD_ENV_NAME
ENV GIT_API_TOKEN=$GIT_API_TOKEN
ENV BTAP_BATCH_BRANCH=$BTAP_BATCH_BRANCH
ENV PYTHONPATH=/btap_batch

RUN apt-get -y update
#RUN apt-get install -y python3.9
RUN apt-get install -y python3-pip
RUN apt-get install -y git
RUN echo "Cloning btap_batch"
RUN git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/btap_batch.git --depth 1 --branch ${BTAP_BATCH_BRANCH} --single-branch /btap_batch
RUN cd /btap_batch && echo 'btap_batch revision' && git rev-parse --short HEAD
RUN cd /btap_batch && pip install --upgrade pip
RUN cd /btap_batch && pip install -r requirements.txt
#RUN apt-get -y install docker
#RUN apt-get -y install ./docker-desktop-amd64.deb
# Install Docker
# Add Docker's official GPG key:
RUN apt-get update
RUN apt-get -y install ca-certificates curl
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
RUN chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
RUN apt-get -y install nano
RUN apt-get -y install wget
RUN apt-get -y install chromium-browser
#Install Chromium for Python charts.
#RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
#RUN apt-get -y install ./google-chrome-stable_current_x86_64.rpm
RUN ln -s /usr/bin/chromium-browser /usr/bin/chromium
# Alternate install chrome driver
#RUN wget https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip
#RUN unzip chromedriver_linux64.zip
#RUN mv chromedriver /usr/bin/chromedriverchromedriver --version


CMD ["/bin/bash"]

#Sample invocation commands
# aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin 834599497928.dkr.ecr.ca-central-1.amazonaws.com
# docker build -t --no-cache --build-arg GIT_API_TOKEN=$GIT_API_TOKEN --build-arg BUILD_ENV_NAME=$BUILD_ENV_NAME --build-arg  BTAP_BATCH_BRANCH=$BTAP_BATCH_BRANCH .
# Test locally.
# docker run -it --rm -v "//var/run/docker.sock:/var/run/docker.sock" -v "//c/Users/plopez/.aws:/root/.aws"  btap_batch /bin/bash
# PYTHONPATH=/btap_batch python3 /btap_batch/examples/optimization/new_run.py

#docker run -it --rm -v "//var/run/docker.sock:/var/run/docker.sock" -v "//c/Users/plopez/.aws:/root/.aws"  834599497928.dkr.ecr.ca-central-1.amazonaws.com/phylroy_lopez_btap_batch  /bin/bash



