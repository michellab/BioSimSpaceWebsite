# Workshop image that builds on the biosimspace docker image

# start from the BioSimSpace image
FROM chryswoods/biosimspace-base:latest

USER root

# Install all OS dependencies for workshop server
RUN apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq gcc \
 && apt-get install -yq --no-install-recommends \
    vim-tiny \
    python \
    python-numpy \
    python-matplotlib \
    python-scipy \
    libpython2.7 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /home

# Download and install FESetup, and change ownership to the user
RUN wget https://biosimspace.blob.core.windows.net/dependencies/FESetup1.2.1_Linux.sh -O FESetup1.2.1_Linux.sh && \
    chmod a+x FESetup1.2.1_Linux.sh && \
    ./FESetup1.2.1_Linux.sh --python /usr/bin/python2.7 --amber "_default" --gromacs "_none" --namd "_none" --dlpoly "_none" && \
    rm FESetup1.2.1_Linux.sh && \
    chown -R $NB_USER:$NB_GID /home/FESetup1.2.1 && \
    fix-permissions /home/FESetup1.2.1

# Dowload and install wham
RUN wget https://biosimspace.blob.core.windows.net/dependencies/wham.tar.bz2 -O wham.tar.bz2 && \
    tar -jxvf wham.tar.bz2 && \
    cp wham/wham/wham /usr/local/bin && \
    cp wham/wham-2d/wham-2d /usr/local/bin && \
    rm wham.tar.bz2

# Download and install ProtoMS
RUN wget https://biosimspace.blob.core.windows.net/dependencies/protoms.tar.bz2 -O protoms.tar.bz2 && \
    tar -jxvf protoms.tar.bz2 && \
    rm protoms.tar.bz2 && \
    chown -R $NB_USER:$NB_GID /home/protoms3.3.0 && \
    fix-permissions /home/protoms3.3.0

# Create the workshops directory and make sure it is owned by the user
RUN mkdir /home/workshops && \
    chown -R $NB_USER:$NB_GID /home/workshops

# Set the path to FESetup and add it to the path
ENV FES_HOME=/home/FESetup1.2.1/FESetup64 \
    PROTOMSHOME=/home/protoms3.3.0 \
    WHAM_HOME=/home/wham \
    OPENMM_PLUGIN_DIR=$SIRE/lib/plugins

ENV PATH=$PATH:$FES_HOME/bin

# Switch to the user so we can pull in the workshops
USER $NB_USER

# Install pyPcazip / MDPlus
RUN conda install cython h5py && \
    pip install pyPcazip && \
    conda clean -tipsy && \
    rm -rf $HOME/.cache $HOME/.jupyter $HOME/.local/share/jupyter

# Now git clone in all workshops we wish to use...
WORKDIR /home/workshops
RUN git clone https://github.com/ccpbiosim/xswaps
RUN git clone https://github.com/ccpbiosim/python_and_data
RUN git clone https://github.com/ccpbiosim/fesetup_workshop
RUN git clone https://github.com/ccpbiosim/md_workshop
RUN git clone https://github.com/ccpbiosim/fe_analysis
RUN git clone https://github.com/ccpbiosim/biosimspace_workshop

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

# Copy a modified library from Sire 2018.1.1
COPY libSireIO.so.2018.1.0 /opt/conda/lib/libSireIO.so.2018.1.0
RUN cp /opt/conda/lib/libSireIO.so.2018.1.0 /opt/conda/pkgs/sire-2018.1.0/lib/

# Install openbabel (doing this late as last-minute addition)
USER root
RUN apt-get update && \
    apt-get install -yq openbabel && \
    apt-get install -yq g++ && \
    apt-get install -yq dssp && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*   

USER $NB_USER

# Install isambard and scikit-image (late requirement)
RUN pip install isambard && \
    pip install scikit-image && \
    conda clean -tipsy && \
    rm -rf $HOME/.cache $HOME/.jupyter $HOME/.local/share/jupyter

# clone in the last workshops
WORKDIR /home/workshops
RUN git clone https://github.com/ccpbiosim/isambard_workshop
RUN git clone https://github.com/ccpbiosim/gcmc_protoms_workshop
RUN git clone https://github.com/ccpbiosim/qmmm_workshop

WORKDIR $HOME

# Link all of the directories into the home directory.
# We do this, as some JupyterHubs will wipe the home
# directory, so need to install workshop files elsewhere.
# However, we need to remove anything that is currently
# in home (e.g. a link to biosimspace)
RUN rm * && ln -s /home/workshops/* .

# Need to use git-lfs to get the gcmc workshop
USER root
RUN wget https://github.com/git-lfs/git-lfs/releases/download/v2.4.0/git-lfs-linux-386-2.4.0.tar.gz && \
    tar -zxvf git-lfs-linux-386-2.4.0.tar.gz && \
    ./git-lfs-2.4.0/install.sh && \
    rm -rf ./git-lfs-2.4.0 git-lfs-linux-386-2.4.0.tar.gz

USER $NB_USER

# pull in the protoms workshop
WORKDIR /home/workshops/gcmc_protoms_workshop
RUN git lfs pull
WORKDIR $HOME

# Patch the netcdf writer in scipy
RUN wget https://raw.githubusercontent.com/scipy/scipy/master/scipy/io/netcdf.py -O /opt/conda/lib/python3.5/site-packages/scipy/io/netcdf.py

# Finally, run 'update_workshops' so that everything is 
# fully updated (or we want to update without rebuilding
# everything), and recopy the isambard settings to $HOME
RUN /opt/conda/bin/update_workshops 4
RUN cp $HOME/isambard_workshop/.isambard_settings $HOME/

# Ensure that the container runs as $NB_USER
USER $NB_USER
