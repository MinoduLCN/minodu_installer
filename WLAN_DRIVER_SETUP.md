# WLAN Driver Setup for TP-Link AC600 Archer T2U Plus (RTL8822BU)

Newer Raspberry Pi OS versions ship with the in-kernel `rtw88_8822bu` driver, which has a known AP mode bug (TX is silently broken — `hostapd` reports `AP-ENABLED` but beacons are never transmitted and the SSID is invisible to clients). The fix is to install the out-of-tree `88x2bu` driver from morrownr and blacklist the in-kernel one.

## 1. Install build dependencies

```bash
sudo apt update
sudo apt install git build-essential dkms bc linux-headers-$(uname -r)
```

## 2. Build and install the out-of-tree driver

```bash
cd /tmp
git clone --depth=1 https://github.com/morrownr/88x2bu-20210702.git 88x2bu
cd 88x2bu
make -j4
sudo make install
sudo depmod -a
```

## 3. Blacklist the in-kernel driver

```bash
sudo nano /etc/modprobe.d/blacklist-rtw88-8822bu.conf
```

Add:

```
blacklist rtw88_8822bu
blacklist rtw88_8822b
blacklist rtw88_usb
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

# hostapd should report state=ENABLED and ssid=Minodu
sudo hostapd_cli status | grep -E 'state|ssid|freq'
```

Expected output:

```
state=ENABLED
freq=2412
ssid[0]=Minodu
```

A phone or laptop should now see the `Minodu` SSID and be able to connect without a password.

---

## Note: correct hostapd.conf for open network

The config in SETUP.md contains `wpa=none` which is invalid — hostapd expects a numeric value. For an **open (no password) network**, use `wpa=0` and omit all WPA-specific keys:

```
driver=nl80211
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
auth_algs=1
beacon_int=100
ssid=Minodu
channel=1
hw_mode=g
ieee80211n=1
interface=wlan1
wpa=0
country_code=DE
ignore_broadcast_ssid=0
ap_max_inactivity=600
disassoc_low_ack=1
skip_inactivity_poll=1
wmm_enabled=1
```
