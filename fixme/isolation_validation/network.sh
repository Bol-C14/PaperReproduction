test -z "$(ip route)" && if wget -T 1 -q -O /work/network http://192.0.2.1/; then exit 1; fi; echo NETWORK_NONE_OK
