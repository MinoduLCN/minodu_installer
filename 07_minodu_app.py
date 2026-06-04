"""
Section 8 — Minodu app

Run standalone:
  pyinfra inventory.py 08_minodu_app.py
"""

import io

from vars import _env_content, install_llm, minodu_repo  # noqa: F401

from pyinfra.operations import apt, files, server

if minodu_repo:
    server.shell(
        name="Clone minodu repository",
        commands=[
            f"test -d /home/pi/minodu || su - pi -c 'git clone {minodu_repo} /home/pi/minodu'",
        ],
    )

    server.shell(
        name="Pull git-lfs files",
        commands=["su - pi -c 'cd /home/pi/minodu && git lfs pull'"]
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
        commands=["su - pi -c 'cd /home/pi/minodu && npm install'"]
    )

    server.shell(
        name="Build and start Docker services (This will take a while when you run it the first time)",
        commands=["bash -c 'cd /home/pi/minodu && npm run docker:start'"]
    )

    server.shell(
        name="Install sync tool dependencies",
        commands=["su - pi -c 'cd /home/pi/minodu/tools/sync && /home/pi/.local/bin/uv sync'"]
    )

    server.shell(
        name="Sync database",
        commands=[
            "su - pi -c 'cd /home/pi/minodu && npm run sync:database'",
        ]
    )

    if install_llm:
        server.shell(
            name="Update RAG embeddings (This will take a long time)",
            commands=[
                "su - pi -c 'cd /home/pi/minodu && npm run sync:rag'",
            ]
        )
