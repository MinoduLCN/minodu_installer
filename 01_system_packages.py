"""
Section 1 — System packages

Run standalone:
  pyinfra inventory.py 01_system_packages.py
"""

from vars import *  # noqa: F401,F403

from pyinfra.operations import apt, server, systemd

apt.update(name="Update apt cache", cache_time=3600)

apt.packages(
    name="Install build dependencies",
    packages=["git", "build-essential", "dkms", "bc"],
)

server.shell(
    name="Install kernel headers",
    commands=["apt-get install -y linux-headers-$(uname -r)"],
)

server.shell(
    name="Install Docker",
    commands=[
        "command -v docker >/dev/null 2>&1 || curl -sSL https://get.docker.com | sh",
    ]
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
    name="Install git-lfs and npm",
    packages=["git-lfs", "npm"],
)

server.shell(
    name="Install uv for pi user",
    commands=[
        "su - pi -c 'command -v uv >/dev/null 2>&1 || "
        "curl -LsSf https://astral.sh/uv/install.sh | sh'",
    ]
)

server.shell(
    name="Install Python 3.12 via uv",
    commands=[
        "su - pi -c '/home/pi/.local/bin/uv python install 3.12'",
    ]
)
