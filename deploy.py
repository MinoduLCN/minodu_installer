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

Individual sections:
  pyinfra inventory.py 01_system_packages.py
  pyinfra inventory.py 02_wlan_driver.py
  pyinfra inventory.py 03_raspap.py
  pyinfra inventory.py 04_ap_config.py
  pyinfra inventory.py 05_captive_portal.py
  pyinfra inventory.py 06_scripts_services.py
  pyinfra inventory.py 07_ollama.py
  pyinfra inventory.py 08_minodu_app.py
"""

from pyinfra import local

from vars import *  # noqa: F401,F403 — triggers prompts once; cached for all includes

local.include("01_system_packages.py")
local.include("02_wlan_driver.py")
local.include("03_raspap.py")
local.include("04_captive_portal.py")
local.include("05_scripts_services.py")
local.include("06_ollama.py")
local.include("07_minodu_app.py")
