#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
COWRIE_CONTAINER_IP="${COWRIE_CONTAINER_IP:-172.30.0.10}"
COWRIE_NETWORK_SUBNET="${COWRIE_NETWORK_SUBNET:-172.30.0.0/24}"
CHAIN="${CHAIN:-DOCKER-USER}"
ESTABLISHED_COMMENT="cowrie-observer allow established docker traffic"
DROP_COMMENT="cowrie-observer block cowrie outbound"

usage() {
    cat <<'USAGE'
Usage:
  sudo ./scripts/cowrie_egress_firewall.sh apply
  sudo ./scripts/cowrie_egress_firewall.sh status
  sudo ./scripts/cowrie_egress_firewall.sh remove

Environment:
  COWRIE_CONTAINER_IP      default: 172.30.0.10
  COWRIE_NETWORK_SUBNET    default: 172.30.0.0/24

This script manages iptables rules in Docker's DOCKER-USER chain.
It allows established Docker traffic, then blocks new outbound traffic
from the Cowrie container IP to destinations outside the Cowrie subnet.
USAGE
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "ERROR: run with sudo." >&2
        exit 2
    fi
}

require_iptables() {
    if ! command -v iptables >/dev/null 2>&1; then
        echo "ERROR: iptables command not found." >&2
        exit 2
    fi
}

require_chain() {
    if ! iptables -nL "${CHAIN}" >/dev/null 2>&1; then
        echo "ERROR: ${CHAIN} chain not found. Is Docker Engine running?" >&2
        exit 2
    fi
}

has_established_rule() {
    iptables -C "${CHAIN}" \
        -m conntrack --ctstate RELATED,ESTABLISHED \
        -m comment --comment "${ESTABLISHED_COMMENT}" \
        -j ACCEPT >/dev/null 2>&1
}

has_drop_rule() {
    iptables -C "${CHAIN}" \
        -s "${COWRIE_CONTAINER_IP}/32" ! -d "${COWRIE_NETWORK_SUBNET}" \
        -m conntrack --ctstate NEW \
        -m comment --comment "${DROP_COMMENT}" \
        -j DROP >/dev/null 2>&1
}

apply_rules() {
    require_root
    require_iptables
    require_chain

    if ! has_drop_rule; then
        iptables -I "${CHAIN}" 1 \
            -s "${COWRIE_CONTAINER_IP}/32" ! -d "${COWRIE_NETWORK_SUBNET}" \
            -m conntrack --ctstate NEW \
            -m comment --comment "${DROP_COMMENT}" \
            -j DROP
    fi

    if ! has_established_rule; then
        iptables -I "${CHAIN}" 1 \
            -m conntrack --ctstate RELATED,ESTABLISHED \
            -m comment --comment "${ESTABLISHED_COMMENT}" \
            -j ACCEPT
    fi

    status_rules
}

remove_rules() {
    require_root
    require_iptables
    require_chain

    while has_drop_rule; do
        iptables -D "${CHAIN}" \
            -s "${COWRIE_CONTAINER_IP}/32" ! -d "${COWRIE_NETWORK_SUBNET}" \
            -m conntrack --ctstate NEW \
            -m comment --comment "${DROP_COMMENT}" \
            -j DROP
    done

    while has_established_rule; do
        iptables -D "${CHAIN}" \
            -m conntrack --ctstate RELATED,ESTABLISHED \
            -m comment --comment "${ESTABLISHED_COMMENT}" \
            -j ACCEPT
    done

    status_rules
}

status_rules() {
    require_iptables
    require_chain

    echo "Cowrie container IP: ${COWRIE_CONTAINER_IP}"
    echo "Cowrie network subnet: ${COWRIE_NETWORK_SUBNET}"
    iptables -S "${CHAIN}" | grep -F "cowrie-observer" || true
}

case "${ACTION}" in
    apply)
        apply_rules
        ;;
    remove)
        remove_rules
        ;;
    status)
        status_rules
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
