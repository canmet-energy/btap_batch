ARG OPENSTUDIO_VERSION='3.6.1'
FROM canmet/docker-openstudio:$OPENSTUDIO_VERSION
# Need to remind Docker of the Openstudio version..https://docs.docker.com/engine/reference/builder/
ARG OPENSTUDIO_VERSION
# Branch information.
ARG BTAP_COSTING_BRANCH=''
ARG OS_STANDARDS_BRANCH='nrcan'
ARG WEATHER_FILES=''
ARG LOCALNRCAN=''
ARG LOCALNRCAN_BRANCH='main'


# Git api token secret. Do not share as a ENV.
ARG GIT_API_TOKEN='nothing'
MAINTAINER Phylroy Lopez phylroy.lopez@canada.ca
# Set X session url..if needed.
ARG DISPLAY=host.docker.internal
ENV DISPLAY ${DISPLAY}

# Set Ruby lib to use the version of OS.
ENV RUBYLIB=/usr/local/openstudio-${OPENSTUDIO_VERSION}/Ruby:/usr/Ruby
USER  root

#Be root and install nrcan_certs under the root folder if LOCALNRCAN is set.
WORKDIR /
RUN if [ ! -z "$LOCALNRCAN" ] ; then \
      echo "Cloning install_nrcan_certs repository" \
      && git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/linux_nrcan_certs.git --depth 1 --branch ${LOCALNRCAN_BRANCH} --single-branch /linux_nrcan_certs \
      && cd /linux_nrcan_certs \
      && ./install_nrcan_certs.sh \
      && git rev-parse --short HEAD;\
    fi

#Be root and install btap_costing under the root folder.
WORKDIR /

# if costing branch name is undefined.. do not use costing.
RUN if [ -z "$BTAP_COSTING_BRANCH" ] ; then \
        echo "Creating Public CLI witout costing" \
        && git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/NREL/openstudio-standards.git --depth 1 --branch ${OS_STANDARDS_BRANCH} --single-branch /btap_costing \
        && cd /btap_costing \
        && bundle install \
        && echo 'standards revision' \
        && git rev-parse --short HEAD;\
    fi

# if costing branch name is defined.. use costing.
RUN if [ ! -z "$BTAP_COSTING_BRANCH" ] ; then \
        echo "Creating Private CLI with Costing" \
        && git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/btap_costing.git --depth 1 --branch ${BTAP_COSTING_BRANCH} --single-branch /btap_costing \
        && cd /btap_costing \
        && sed -i '/^.*standards.*$/d' Gemfile \
        && echo "gem 'openstudio-standards', :github => 'NREL/openstudio-standards', :branch => '${OS_STANDARDS_BRANCH}'" | tee -a Gemfile \
        && bundle install \
        && echo 'standards revision' \
        && git rev-parse --short HEAD;\
    fi

# Make folders that will map to host drives.
WORKDIR /btap_costing/utilities/btap_cli
RUN mkdir output
RUN mkdir input
RUN mkdir weather

# Download non-standard weather files to the weather directory.
WORKDIR /btap_costing/utilities/btap_cli/weather
RUN if [ ! -z "$WEATHER_FILES" ] ; then \
    echo "Downloading weather files." \
    && wget --no-check-certificate $WEATHER_FILES; \
fi
WORKDIR /btap_costing/utilities/btap_cli
CMD ["/bin/bash"]

#Sample invocation commands

