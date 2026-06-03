"""
Section 5 — Captive portal

Run standalone:
  pyinfra inventory.py 05_captive_portal.py
"""

import io

from vars import *  # noqa: F401,F403

from pyinfra.operations import apt, files, server

files.template(
    name="Configure dnsmasq captive portal (redirects all DNS to 10.20.1.1)",
    src=io.StringIO("interface=wlan1\naddress=/#/10.20.1.1\n"),
    dest="/etc/dnsmasq.d/captive.conf",
    mode="644",
)

server.shell(
    name="Add iptables DNS redirect rules for captive portal",
    commands=[
        "iptables -t nat -C PREROUTING -i wlan1 -p udp --dport 53 -j DNAT "
        "--to 10.20.1.1 2>/dev/null || "
        "iptables -t nat -A PREROUTING -i wlan1 -p udp --dport 53 -j DNAT --to 10.20.1.1",
        "iptables -t nat -C PREROUTING -i wlan1 -p tcp --dport 53 -j DNAT "
        "--to 10.20.1.1 2>/dev/null || "
        "iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 53 -j DNAT --to 10.20.1.1",
    ],
)

apt.packages(
    name="Install iptables-persistent (survives reboots)",
    packages=["iptables-persistent"],
    present=True,
)

server.shell(
    name="Save iptables rules",
    commands=["iptables-save > /etc/iptables/rules.v4"],
)
