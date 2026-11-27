ARG OPENSTUDIO_VERSION='3.11.0'
FROM canmet/os_sdk_container:$OPENSTUDIO_VERSION

ARG RSMEANS_YEAR=''
ARG OS_STANDARDS_BRANCH='nrcan'
ARG WEATHER_FILES=''
ARG LOCAL_COSTING_PATH=''
ARG LOCAL_FACTORS_PATH=''
ARG LOCAL_CARBON_OPAQUE_PATH=''
ARG LOCAL_CARBON_GLAZING_PATH=''
ARG LOCAL_CARBON_FRAME_PATH=''

ARG OS_STANDARDS_ORG='NatLabRockies'

LABEL author="Phylroy Lopez phylroy.lopez@canada.ca, Chris Kirney chris.kirney@nrcan-rncan.gc.ca, Nicholas Pneumaticos nicholas.pneumaticos@nrcan-rncan.gc.ca"

# Install openstudio-standards under the root folder.
WORKDIR /

# Clone openstudio-standards into the container
RUN echo "Creating Public CLI" \
    && git clone https://github.com/${OS_STANDARDS_ORG}/openstudio-standards.git --depth 1 --branch ${OS_STANDARDS_BRANCH} --single-branch /openstudio-standards \
    && cd /openstudio-standards \
    && bundle install \
    && echo 'standards revision' \
    && git rev-parse --short HEAD;

WORKDIR /

# Copy the local database files using the * wildcard which copies the file and 
# doesn't throw an error if the file does not exist
COPY $LOCAL_COSTING_PATH* /openstudio-standards/lib/openstudio-standards/btap/common/costs.csv
COPY $LOCAL_FACTORS_PATH* /openstudio-standards/lib/openstudio-standards/btap/common/costs_local_factors.csv
COPY $LOCAL_CARBON_OPAQUE_PATH* /openstudio-standards/lib/openstudio-standards/btap/common/carbon_opaque.csv
COPY $LOCAL_CARBON_GLAZING_PATH* /openstudio-standards/lib/openstudio-standards/btap/common/carbon_glazing.csv
COPY $LOCAL_CARBON_FRAME_PATH* /openstudio-standards/lib/openstudio-standards/btap/common/carbon_frame.csv

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


