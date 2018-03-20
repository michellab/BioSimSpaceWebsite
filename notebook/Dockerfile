# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Ubuntu 16.04 (xenial) from 2017-07-23
# https://github.com/docker-library/official-images/commit/0ea9b38b835ffb656c497783321632ec7f87b60c
FROM ubuntu@sha256:84c334414e2bfdcae99509a6add166bbb4fa4041dc3fa6af08046a66fed3005f

LABEL maintainer="Jupyter Project <jupyter@googlegroups.com>"

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
    fonts-liberation \
    libgfortran3 \
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
    SHELL=/bin/bash \
    AMBERHOME=/home/amber/amber16 \
    NB_USER=jovyan \
    NB_UID=1000 \
    NB_GID=100 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8
ENV PATH=$CONDA_DIR/bin:$AMBERHOME/bin:$PATH \
    HOME=/home/$NB_USER

ADD fix-permissions /usr/local/bin/fix-permissions

# Create jovyan user with UID=1000 and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    fix-permissions $HOME

ADD sire.run /tmp

# Install sire to CONDA_DIR
RUN ls -l /tmp && \
    cd /tmp && \
    echo "$CONDA_DIR" | /bin/sh ./tmp_sire.app/pkgs/sire-*/share/Sire/build/install_sire.sh && \
    ls -l /tmp && \
    ls -l $CONDA_DIR

# Change ownership of these files to jovyan user
RUN chown -R $NB_USER:$NB_GID $CONDA_DIR && \
    fix-permissions $CONDA_DIR && \
    ls -l $CONDA_DIR

USER $NB_USER

# Setup work directory for backward-compatibility
RUN mkdir /home/$NB_USER/work && \
    fix-permissions /home/$NB_USER

RUN ls -l $CONDA_DIR
RUN ls -l /tmp

# Configure the notebook and conda as jovyon
RUN $CONDA_DIR/bin/conda config --system --prepend channels conda-forge
RUN $CONDA_DIR/bin/conda config --system --set auto_update_conda false
RUN $CONDA_DIR/bin/conda config --system --set show_channel_urls true
RUN conda clean -tipsy && \
    fix-permissions $CONDA_DIR

# Install Jupyter Notebook and Hub
RUN conda install --quiet --yes \
    'notebook=5.2.*' \
    'jupyterhub=0.8.*' \
    'jupyterlab=0.31.*'

RUN pip install --upgrade pip
RUN pip install pygtail
RUN pip install matplotlib
RUN conda install watchdog

# Now clean up after conda
RUN conda clean -tipsy && \
    jupyter labextension install @jupyterlab/hub-extension@^0.8.0 && \
    npm cache clean && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    fix-permissions $CONDA_DIR

RUN pip --no-cache-dir install nglview
RUN jupyter-nbextension enable nglview --py --sys-prefix

USER root

EXPOSE 8888
WORKDIR $HOME

# Configure container startup
ENTRYPOINT ["tini", "--"]
CMD ["start-notebook.sh"]

# Add local files as late as possible to avoid cache busting
COPY start.sh /usr/local/bin/
COPY start-notebook.sh /usr/local/bin/
COPY start-singleuser.sh /usr/local/bin/
COPY jupyter_notebook_config.py /etc/jupyter/
RUN fix-permissions /etc/jupyter/

# Add biosimspace files
ADD biosimspace.tar.bz2 /home/
RUN chown -R $NB_USER:$NB_GID /home/biosimspace

# Switch back to jovyan to avoid accidental container runs as root
USER $NB_USER

# install biosimspace
RUN cd /home/biosimspace/python && \
    python setup.py install

RUN /home/biosimspace/demo/nglview_patch.sh /opt/conda

# install ambertools into /home/amber
ADD amber.tar.bz2 /home/amber
