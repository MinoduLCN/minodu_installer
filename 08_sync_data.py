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
        name="Install sync tool dependencies",
        commands=["su - pi -c 'cd /home/pi/minodu/tools/sync && /home/pi/.local/bin/uv sync'"]
    )

    # server.shell(
    #     name="Renew Backup on server",
    #     commands=[
    #         "su - pi -c 'cd /home/pi/minodu && npm run sync:update_backup'",
    #     ]
    # )

    server.shell(
        name="Stop minodu docker containers",
        commands=["bash -c 'cd /home/pi/minodu && npm run docker:stop'"]
    )

    server.shell(
        name="Change user rights of data directory to pi",
        commands=[
            "chown -R pi:pi /home/pi/minodu/data"
        ]
    )

    server.shell(
        name="Start minodu docker containers",
        commands=["bash -c 'cd /home/pi/minodu && npm run docker:start'"]
    )

    server.shell(
        name="Sync local database with server",
        commands=[
            "su - pi -c 'cd /home/pi/minodu && npm run sync:database'",
        ]
    )

    server.shell(
    name="Post weather data to minodupi API",
    commands=[
        """curl -X 'POST' \
        'http://minodupi.local/api/backend/v1/weather' \
        -H 'accept: */*' \
        -H 'Content-Type: application/json' \
        -d '{
        "temp": 22,
        "temp1": 21.8,
        "hum": 45,
        "hum1": 47.2,
        "press": 1013.25,
        "lux": 320.5,
        "ambient": 215,
        "CO": 0.5,
        "NO2": 12,
        "wind_dir": 12,
        "wind_spd": 12,
        "uv": 12,
        "battery": 12
        }'"""
        ],
    )

    if install_llm:
        server.shell(
            name="Update RAG embeddings (This will take a long time)",
            commands=[
                "su - pi -c 'cd /home/pi/minodu && npm run sync:rag'",
            ]
        )
