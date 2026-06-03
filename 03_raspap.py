"""
Section 3 — Install RaspAP

Run standalone:
  pyinfra inventory.py 03_raspap.py
"""

import io

from vars import _set_pass_php  # noqa: F401

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
    name="Install RaspAP (idempotent) (This will take a while)",
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
