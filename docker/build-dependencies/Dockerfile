# Based on the JupyterHub docker image that is
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
# Ubuntu 16.04 (xenial) from 2017-07-23
# https://github.com/docker-library/official-images/commit/0ea9b38b835ffb656c497783321632ec7f87b60c

# Changes made for the BioSimSpace project (https://biosimspace.org), and
# are (c) the BioSimSpace development team, distributed under
# the same license as the original JupyterHub docker file, i.e.
# the Modified BSD License.

# Any errors or problems are the fault of the BioSimSpace team and nothing
# to do with JupyterHub

# Start from ubuntu :-)
FROM ubuntu@sha256:84c334414e2bfdcae99509a6add166bbb4fa4041dc3fa6af08046a66fed3005f

LABEL maintainer="Christopher Woods <Christopher.Woods@bristol.ac.uk>"

USER root

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq --no-install-recommends \
    wget \
    bzip2 \
    ca-certificates \
    sudo \
    locales \
    git \
    bc \
    less \
    nano \
    libgfortran3 \
    fonts-liberation \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Install Tini
RUN wget --quiet https://github.com/krallin/tini/releases/download/v0.10.0/tini && \
    echo "1361527f39190a7338a0b434bd8c88ff7233ce7b9a4876f3315c22fce7eca1b0 *tini" | sha256sum -c - && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

# Configure environment
ENV CONDA_DIR=/opt/conda \
    SIRE_SILENT_PHONEHOME=1 \
    SIRE=/opt/conda \
    AMBERHOME=/home/amber16 \
    SHELL=/bin/bash \
    NB_USER=jovyan \
    NB_UID=1000 \
    NB_GID=100 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8

ENV PATH=$CONDA_DIR/bin:$PATH \
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$AMBERHOME/lib64 \
    HOME=/home/$NB_USER

ADD fix-permissions /usr/local/bin/fix-permissions

# Create jovyan user with UID=1000 and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    fix-permissions $HOME

USER root
WORKDIR $HOME

CMD ["/bin/bash"]
