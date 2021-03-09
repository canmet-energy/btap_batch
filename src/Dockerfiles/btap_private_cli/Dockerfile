ARG OPENSTUDIO_VERSION='3.0.1'
FROM canmet/docker-openstudio:$OPENSTUDIO_VERSION
# Need to remind Docker of the Openstudio version..https://docs.docker.com/engine/reference/builder/
ARG OPENSTUDIO_VERSION
# Branch information.
ARG BTAP_COSTING_BRANCH='master'
ARG OS_STANDARDS_BRANCH='nrcan'
# Git api token secret. Do not share as a ENV.
ARG GIT_API_TOKEN='nothing'
MAINTAINER Phylroy Lopez phylroy.lopez@canada.ca
# Set X session url..if needed.
ARG DISPLAY=host.docker.internal
ENV DISPLAY ${DISPLAY}

# Set Ruby lib to use the version of OS.
ENV RUBYLIB=/usr/local/openstudio-${OPENSTUDIO_VERSION}/Ruby:/usr/Ruby

#Be root and install btap_costing under the root folder.
USER  root
WORKDIR /
# Clone a shallow copy of btap_costing with selected branch.
RUN git clone https://$GIT_API_TOKEN:x-oauth-basic@github.com/canmet-energy/btap_costing.git --depth 1 --branch ${BTAP_COSTING_BRANCH} --single-branch /btap_costing
WORKDIR /btap_costing
# Set standards branch
RUN sed -i '/^.*standards.*$/d' Gemfile
RUN echo "gem 'openstudio-standards', :github => 'NREL/openstudio-standards', :branch => '${OS_STANDARDS_BRANCH}'" | tee -a Gemfile

#Run bundle update openstudio-standards
RUN bundle install

# Show which version of btap_costing is being used.
RUN echo 'btap_costing revision'
RUN git rev-parse --short HEAD

# Make folders that will map to host drives.
WORKDIR /btap_costing/utilities/btap_cli
RUN mkdir output
RUN mkdir input
CMD ["/bin/bash"]