FROM public.ecr.aws/amazonlinux/amazonlinux:2022
ARG BTAP_BATCH_BRANCH
ARG GIT_API_TOKEN
ARG AWS_USERNAME

ENV AWS_USERNAME=$AWS_USERNAME
ENV GIT_API_TOKEN=$GIT_API_TOKEN


RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN yum -y install python39
RUN python3 get-pip.py --user
RUN yum -y install git
RUN echo "Cloning btap_batch"
RUN git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/btap_batch.git --depth 1 --branch ${BTAP_BATCH_BRANCH} --single-branch /btap_batch
RUN cd /btap_batch && echo 'btap_batch revision' && git rev-parse --short HEAD
RUN cd /btap_batch && /root/.local/bin/pip install icecream scikit-learn pymoo==0.6.0 pyyaml boto3 pandas scikit-optimize openstudio==3.2.1 tqdm numpy_financial docker openpyxl podman pip_system_certs
RUN yum -y update
RUN yum -y install docker
RUN yum -y install nano
CMD ["/bin/bash"]

#Sample invocation commands
# docker build -t --no-cache btap_batch .
# Test locally.
# docker run -it --rm -v "//var/run/docker.sock:/var/run/docker.sock" -v "//c/Users/plopez/.aws:/root/.aws"  btap_batch /bin/bash
# PYTHONPATH=/btap_batch python3 new_run.py



