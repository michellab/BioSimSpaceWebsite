# Dependency building image

This image is used to allow me to build dependencies that are installed
into the BioSimSpace image. This image provides the Linux environment
that BioSimSpace uses with a bash prompt available as root.

Build and run using

```
$ docker build . -t chryswoods/builddeps
$ docker run -it --rm chryswoods/builddeps
```

