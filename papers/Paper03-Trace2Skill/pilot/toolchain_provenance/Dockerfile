FROM scratch
COPY rootfs/ /
USER 65534:65534
WORKDIR /work
ENV PATH=/usr/bin:/bin HOME=/tmp TMPDIR=/tmp LANG=C.UTF-8
ENTRYPOINT ["/bin/sh"]
