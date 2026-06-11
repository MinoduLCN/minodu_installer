"""
Section 7 — Ollama setup

Run standalone:
  pyinfra inventory.py 07_ollama.py
"""

import io

from vars import install_llm  # noqa: F401

from pyinfra.operations import files, server, systemd

if install_llm:
    server.shell(
        name="Wait for systemd to finish booting",
        commands=["systemctl is-system-running --wait || true"],
    )
    
    server.shell(
        name="Install ollama",
        commands=[
            "command -v ollama >/dev/null 2>&1 || curl -fsSL https://ollama.com/install.sh | sh",
        ]
    )

    files.directory(
        name="Create ollama systemd override directory",
        path="/etc/systemd/system/ollama.service.d",
        mode="755",
    )

    files.put(
        name="Configure ollama (bind to all interfaces, pin to CPU cores 0-2)",
        src=io.BytesIO(
            b'[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0:11434"\nCPUAffinity=0 1 2\n'
        ),
        dest="/etc/systemd/system/ollama.service.d/override.conf",
        mode="644",
    )

    systemd.service(
        name="Enable and restart ollama with new config",
        service="ollama",
        running=True,
        enabled=True,
        daemon_reload=True,
        restarted=True,
    )

    server.shell(
        name="Pull ollama models",
        commands=[
            "ollama pull llama3.2:1b",
            "ollama pull nomic-embed-text",
            "ollama pull all-minilm:l6-v2",
        ]
    )
