"""
Section 8 — Minodu app

Run standalone:
  pyinfra inventory.py 08_minodu_app.py
"""

import io

from vars import _env_content, install_llm, minodu_repo  # noqa: F401

from pyinfra.operations import apt, files, server, python

if minodu_repo:

    if install_llm:
        # server.shell(
        #     name="Update RAG embeddings (runs in background, takes a few hours)",
        #     commands=[
        #         "su - pi -c 'cd /home/pi/minodu && nohup npm run sync:rag > /home/pi/rag_build.log 2>&1 < /dev/null &'",
        #     ],
        # )

        server.shell(
            name="Update RAG embeddings (runs in background, takes a few hours)",
            commands=[
                "systemd-run --uid=pi --gid=pi "
                "--working-directory=/home/pi/minodu "
                "--unit=rag-sync --collect "
                "bash -lc 'npm run sync:rag'",
            ],
        )

    def print_summary(state, host):
        print("""
        =============================================
        Deployment finished successfully!
              
        If you have choosen to install the llm. the vector database is now beeing build.
        Dont turn of your pi for a few hours. 
        You can check its success on the pi by logging in via ssh 
        and running `systemctl status rag-sync` to see its status.
        The service will dissapear once it build the whole database.
              
        You can rerun the building of the rag database by running:
        pyinfra @ssh/minodupi.local 09_build_rag_db.py -v --ssh-user="pi" --ssh-password="raspberry"
        
        The minodu app is available on http://minodupi.local.
        The backoffice can be found on http://minodupi.local:8080.
        The raspap config to change your network settings can be found here: 
        http://minodupi.local:81
        =================
        ============================
        """)
    
    python.call(
        name="Print final deployment summary",
        function=print_summary,
    )
