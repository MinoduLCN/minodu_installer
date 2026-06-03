"""
Section 3 — Install RaspAP

Run standalone:
  pyinfra inventory.py 03_raspap.py
"""

import io

from vars import _set_pass_php, ssid

from pyinfra.operations import files, server

server.shell(
    name="Clone RaspAP repository",
    commands=[
        "test -d /home/pi/raspap-webgui || "
        "git clone https://github.com/RaspAP/raspap-webgui.git /home/pi/raspap-webgui",
        "git -C /home/pi/raspap-webgui checkout 3.5.4"
    ],
)

server.shell(
    name="Install RaspAP (idempotent)",
    commands=[
        "test -d /etc/raspap || "
        "TERM=xterm bash /home/pi/raspap-webgui/installers/raspbian.sh --yes",
    ]
)

server.shell(
    name="Set lighttpd webinterface port to 81",
    commands=[
        "sed -i 's/^server\\.port\\s*=.*/server.port                 = 81/' "
        "/etc/lighttpd/lighttpd.conf",
    ],
)

files.put(
    name="Upload RaspAP password helper script",
    src=io.BytesIO(_set_pass_php.encode()),
    dest="/tmp/set_raspap_pass.php",
    mode="600",
)

server.shell(
    name="Set RaspAP admin password",
    commands=["php /tmp/set_raspap_pass.php && rm /tmp/set_raspap_pass.php"],
)

files.template(
    name="Configure hostapd (open network, wlan1, ch1, 2.4GHz)",
    src="templates/hostapd.conf.j2",
    dest="/etc/hostapd/hostapd.conf",
    mode="644",
    ssid=ssid,
)

files.put(
    name="Configure dnsmasq DHCP for wlan1 (10.20.1.x)",
    src="files/090_wlan1.conf",
    dest="/etc/dnsmasq.d/090_wlan1.conf",
    mode="644",
)

server.shell(
    name="Add static IP block for wlan1 in dhcpcd.conf",
    commands=[
        "grep -q 'RaspAP wlan1 configuration' /etc/dhcpcd.conf || "
        r"printf '\n# RaspAP wlan1 configuration\n"
        r"interface wlan1\n"
        r"static ip_address=10.20.1.1/24\n"
        r"static routers=10.20.1.1\n"
        r"static domain_name_servers=1.1.1.1 8.8.8.8\n' >> /etc/dhcpcd.conf",
    ],
)

server.reboot(
    name="Reboot after AP configuration"
)