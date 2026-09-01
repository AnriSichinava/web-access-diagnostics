#!/usr/bin/env bash
# One-shot tinyproxy setup for a fresh Ubuntu/Debian VM.
#
# Run this ON THE VM (over SSH), not on your own machine:
#   scp infra/setup_proxy_vm.sh youruser@<vm-ip>:~/
#   ssh youruser@<vm-ip>
#   chmod +x setup_proxy_vm.sh
#   sudo ./setup_proxy_vm.sh <YOUR_HOME_PUBLIC_IP> [PORT]
#
# Find your own public IP first (run this on YOUR machine, not the VM):
#   curl -s ifconfig.me
#
# PORT defaults to 8888 if not given.

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run this with sudo." >&2
  exit 1
fi

ALLOWED_IP="${1:-}"
PORT="${2:-8888}"

if [[ -z "$ALLOWED_IP" ]]; then
  echo "Usage: sudo $0 <YOUR_HOME_PUBLIC_IP> [PORT]" >&2
  echo "Find your IP on your own machine with: curl -s ifconfig.me" >&2
  exit 1
fi

echo "== Installing tinyproxy =="
apt-get update -qq
apt-get install -y -qq tinyproxy

CONFIG_FILE="/etc/tinyproxy/tinyproxy.conf"
BACKUP_FILE="/etc/tinyproxy/tinyproxy.conf.bak.$(date +%s)"

echo "== Backing up existing config to $BACKUP_FILE =="
cp "$CONFIG_FILE" "$BACKUP_FILE"

echo "== Writing locked-down config (port $PORT, allow only $ALLOWED_IP) =="
sed -i "s/^Port .*/Port $PORT/" "$CONFIG_FILE"

# Remove any existing Allow lines, then add exactly one for the given IP.
sed -i "/^Allow /d" "$CONFIG_FILE"
echo "Allow $ALLOWED_IP" >> "$CONFIG_FILE"

echo "== Restarting and enabling tinyproxy =="
systemctl restart tinyproxy
systemctl enable -q tinyproxy

echo
echo "Done. tinyproxy is listening on port $PORT, allowed client IP: $ALLOWED_IP"
echo
echo "Next steps:"
echo "1. Open port $PORT in this VM's cloud firewall/security group (not just ufw)."
echo "2. From YOUR machine, verify it works:"
echo "     curl -x http://<this-vm-public-ip>:$PORT https://httpbin.org/ip"
echo "3. Add it to proxies.yaml in the diagnostics project:"
echo "     - label: <name>"
echo "       host: <this-vm-public-ip>"
echo "       port: $PORT"
echo "       scheme: http"
echo "       region: <region>"
