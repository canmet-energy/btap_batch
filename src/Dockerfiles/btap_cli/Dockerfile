ARG OPENSTUDIO_VERSION='3.9.0'
FROM canmet/os_sdk_container:$OPENSTUDIO_VERSION

ARG ENABLE_RSMEANS=''
ARG RSMEANS_YEAR=''
ARG ENABLE_PROPRIETARY_CARBON=''
ARG OS_STANDARDS_BRANCH='nrcan'
ARG WEATHER_FILES=''
ARG LOCALNRCAN=''
ARG LOCALNRCAN_BRANCH='ruby_3.2'
ARG LOCAL_COSTING_PATH=''
ARG LOCAL_FACTORS_PATH=''
ARG LOCAL_CARBON_OPAQUE_PATH=''
ARG LOCAL_CARBON_GLAZING_PATH=''
ARG LOCAL_CARBON_FRAME_PATH=''

ARG GIT_API_TOKEN='nothing'
ARG OS_STANDARDS_ORG='NREL'

LABEL author="Phylroy Lopez phylroy.lopez@canada.ca, Chris Kirney chris.kirney@nrcan-rncan.gc.ca, Nicholas Pneumaticos nicholas.pneumaticos@nrcan-rncan.gc.ca"

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

WORKDIR /

# Copy the local database files using the * wildcard which copies the file and 
# doesn't throw an error if the file does not exist
COPY $LOCAL_COSTING_PATH* /openstudio-standards/lib/openstudio-standards/btap/common_resources/costs.csv
COPY $LOCAL_FACTORS_PATH* /openstudio-standards/lib/openstudio-standards/btap/common_resources/costs_local_factors.csv
COPY $LOCAL_CARBON_OPAQUE_PATH* /openstudio-standards/lib/openstudio-standards/btap/common_resources/carbon_opaque.csv
COPY $LOCAL_CARBON_GLAZING_PATH* /openstudio-standards/lib/openstudio-standards/btap/common_resources/carbon_glazing.csv
COPY $LOCAL_CARBON_FRAME_PATH* /openstudio-standards/lib/openstudio-standards/btap/common_resources/carbon_frame.csv

RUN if [ -n "$ENABLE_RSMEANS" ] ; then \
        echo "Overwriting placeholder costing data with RSMeans data (ENABLE_RSMEANS=$ENABLE_RSMEANS)" \
        && curl -v https://$GIT_API_TOKEN:x-oauth-basic@raw.githubusercontent.com/canmet-energy/btap_costing_data_generation/refs/heads/main/resources/rsmeans_factors.csv \
            -o /openstudio-standards/lib/openstudio-standards/btap/common_resources/costs_local_factors.csv \
        && curl -v https://$GIT_API_TOKEN:x-oauth-basic@raw.githubusercontent.com/canmet-energy/btap_costing_data_generation/refs/heads/main/output/costing/$RSMEANS_YEAR/costs_rsmeans.csv \
            -o /openstudio-standards/lib/openstudio-standards/btap/common_resources/costs.csv; \
    fi

RUN if [ -n "$ENABLE_PROPRIETARY_CARBON" ] ; then \
        echo "Overwriting placeholder costing data with RSMeans data (ENABLE_PROPRIETARY_CARBON=$ENABLE_PROPRIETARY_CARBON)" \
        && curl -v https://$GIT_API_TOKEN:x-oauth-basic@raw.githubusercontent.com/canmet-energy/btap_costing_data_generation/refs/heads/main/resources/carbon_opaque_proprietary.csv \
            -o /openstudio-standards/lib/openstudio-standards/btap/common_resources/carbon_opaque.csv \
        && curl -v https://$GIT_API_TOKEN:x-oauth-basic@raw.githubusercontent.com/canmet-energy/btap_costing_data_generation/refs/heads/main/resources/carbon_glazing_proprietary.csv \
            -o /openstudio-standards/lib/openstudio-standards/btap/common_resources/carbon_glazing.csv \
        && curl -v https://$GIT_API_TOKEN:x-oauth-basic@raw.githubusercontent.com/canmet-energy/btap_costing_data_generation/refs/heads/main/resources/carbon_frame_proprietary.csv \
            -o /openstudio-standards/lib/openstudio-standards/btap/common_resources/carbon_frame.csv; \
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


