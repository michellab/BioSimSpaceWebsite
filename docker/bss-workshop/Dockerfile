# Workshop image that builds on the biosimspace docker image

# start from the BioSimSpace image
FROM chryswoods/biosimspace-base:latest

USER root

ENV GROMACSHOME=/home/gromacs \
    BSS_SKIP_INSTALL=1

# Install all OS dependencies for workshop server
RUN apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq gcc \
 && apt-get install -yq openbabel \
 && apt-get install -yq g++ \
 && apt-get install -yq dssp \
 && apt-get install -yq --no-install-recommends \
    vim-tiny \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Add in an edited version of the gromacs water models so
# that these can be read in correctly by BioSimSpace
add growat.tar.bz2 /home/gromacs/share/topology/

WORKDIR /home

# Create the workshops directory and make sure it is owned by the user
RUN mkdir /home/workshops && \
    chown -R $NB_USER:$NB_GID /home/workshops

# Switch to the user so we can pull in the workshops
USER $NB_USER

# Install pyPcazip / MDPlus - USED FOR CHARLIES WORKSHOP
RUN conda install numpy cython h5py && \
    pip install pyPcazip && \
    pip install scikit-image && \
    conda clean -tipsy && \
    rm -rf $HOME/.cache $HOME/.jupyter $HOME/.local/share/jupyter

# Patch the netcdf writer in scipy
RUN wget https://raw.githubusercontent.com/scipy/scipy/master/scipy/io/netcdf.py -O /opt/conda/lib/python3.6/site-packages/scipy/io/netcdf.py

# Now git clone in all workshops we wish to use...
WORKDIR /home/workshops

RUN git clone https://github.com/ccpbiosim/python_and_data
RUN git clone https://github.com/ccpbiosim/biosimspace_workshop

RUN git clone https://github.com/ccpbiosim/md_workshop

# switch back to the home directory
WORKDIR $HOME

# Link all of the directories into the home directory.
# We do this, as some JupyterHubs will wipe the home 
# directory, so need to install workshop files elsewhere.
# However, we need to remove anything that is currently
# in home (e.g. a link to biosimspace)
RUN rm * && ln -s /home/workshops/* .

# Add a file into the path that allows the user to update
# BioSimSpace and all workshops very easily
COPY update_workshops /opt/conda/bin/
COPY update_biosimspace /opt/conda/bin/

# Last minute configuration changes for jupyter
USER root

COPY jupyter_notebook_config.py /etc/jupyter/
RUN fix-permissions /etc/jupyter/

USER $NB_USER

WORKDIR $HOME
USER $NB_USER

# Final update of the workshops
RUN update_workshops

# Ensure that the container runs as $NB_USER
USER $NB_USER
