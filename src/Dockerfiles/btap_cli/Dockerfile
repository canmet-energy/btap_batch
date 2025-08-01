ARG OPENSTUDIO_VERSION='3.7.0'
FROM canmet/os_sdk_container:$OPENSTUDIO_VERSION

ARG ENABLE_RSMEANS=''
ARG OS_STANDARDS_BRANCH='nrcan'
ARG WEATHER_FILES=''
ARG LOCALNRCAN=''
ARG LOCALNRCAN_BRANCH='main'
ARG LOCAL_COSTING_PATH=''
ARG GIT_API_TOKEN='nothing'
ARG OS_STANDARDS_ORG='NREL'

LABEL author="Phylroy Lopez phylroy.lopez@canada.ca"

#Be root and install nrcan_certs under the root folder if LOCALNRCAN is set.
WORKDIR /
RUN if [ -n "$LOCALNRCAN" ] ; then \
      echo "Cloning install_nrcan_certs repository" \
      && git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/linux_nrcan_certs.git --depth 1 --branch ${LOCALNRCAN_BRANCH} --single-branch /linux_nrcan_certs \
      && cd /linux_nrcan_certs \
      && ./install_nrcan_certs.sh \
      && git rev-parse --short HEAD;\
    fi

# Install openstudio-standards under the root folder.
WORKDIR /

# Clone openstudio-standards into the container
RUN echo "Creating Public CLI" \
    && git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/${OS_STANDARDS_ORG}/openstudio-standards.git --depth 1 --branch ${OS_STANDARDS_BRANCH} --single-branch /openstudio-standards \
    && cd /openstudio-standards \
    && bundle install \
    && echo 'standards revision' \
    && git rev-parse --short HEAD;

RUN if [ -n "$ENABLE_RSMEANS" ]; then \
        echo "Overwriting placeholder costing data with RSMeans data (ENABLE_RSMEANS=$ENABLE_RSMEANS)" \
        && curl -v -s https://$GIT_API_TOKEN:x-oauth-basic@raw.githubusercontent.com/canmet-energy/btap_costing_data_generation/refs/heads/main/resources/rsmeans_factors.csv \
                -o /openstudio-standards/lib/openstudio-standards/btap/costing/common_resources/costs_local_factors.csv \
        && curl -v -s https://$GIT_API_TOKEN:x-oauth-basic@raw.githubusercontent.com/canmet-energy/btap_costing_data_generation/refs/heads/main/output/costs_rsmeans.csv \
                -o /openstudio-standards/lib/openstudio-standards/btap/costing/common_resources/costs.csv; \
fi

RUN if [ -n "$LOCAL_COSTING_PATH" ]; then \
        echo "Using local costing file at $LOCAL_COSTING_PATH" \
        && cp $LOCAL_COSTING_PATH /openstudio-standards/lib/openstudio-standards/btap/costing/costing_database.json; \
    fi

# Make folders that will map to host drives.
WORKDIR /openstudio-standards/utilities/btap_cli
RUN mkdir output
RUN mkdir input
RUN mkdir weather

# Download non-standard weather files to the weather directory.
WORKDIR /openstudio-standards/utilities/btap_cli/weather
RUN if [ -n "$WEATHER_FILES" ] ; then \
    echo "Downloading weather files." \
    && wget --no-check-certificate $WEATHER_FILES; \
fi
WORKDIR /openstudio-standards/utilities/btap_cli
CMD ["/bin/bash"]


