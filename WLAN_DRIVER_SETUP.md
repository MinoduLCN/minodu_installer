# WLAN Driver Setup for TP-Link AC600 Archer T2U Plus (RTL8822BU)

Newer Raspberry Pi OS versions ship with the in-kernel `rtw88_8822bu` driver, which has a known AP mode bug (TX is silently broken — `hostapd` reports `AP-ENABLED` but beacons are never transmitted and the SSID is invisible to clients). The fix is to install the out-of-tree `88x2bu` driver from morrownr and blacklist the in-kernel one.

## 1. Install build dependencies

```bash
sudo apt update && sudo apt full-upgrade
sudo apt install -y bc git dkms build-essential raspberrypi-kernel-headers
sudo reboot
```

## 2. Build and install the out-of-tree driver

```bash
git clone https://github.com/morrownr/8821au-20210708.git
cd 8821au-20210708
sudo ./install-driver.sh
```

## 3. Disable wifi power management

```
nano /etc/modprobe.d/8821au.conf
# search for the lne starting with options 8821au and add rtw_power_mgnt=0 at end
options 8821au ... rtw_power_mgnt=0

```

## 4. Disable USB autosuspend

The USB adapter suspends after 2 seconds of inactivity by default, which causes it to stop beaconing. Disable it persistently by adding a kernel parameter.

Edit `/boot/firmware/cmdline.txt` — append to the **single existing line** (do not add a new line):

```
usbcore.autosuspend=-1
```

Example of what the line should look like after editing:

```
console=serial0,115200 console=tty1 root=PARTUUID=... rootfstype=ext4 fsck.repair=yes rootwait cfg80211.ieee80211_regdom=DE usbcore.autosuspend=-1
```

## 5. Disable WLAN power management

```bash
sudo nano /etc/udev/rules.d/70-rtl88x2bu-pm.rules
```

Add:

```
ACTION=="add", SUBSYSTEM=="net", KERNEL=="wlan1", RUN+="/sbin/iwconfig wlan1 power off"
```

## 6. Reboot

```bash
sudo reboot
```

## 7. Verify

After reboot:

```bash
# custom driver should be loaded, in-kernel driver absent
lsmod | grep -E '88x2bu|rtw'

# AP should be active
systemctl status hostapd

# wlan1 should be UP with IP 10.20.1.1
ip addr show wlan1

# hostapd should report state=ENABLED
sudo hostapd_cli status | grep -E 'state|ssid|freq'
```
