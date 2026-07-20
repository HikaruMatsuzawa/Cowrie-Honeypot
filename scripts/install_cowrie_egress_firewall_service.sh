#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-install}"
SERVICE_NAME="${SERVICE_NAME:-cowrie-egress-firewall.service}"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIREWALL_SCRIPT="${REPO_DIR}/scripts/cowrie_egress_firewall.sh"

usage() {
    cat <<'USAGE'
Usage:
  sudo ./scripts/install_cowrie_egress_firewall_service.sh install
  sudo ./scripts/install_cowrie_egress_firewall_service.sh remove
  sudo ./scripts/install_cowrie_egress_firewall_service.sh status

Installs a systemd oneshot service that reapplies Cowrie DOCKER-USER
egress firewall rules after Docker starts.
USAGE
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "ERROR: run with sudo." >&2
        exit 2
    fi
}

require_systemctl() {
    if ! command -v systemctl >/dev/null 2>&1; then
        echo "ERROR: systemctl command not found." >&2
        exit 2
    fi
}

require_firewall_script() {
    if [ ! -x "${FIREWALL_SCRIPT}" ]; then
        echo "ERROR: firewall script is not executable: ${FIREWALL_SCRIPT}" >&2
        echo "Run: chmod +x ${FIREWALL_SCRIPT}" >&2
        exit 2
    fi
}

install_service() {
    require_root
    require_systemctl
    require_firewall_script

    cat > "${SERVICE_PATH}" <<UNIT
[Unit]
Description=Cowrie egress firewall rules
Requires=docker.service
After=docker.service docker.socket network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${REPO_DIR}
EnvironmentFile=-${REPO_DIR}/.env
ExecStart=${FIREWALL_SCRIPT} apply
ExecStop=${FIREWALL_SCRIPT} remove

[Install]
WantedBy=multi-user.target
UNIT

    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}"
    systemctl start "${SERVICE_NAME}"
    systemctl status "${SERVICE_NAME}" --no-pager
}

remove_service() {
    require_root
    require_systemctl

    systemctl stop "${SERVICE_NAME}" >/dev/null 2>&1 || true
    systemctl disable "${SERVICE_NAME}" >/dev/null 2>&1 || true
    rm -f "${SERVICE_PATH}"
    systemctl daemon-reload
    echo "Removed ${SERVICE_NAME}."
}

status_service() {
    require_systemctl
    systemctl status "${SERVICE_NAME}" --no-pager || true
}

case "${ACTION}" in
    install)
        install_service
        ;;
    remove)
        remove_service
        ;;
    status)
        status_service
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
