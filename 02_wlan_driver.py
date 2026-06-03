"""
Section 2 — WLAN driver (RTL8822BU / 88x2bu)

Run standalone:
  pyinfra inventory.py 02_wlan_driver.py
"""

from vars import *  # noqa: F401,F403

from pyinfra.operations import apt, files, server

server.shell(
    name="Set WLAN country code",
    commands=[f"raspi-config nonint do_wifi_country {wlan_country}"],
)

server.shell(
    name="Disable USB autosuspend in cmdline.txt",
    commands=[
        "grep -q 'usbcore.autosuspend=-1' /boot/firmware/cmdline.txt || "
        "sed -i 's/$/ usbcore.autosuspend=-1/' /boot/firmware/cmdline.txt",
    ],
)

server.shell(
    name="Clone 8821au driver repository",
    commands=[
        "test -d /opt/8821au-20210708 || "
        "git clone https://github.com/morrownr/8821au-20210708.git /opt/8821au-20210708",
    ],
)

server.shell(
    name="Install 8821au driver",
    commands=[
        "dkms status | grep -q '8821au' || "
        "(cd /opt/8821au-20210708 && printf 'n\\n' | ./install-driver.sh)",
    ],
)

server.shell(
    name="Disable power management in 8821au driver config",
    commands=[
        "grep -q 'rtw_power_mgnt=0' /etc/modprobe.d/8821au.conf || "
        "sed -i '/^options 8821au/ s/$/ rtw_power_mgnt=0/' /etc/modprobe.d/8821au.conf",
    ],
)

server.reboot(
    name="Reboot to load 88x2bu driver",
    delay=5,
    interval=5,
    reboot_timeout=90,
)
