# Dependency building image

This image is used to allow me to build dependencies that are installed
into the BioSimSpace image. This image provides the Linux environment
that BioSimSpace uses with a bash prompt available as root.

Build and run using

```
$ docker build . -t chryswoods/builddeps
$ docker run -it --rm chryswoods/builddeps
```

## Building dependencies

To build dependencies we first need to update and install compilers

```
root$ apt-get update
root$ apt-get install g++ gcc gfortran
```

## Building gromacs

```
root$ apt-get install cmake
root$ wget ftp://ftp.gromacs.org/pub/gromacs/gromacs-2018.2.tar.gz
root$ tar -zxvf gromacs-2018.2.tar.gz
root$ cd gromacs-2018.2
root$ mkdir build
root$ cd build
root$ cmake -DGMX_BUILD_OWN_FFTW=ON -DCMAKE_INSTALL_PREFIX=/home/gromacs ../
root$ make -j 16
root$ make install
root$ cd /home
root$ tar -jcvf gromacs.tar.bz2 gromacs
```

## Copying dependencies to another machine

I use scp to move created files to another machine.

```
root$ apt-get install ssh
root$ scp gromacs.tar.bz2 chris@cibod.acrc.bris.ac.uk:
```

