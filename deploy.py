"""
Minodu Pi Installer
===================
Automates the full SETUP.md + WLAN_DRIVER_SETUP.md setup on a fresh
Raspberry Pi OS Lite 64-bit image (hostname: minodupi), then deploys
the Minodu app stack.

Prerequisites (manual, once):
  - Flash Pi OS Lite 64-bit, set hostname=minodupi, enable SSH
  - Open raspi-config > Localisation Options > WLAN Country > Togo
  - Plug TP-Link AC600 Archer T2U Plus into USB1 port
  - Ensure SSH key is authorised on the Pi for the pi user

Run from project root:
  pyinfra inventory.py deploy.py

Dry-run:
  pyinfra inventory.py deploy.py --dry
"""

import binascii
import getpass
import io
import secrets

from pyinfra import config
from pyinfra.operations import apt, files, server, systemd

config.SUDO = True

# ── Prompts ───────────────────────────────────────────────────────────────────

print("\nMinodu Pi Installer — Configuration\n")

ssid = input("WiFi SSID [Minodu]: ").strip() or "Minodu"
raspap_password = getpass.getpass("RaspAP admin password [secret]: ").strip() or "secret"

print()
admin_phone = input("Admin phone number: ").strip()
admin_password = getpass.getpass("Admin password: ").strip()
print()

minodu_repo = "https://github.com/MinoduLCN/minodu.git"

# Auto-generated secrets — only written to .env if the file doesn't yet exist.
_mysql_password = secrets.token_urlsafe(24)
_mysql_root_password = secrets.token_urlsafe(24)
_jwt_secret = secrets.token_urlsafe(32)
_forum_admin_password = secrets.token_urlsafe(16)

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
    # The installer may reboot internally; pyinfra reconnects automatically.
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

files.directory(
    name="Create captive portal www directory",
    path="/home/minodu/www",
    user="www-data",
    group="www-data",
    mode="755",
)

files.put(
    name="Upload hotspot-detect.html (OS captive portal probe response)",
    src="resources/captive/hotspot-detect.html",
    dest="/home/minodu/www/hotspot-detect.html",
    user="www-data",
    group="www-data",
    mode="644",
)

files.put(
    name="Upload captive portal index.html",
    src="resources/captive/index.html",
    dest="/home/minodu/www/index.html",
    user="www-data",
    group="www-data",
    mode="644",
)

# ── 6. Scripts & systemd services ─────────────────────────────────────────────

files.put(
    name="Install captive-enable toggle script",
    src="scripts/captive-enable.sh",
    dest="/usr/local/bin/captive-enable",
    mode="755",
)

files.put(
    name="Install RaspAP watchdog script",
    src="scripts/raspap-watchdog.sh",
    dest="/usr/local/bin/raspap-watchdog",
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

# ── 7. Minodu app ─────────────────────────────────────────────────────────────

server.shell(
    name="Install ollama",
    commands=[
        "command -v ollama >/dev/null 2>&1 || curl -fsSL https://ollama.com/install.sh | sh",
    ],
    timeout=300,
)

server.shell(
    name="Pull ollama models",
    commands=[
        "ollama pull llama3.2:1b",
        "ollama pull nomic-embed-text",
        "ollama pull all-minilm:l6-v2",
    ],
    timeout=600,
)

files.directory(
    name="Create ollama systemd override directory",
    path="/etc/systemd/system/ollama.service.d",
    mode="755",
)

files.put(
    name="Configure ollama (bind to all interfaces, pin to CPU cores 0-2)",
    src=io.BytesIO(
        b'[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0:11434"\nCPUAffinity=0 1 2\n'
    ),
    dest="/etc/systemd/system/ollama.service.d/override.conf",
    mode="644",
)

systemd.service(
    name="Enable and restart ollama with new config",
    service="ollama",
    running=True,
    enabled=True,
    daemon_reload=True,
    restarted=True,
)

server.shell(
    name="Install Docker",
    commands=[
        "command -v docker >/dev/null 2>&1 || curl -sSL https://get.docker.com | sh",
    ],
    timeout=300,
)

server.shell(
    name="Add pi to docker group",
    commands=["usermod -aG docker pi"],
)

systemd.service(
    name="Enable Docker",
    service="docker",
    running=True,
    enabled=True,
)

apt.packages(
    name="Install git-lfs, npm, python3-poetry",
    packages=["git-lfs", "npm", "python3-poetry"],
)

server.shell(
    name="Install pyenv for pi user",
    commands=[
        "test -d /home/pi/.pyenv || su - pi -c 'curl https://pyenv.run | bash'",
    ],
    timeout=120,
)

server.shell(
    name="Add pyenv to pi user .bashrc",
    commands=[
        "su - pi -c '"
        r"grep -q PYENV_ROOT ~/.bashrc || printf "
        r'"\nexport PYENV_ROOT=\"\$HOME/.pyenv\"\n'
        r"[[ -d \$PYENV_ROOT/bin ]] && export PATH=\"\$PYENV_ROOT/bin:\$PATH\"\n"
        r'eval \"\$(pyenv init - bash)\"\n"'
        " >> ~/.bashrc'",
    ],
)

server.shell(
    name="Install Python 3.12.11 via pyenv",
    commands=[
        "su - pi -c '"
        "export PYENV_ROOT=\"$HOME/.pyenv\" && "
        "export PATH=\"$PYENV_ROOT/bin:$PATH\" && "
        "eval \"$(pyenv init - bash)\" && "
        "pyenv install --skip-existing 3.12.11'",
    ],
    timeout=600,
)

if minodu_repo:
    server.shell(
        name="Clone minodu repository",
        commands=[
            f"test -d /home/pi/minodu || su - pi -c 'git clone {minodu_repo} /home/pi/minodu'",
        ],
    )

    server.shell(
        name="Pull git-lfs files",
        commands=["su - pi -c 'cd /home/pi/minodu && git lfs pull'"],
        timeout=300,
    )

    _env_content = (
        f"MYSQL_USER=minodu_user\n"
        f"MYSQL_PASSWORD={_mysql_password}\n"
        f"MYSQL_ROOT_PASSWORD={_mysql_root_password}\n"
        f"DB_NAME=minodu\n"
        f"JWT_SECRET_KEY={_jwt_secret}\n"
        f"FORUM_ADMIN_PASSWORD={_forum_admin_password}\n"
        f"ADMIN_PASSWORD={admin_password}\n"
        f"ADMIN_PHONE={admin_phone}\n"
        f"ENVIRONMENT=production\n"
    )

    files.put(
        name="Stage .env to /tmp",
        src=io.BytesIO(_env_content.encode()),
        dest="/tmp/minodu.env",
        mode="600",
    )

    server.shell(
        name="Install .env (skip if already present)",
        commands=[
            "if [ ! -f /home/pi/minodu/.env ]; then "
            "  mv /tmp/minodu.env /home/pi/minodu/.env && "
            "  chown pi:pi /home/pi/minodu/.env; "
            "else rm -f /tmp/minodu.env; fi",
        ],
    )

    server.shell(
        name="Install npm dependencies",
        commands=["su - pi -c 'cd /home/pi/minodu && npm install'"],
        timeout=300,
    )

    server.shell(
        name="Build and start Docker services",
        commands=["bash -c 'cd /home/pi/minodu && npm run docker:start'"],
        timeout=300,
    )

    server.shell(
        name="Install sync tool dependencies",
        commands=["su - pi -c 'cd /home/pi/minodu/tools/sync && poetry install'"],
        timeout=120,
    )

    server.shell(
        name="Sync database and update RAG embeddings",
        commands=[
            "su - pi -c 'cd /home/pi/minodu && npm run sync:database'",
        ],
        timeout=999,
    )

    server.shell(
        name="Sync database and update RAG embeddings",
        commands=[
            "su - pi -c 'cd /home/pi/minodu && npm run sync:rag'",
        ],
        timeout=999,
    )
