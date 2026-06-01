# minodu-installer

## Setup Raspberry Pi

* install Raspberry Pi OS Lite (64 bit) on Raspberry Pi. *Tested with this version: https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-04-21/*
* enable ssh access and set hostname to minodupi.local
* connect via ethernet cable to raspberry pi and enable internet Sharing to the Ethernet port on mac

## Configure MinoduPi

* open terminal and run:
    ```
    pip install pyinfra
    pyinfra inventory.py deploy.py
    ```
* follow installation instructions


## Manual Setup Instructions

Setup Guide: [SETUP.md](SETUP.md)

