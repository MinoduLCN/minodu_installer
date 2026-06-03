"""
Section 2 — WLAN driver (RTL8822BU / 88x2bu)

Run standalone:
  pyinfra inventory.py 02_wlan_driver.py
"""

from vars import *  # noqa: F401,F403

from pyinfra.operations import files, server

server.shell(
    name="Build and install 88x2bu WLAN driver",
    commands=[
        "if ! modinfo 88x2bu >/dev/null 2>&1; then "
        "  git clone --depth=1 https://github.com/morrownr/88x2bu-20210702.git /tmp/88x2bu && "
        "  cd /tmp/88x2bu && make -j4 && make install && depmod -a; "
        "fi",
    ]
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
    name="Reboot to load 88x2bu driver"
)
