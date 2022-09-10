#Start from ubuntu 20.04 as a base
FROM ubuntu:22.04 AS builder

#Install needed packages
RUN apt update &&                                        \
    apt install -y software-properties-common         && \
    add-apt-repository -y ppa:ubuntu-toolchain-r/test && \
    apt update &&                                        \
    apt install -y                                       \
    g++-11                                                    \
    gcc-11                                                    \
    cmake                                                     \
    autoconf                                                  \
    libtool                                                   \
    vim                                                       \
    curl                                                      \
    git                                                       \
    perl                                                      \
    zlib1g-dev                                                \
    zlib1g                                                    \
    yasm                                                      \
    texinfo                                                   \
    subversion                                                \
    apt-utils                                                 \
    wget                                                      \
    lzip

#Set GCC-11 and G++-11 as the default compilers
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 11 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 11 && \
    update-alternatives --install /usr/bin/cc  cc  /usr/bin/gcc 11    && \
    update-alternatives --install /usr/bin/c++ c++ /usr/bin/g++ 11    && \
    update-alternatives --set c++ /usr/bin/g++                        && \
    update-alternatives --set cc  /usr/bin/gcc

#Set working directory
WORKDIR /tmp

#Build variable
ARG BUILDTHREADS=4

#Copy all dependencies of YAFU
#Note: the repository for this code can be found here: https://sourceforge.net/p/msieve/code/HEAD/tree/trunk/
COPY ./docker/msieve-code-r1044-trunk    /tmp/msieve

#Install it all in the right order
RUN  wget https://gmplib.org/download/gmp/gmp-6.2.1.tar.lz                                                 && \ 
     tar --lzip  -xf gmp-6.2.1.tar.lz                                                                      && \    
     cd /tmp/gmp-6.2.1                                                                                     && \   
     autoreconf -i                                                                                         && \
     find . -type f -exec touch {} +                                                                       && \
     chmod +x ./mpn/m4-ccas                                                                                && \
     ./configure --enable-cxx                                                                              && \
     make    -j $BUILDTHREADS                                                                              && \
     make install                                                                                          && \
     mkdir -p /users/buhrow/src/c/gmp_install/gmp-6.2.0/lib                                                && \            
     cp /tmp/gmp-6.2.1/.libs/libgmp.a /users/buhrow/src/c/gmp_install/gmp-6.2.0/lib/libgmp.a               && \            
     #Install GMP-ECM 
     cd /tmp                                                                                               && \ 
     git clone https://gitlab.inria.fr/zimmerma/ecm.git                                                    && \
     cd ecm                                                                                                && \
     git checkout master                                                                                   && \
     autoreconf -i                                                                                         && \
     ls /usr/local/lib                                                                                     && \
     ls /usr/local/include                                                                                 && \
     touch configure                                                                                       && \
     ./configure --with-gmp=/usr/local/                                                                    && \
     make  -j $BUILDTHREADS                                                                                && \
     make check                                                                                            && \
     make -j $BUILDTHREADS                                                                                 && \
     make install                                                                                          && \
     cd /tmp                                                                                               && \
     mv ecm gmp-ecm                                                                                        && \
     #Build ggnfs sievers
     cd /tmp                                                                                               && \
     git clone https://github.com/FACT0RN/ggnfs.git                                                        && \
     cd ggnfs/src/experimental/lasieve4_64                                                                 && \
     ./build.sh                                                                                            && \
     mkdir /tmp/ggnfs_bin                                                                                  && \
     mv  gnfs-lasieve4I11e /tmp/ggnfs/                                                                     && \ 
     mv  gnfs-lasieve4I12e /tmp/ggnfs/                                                                     && \ 
     mv  gnfs-lasieve4I13e /tmp/ggnfs/                                                                     && \ 
     mv  gnfs-lasieve4I14e /tmp/ggnfs/                                                                     && \ 
     mv  gnfs-lasieve4I15e /tmp/ggnfs/                                                                     && \ 
     mv  gnfs-lasieve4I16e /tmp/ggnfs/                                                                     && \ 
     #Build msieve
     cd /tmp/msieve                                                                                        && \
     make all NO_ZLIB=1 ECM=1                                                                              && \
     #Build ytools
     cd /tmp                                                                                               && \
     git clone https://github.com/bbuhrow/ytools.git                                                       && \
     cd /tmp/ytools                                                                                        && \
     make -j $BUILDTHREADS  CC=gcc-11 CPP=g++-11 CXX=g++-11 LD=g++-11                                      && \
     #Build ysieve
     cd /tmp                                                                                               && \
     git clone https://github.com/bbuhrow/ysieve.git                                                       && \
     cd /tmp/ysieve                                                                                        && \
     make -j $BUILDTHREADS                                                                                 && \
     #Install mpir
     cd /tmp                                                                                               && \
     git clone https://github.com/wbhart/mpir.git                                                          && \
     cd mpir                                                                                               && \
     ./autogen.sh                                                                                          && \
     touch configure                                                                                       && \
     ./configure                                                                                           && \
     make                                                                                                  && \
     make install                                                                                          && \
     #Build YAFU
     cd /tmp                                                                                               && \ 
     git clone https://github.com/bbuhrow/yafu.git                                                         && \ 
     cd /tmp/yafu                                                                                          && \ 
     git checkout 13cfca2b533dd8353cb6e1ef4b6002ea01fef8da                                                 && \
     make yafu NFS=1                                                                                       

#Copy yafu ini file
COPY docker/yafu.ini /tmp/yafu

#Give permissions to use sievers
RUN chmod +x /tmp/ggnfs/gnfs-lasieve4*

#Create lighter container
FROM ubuntu:22.04

WORKDIR /tmp

RUN apt update && apt install -y  \ 
                  libgmp-dev      \
                  libcrypto++8    \
                  libcrypto++-dev \ 
                  python3-minimal \
                  python3-pip                                                                              && \ 
     pip3 install --upgrade pip                                                                            && \
     pip3 install sympy           \ 
                  gmpy2           \
                  numpy           \
                  base58          \
                  factordb-python      

WORKDIR /tmp/factoring

#Copy the entire repo into the image
COPY . . 

RUN ./script/build.sh

##GMP library
COPY --from=builder /usr/lib/x86_64-linux-gnu/libgmp.so.10      /usr/lib/x86_64-linux-gnu/libgmp.so.10     
COPY --from=builder /usr/lib/x86_64-linux-gnu/libgmp.so.10.4.1  /usr/lib/x86_64-linux-gnu/libgmp.so.10.4.1    
COPY --from=builder /usr/local/lib/libgmpxx.so.4.6.1            /usr/local/lib/libgmpxx.so.4.6.1                
COPY --from=builder /usr/local/lib/libgmp.so.10                 /usr/local/lib/libgmp.so.10                       
COPY --from=builder /usr/local/lib/libgmpxx.so.4                /usr/local/lib/libgmpxx.so.4                    
COPY --from=builder /usr/local/lib/libgmpxx.a                   /usr/local/lib/libgmpxx.a                     
COPY --from=builder /usr/local/lib/libgmp.so                    /usr/local/lib/libgmp.so                             
COPY --from=builder /usr/local/lib/libgmp.a                     /usr/local/lib/libgmp.a                           
COPY --from=builder /usr/local/lib/libgmpxx.so                  /usr/local/lib/libgmpxx.so                         
COPY --from=builder /usr/local/lib/libgmp.so.10.4.1             /usr/local/lib/libgmp.so.10.4.1                    
COPY --from=builder /usr/local/lib/libgmpxx.la                  /usr/local/lib/libgmpxx.la                               
COPY --from=builder /usr/local/lib/libgmp.la                    /usr/local/lib/libgmp.la                            

#COPY Executables
COPY --from=builder /tmp/ggnfs/gnfs-lasieve4I11e           /tmp/ggnfs-bin/gnfs-lasieve4I11e
COPY --from=builder /tmp/ggnfs/gnfs-lasieve4I12e           /tmp/ggnfs-bin/gnfs-lasieve4I12e
COPY --from=builder /tmp/ggnfs/gnfs-lasieve4I13e           /tmp/ggnfs-bin/gnfs-lasieve4I13e
COPY --from=builder /tmp/ggnfs/gnfs-lasieve4I14e           /tmp/ggnfs-bin/gnfs-lasieve4I14e
COPY --from=builder /tmp/ggnfs/gnfs-lasieve4I15e           /tmp/ggnfs-bin/gnfs-lasieve4I15e
COPY --from=builder /tmp/ggnfs/gnfs-lasieve4I16e           /tmp/ggnfs-bin/gnfs-lasieve4I16e
COPY --from=builder /tmp/gmp-ecm/ecm                       /tmp/gmp-ecm/ecm
COPY --from=builder /tmp/mpir/printf/.libs/libprintf.a     /tmp/mpir/printf/.libs/libprintf.a
COPY --from=builder /tmp/mpir/mpf/.libs/libmpf.a           /tmp/mpir/mpf/.libs/libmpf.a
COPY --from=builder /tmp/mpir/.libs/libmpir.a              /tmp/mpir/.libs/libmpir.a
COPY --from=builder /tmp/mpir/mpq/.libs/libmpq.a           /tmp/mpir/mpq/.libs/libmpq.a
COPY --from=builder /tmp/mpir/mpn/.libs/libmpn.a           /tmp/mpir/mpn/.libs/libmpn.a
COPY --from=builder /tmp/mpir/scanf/.libs/libscanf.a       /tmp/mpir/scanf/.libs/libscanf.a
COPY --from=builder /tmp/mpir/mpz/.libs/libmpz.a           /tmp/mpir/mpz/.libs/libmpz.a
COPY --from=builder /tmp/mpir/fft/.libs/libfft.a           /tmp/mpir/fft/.libs/libfft.a
COPY --from=builder /tmp/mpir/.libs/libmpir.so.23          /tmp/mpir/.libs/libmpir.so.23
COPY --from=builder /tmp/mpir/.libs/libmpir.so.23.0.3      /tmp/mpir/.libs/libmpir.so.23.0.3
COPY --from=builder /tmp/mpir/.libs/libmpir.so             /tmp/mpir/.libs/libmpir.so
COPY --from=builder /tmp/msieve/libmsieve.a                /tmp/msieve/libmsieve.a 
COPY --from=builder /tmp/ysieve/libysieve.a                /tmp/ysieve/libysieve.a 
COPY --from=builder /tmp/ytools/libytools.a                /tmp/ytools/libytools.a
COPY --from=builder /tmp/yafu/libyecm.a                    /tmp/yafu/libyecm.a
COPY --from=builder /tmp/yafu/libynfs.a                    /tmp/yafu/libynfs.a
COPY --from=builder /tmp/yafu/libysiqs.a                   /tmp/yafu/libysiqs.a  
COPY --from=builder /tmp/yafu/yafu                         /tmp/yafu/yafu  

#Copy yafu ini file
COPY docker/yafu.ini /tmp/yafu

ENV OMP_PROC_BIND="TRUE"
ENV MSIEVE_BIN="/tmp/ggnfs-bin"
ENV YAFU_BIN="/tmp/yafu/yafu"

WORKDIR /tmp/factoring/python

CMD bash
