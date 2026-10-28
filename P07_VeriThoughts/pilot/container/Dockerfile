FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential bison flex gawk pkg-config python3 python3-numpy iverilog ca-certificates \
 && mkdir -p /opt/provenance \
 && dpkg-query -W > /opt/provenance/dpkg-lock.tsv \
 && du -sb /var/lib/apt/lists > /opt/provenance/apt-list-bytes.txt \
 && rm -rf /var/lib/apt/lists/*
COPY yosys-source.tar.gz /tmp/yosys-source.tar.gz
RUN --network=none echo 'a22b1dd9f23bc829ed9bbb938dde5404c2577dc89f4618d5d1e89999eb3d84e8  /tmp/yosys-source.tar.gz' | sha256sum -c - \
 && mkdir /tmp/yosys-src \
 && tar -xzf /tmp/yosys-source.tar.gz -C /tmp/yosys-src --strip-components=1 \
 && cd /tmp/yosys-src \
 && make -j2 CONFIG=gcc ENABLE_ABC=0 ENABLE_TCL=0 ENABLE_READLINE=0 ENABLE_PLUGINS=0 ENABLE_ZLIB=0 PREFIX=/opt/yosys \
 && make install CONFIG=gcc ENABLE_ABC=0 ENABLE_TCL=0 ENABLE_READLINE=0 ENABLE_PLUGINS=0 ENABLE_ZLIB=0 PREFIX=/opt/yosys \
 && cp COPYING /opt/provenance/YOSYS-COPYING \
 && cp Makefile /opt/provenance/YOSYS-Makefile \
 && rm -rf /tmp/yosys-src /tmp/yosys-source.tar.gz
ENV PATH=/opt/yosys/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WORKDIR /work
