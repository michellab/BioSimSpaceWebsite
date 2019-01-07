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

# Variables holding links to download dependencies
ENV SIRE_DOWNLOAD=https://objectstorage.eu-frankfurt-1.oraclecloud.com/p/kAWkIxg3dh6eJ-_pC1kdTYY0vAAleqDQ3h5pEAA2eRQ/n/chryswoods/b/downloads/o/sire_2018_2_0_linux.run

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

# Install Sire, which provides conda
RUN wget $SIRE_DOWNLOAD sire.run && \
    chmod a+x sire.run && \
    echo "/opt/conda" | ./sire.run && \
    chown -R $NB_USER:$NB_GID /opt/conda && \
    fix-permissions /opt/conda && \
    rm sire.run

# Install biosimspace into /home using git
WORKDIR /home
RUN git clone https://github.com/michellab/biosimspace && \
    chown -R $NB_USER:$NB_GID /home/biosimspace && \
    fix-permissions /home/biosimspace

# Download and install amber16 into /home using wget
RUN wget https://biosimspace.blob.core.windows.net/dependencies/amber16.tar.bz2 -O amber16.tar.bz2 && \
    tar -jxvf amber16.tar.bz2 && \
    rm amber16.tar.bz2

# Download and install gromacs into /home using wget
RUN wget https://biosimspace.blob.core.windows.net/dependencies/gromacs.tar.bz2 -O gromacs.tar.bz2 && \
    tar -jxvf gromacs.tar.bz2 && \
    rm gromacs.tar.bz2

# Configure container startup
ENTRYPOINT ["tini", "--"]
CMD ["start-notebook.sh"]
EXPOSE 8888

COPY start.sh /usr/local/bin/
COPY start-notebook.sh /usr/local/bin/
COPY start-singleuser.sh /usr/local/bin/
COPY jupyter_notebook_config.py /etc/jupyter/
RUN fix-permissions /etc/jupyter/

# Do all conda work as $NB_USER
USER $NB_USER
WORKDIR $HOME

# Install Jupyter Notebook and Hub and other useful packages
RUN conda config --system --prepend channels conda-forge && \
    conda config --system --set auto_update_conda false && \
    conda config --system --set show_channel_urls true && \
    conda install --quiet --yes 'notebook=5.2.*' 'jupyterhub=0.8.*' 'jupyterlab=0.31.*'
RUN conda install watchdog
RUN pip install --upgrade pip && \
    pip install pygtail && \
    pip install matplotlib && \
    pip install jupyterhub-tmpauthenticator

RUN conda config --add channels conda-forge && \
    conda install mdanalysis
RUN conda install -c omnia mdtraj
RUN conda install -c omnia pymbar

# Install and enable nglview (including patching some issues) and fileupload
COPY nglview_patch.sh $HOME
RUN pip --no-cache-dir install nglview && \
    jupyter-nbextension install nglview --py --sys-prefix && \
    jupyter-nbextension enable nglview --py --sys-prefix && \
    $HOME/nglview_patch.sh /opt/conda && \
    rm $HOME/nglview_patch.sh && \
    pip install fileupload && \
    jupyter-nbextension install fileupload --py --sys-prefix && \
    jupyter-nbextension enable fileupload --py --sys-prefix

# Install BioSimSpace (updating to the latest version here to
# limit cache busting)
RUN cd /home/biosimspace/python && \
    git pull && \
    python setup.py install

# Reinstall an older version of tornado as tornado 5 
# and clean up after conda, including clearing the cache
RUN conda install tornado=4.5.3 && \
    conda clean -tipsy && \
    npm cache clean --force && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    fix-permissions $CONDA_DIR && \
    rm -rf $HOME/.cache $HOME/.jupyter $HOME/.local/share/jupyter

# Link the BioSimSpace directory into $HOME so that we can access
# this from the notebook
RUN ln -s /home/biosimspace $HOME/

# End as the User to make sure that we don't
# accidentally run the container as root
USER $NB_USER
