FROM public.ecr.aws/amazonlinux/amazonlinux:2022
ARG BTAP_BATCH_BRANCH
ARG GIT_API_TOKEN
ARG BUILD_ENV_NAME

ENV BUILD_ENV_NAME=$BUILD_ENV_NAME
ENV GIT_API_TOKEN=$GIT_API_TOKEN
ENV BTAP_BATCH_BRANCH=$BTAP_BATCH_BRANCH
ENV PYTHONPATH=/btap_batch


RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN yum -y install python39
RUN python3 get-pip.py --user
RUN yum -y install git
RUN echo "Cloning btap_batch"
RUN git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/btap_batch.git --depth 1 --branch ${BTAP_BATCH_BRANCH} --single-branch /btap_batch
RUN cd /btap_batch && echo 'btap_batch revision' && git rev-parse --short HEAD
RUN cd /btap_batch && /root/.local/bin/pip install -r requirements.txt
RUN yum -y update
RUN yum -y install docker
RUN yum -y install nano
RUN yum -y install wget
#Install Chromium for Python charts.
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
RUN yum -y install ./google-chrome-stable_current_x86_64.rpm
RUN ln -s /usr/bin/google-chrome-stable /usr/bin/chromium
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



