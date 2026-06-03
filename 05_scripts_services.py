"""
Section 6 — Scripts & systemd services

Run standalone:
  pyinfra inventory.py 06_scripts_services.py
"""

from vars import *  # noqa: F401,F403

from pyinfra.operations import files, server, systemd

files.put(
    name="Install captive-enable toggle script",
    src="scripts/captive-enable.sh",
    dest="/usr/local/bin/captive-enable",
    mode="755",
)

files.put(
    name="Install daily-reboot systemd service unit",
    src="scripts/daily-reboot.service",
    dest="/etc/systemd/system/daily-reboot.service",
    mode="644",
)

files.put(
    name="Install daily-reboot systemd timer unit",
    src="scripts/daily-reboot.timer",
    dest="/etc/systemd/system/daily-reboot.timer",
    mode="644",
)

systemd.service(
    name="Enable and start daily-reboot timer",
    service="daily-reboot.timer",
    running=True,
    enabled=True,
    daemon_reload=True,
)

systemd.service(
    name="Restart dnsmasq to pick up captive portal config",
    service="dnsmasq",
    running=True,
    restarted=True,
)
