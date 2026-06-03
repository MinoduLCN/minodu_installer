# minodu-installer

## Setup Raspberry Pi

* install Raspberry Pi OS Lite (64 bit) on Raspberry Pi. *Tested with this version: https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-04-21/* 
    * create user: pi
    * wlan can be left disabled
    * enable ssh access and set hostname to minodupi.local
* connect via ethernet cable to raspberry pi and enable internet Sharing to the Ethernet port on mac
* make sure `ping minodupi.local` returns an answer, meaning your machine can discover the raspberry pi in the network

## Configure minodupi and install system

* open terminal and run:
    ```
    pip install pyinfra
    # run install script (adapt password if you used another one) 
    pyinfra inventory.py deploy.py -v --ssh-user="pi" --ssh-password="raspberry"
    ```
* follow installation instructions


## Manual Setup Instructions

Read [SETUP.md](SETUP.md).

## Troubleshooting

* Make sure raspberrpi is reachable with `ping minodupi.local`. If not. reinstall image and make sure to set the hostname to minodupi.local
* Make sure ssh is enabled, test with `ssh pi@minodupi.local`. Default password is *raspberry*. If it is not working reinstall image and enable ssh access.
* Make sure your macbook is connected to the internet during the install procedure.

