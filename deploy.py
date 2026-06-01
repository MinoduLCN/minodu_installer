"""
Minodu Pi Installer
===================
Automates the full SETUP.md + WLAN_DRIVER_SETUP.md setup on a fresh
Raspberry Pi OS Lite 64-bit image (hostname: minodupi).

Prerequisites (manual, once):
  - Flash Pi OS Lite 64-bit, set hostname=minodupi, enable SSH
  - Open raspi-config > Localisation Options > WLAN Country > Togo
  - Plug TP-Link AC600 Archer T2U Plus into USB1 port

Run from project root:
  pyinfra inventory.py deploy.py

Dry-run:
  pyinfra inventory.py deploy.py --dry
"""

import binascii
import getpass
import io

from pyinfra import config
from pyinfra.operations import apt, files, server, systemd

config.SUDO = True

# ── Prompt for deployment-specific values ─────────────────────────────────────

print("\nMinodu Pi Installer — Configuration\n")
ssid = input("WiFi SSID [Minodu3]: ").strip() or "Minodu3"
raspap_password = getpass.getpass("RaspAP admin password [secret]: ").strip() or "secret"
print()

# ── 1. System packages ────────────────────────────────────────────────────────

apt.update(name="Update apt cache", cache_time=3600)

apt.packages(
    name="Install build dependencies",
    packages=["git", "build-essential", "dkms", "bc"],
)

server.shell(
    name="Install kernel headers",
    commands=["apt-get install -y linux-headers-$(uname -r)"],
)

# ── 2. WLAN driver (RTL8822BU / 88x2bu) ──────────────────────────────────────
#
# Newer Raspberry Pi OS ships with the in-kernel rtw88_8822bu driver, which has
# a known AP-mode bug (TX is silently broken). We install the out-of-tree
# 88x2bu driver from morrownr instead.

server.shell(
    name="Build and install 88x2bu WLAN driver",
    commands=[
        "if ! modinfo 88x2bu >/dev/null 2>&1; then "
        "  git clone --depth=1 https://github.com/morrownr/88x2bu-20210702.git /tmp/88x2bu && "
        "  cd /tmp/88x2bu && make -j4 && make install && depmod -a; "
        "fi",
    ],
)

files.put(
    name="Blacklist in-kernel rtw88_8822bu driver",
    src="files/blacklist-rtw88-8822bu.conf",
    dest="/etc/modprobe.d/blacklist-rtw88-8822bu.conf",
    mode="644",
)

server.shell(
    name="Disable USB autosuspend in cmdline.txt",
    commands=[
        "grep -q 'usbcore.autosuspend=-1' /boot/firmware/cmdline.txt || "
        "sed -i 's/$/ usbcore.autosuspend=-1/' /boot/firmware/cmdline.txt",
    ],
)

files.put(
    name="Disable WLAN power management via udev",
    src="files/70-rtl88x2bu-pm.rules",
    dest="/etc/udev/rules.d/70-rtl88x2bu-pm.rules",
    mode="644",
)

server.reboot(
    name="Reboot to load 88x2bu driver",
    delay=5,
    timeout=120,
    interval=2,
)

# ── 3. Install RaspAP ─────────────────────────────────────────────────────────

server.shell(
    name="Clone RaspAP repository",
    commands=[
        "test -d /home/pi/raspap-webgui || "
        "git clone https://github.com/RaspAP/raspap-webgui.git /home/pi/raspap-webgui",
    ],
)

server.shell(
    name="Install RaspAP (idempotent)",
    commands=[
        "test -d /etc/raspap || "
        "bash /home/pi/raspap-webgui/installers/raspbian.sh --yes",
    ],
    # The installer reboots internally; pyinfra reconnects automatically.
    timeout=600,
)

server.shell(
    name="Set lighttpd webinterface port to 81",
    commands=[
        "sed -i 's/^server\\.port\\s*=.*/server.port                 = 81/' "
        "/etc/lighttpd/lighttpd.conf",
    ],
)

# Password is hex-encoded so it survives PHP/shell quoting regardless of content.
_pass_hex = binascii.hexlify(raspap_password.encode()).decode()
_set_pass_php = (
    "<?php\n"
    f"$hash = password_hash(hex2bin('{_pass_hex}'), PASSWORD_DEFAULT);\n"
    "file_put_contents('/etc/raspap/raspap.webgui',\n"
    "    '<?php $userinfo = array(\"admin\" => \"' . $hash . '\"); ?>');\n"
    "echo \"RaspAP password updated.\\n\";\n"
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

# ── 4. AP configuration ───────────────────────────────────────────────────────

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
    name="Reboot after AP configuration",
    delay=5,
    timeout=120,
    interval=2,
)

# ── 5. Captive portal ─────────────────────────────────────────────────────────

files.put(
    name="Configure dnsmasq captive portal (redirects all DNS to 10.20.1.1)",
    src="resources/captive/captive.conf",
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

# ── 6. Scripts & systemd services ─────────────────────────────────────────────

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
