test "$(id -u)" = 65534 && grep -q "CapEff:[[:space:]]*0000000000000000" /proc/self/status && grep -q "NoNewPrivs:[[:space:]]*1" /proc/self/status && echo PRIVILEGES_OK
