import binascii
import getpass
import secrets

from pyinfra import config

config.SUDO = True

print("\nMinodu Pi Installer — Configuration\n")

ssid = input("WiFi SSID [Minodu]: ").strip() or "Minodu"
wlan_country = input("WLAN country code [DE]: ").strip().upper() or "DE"
raspap_password = getpass.getpass("RaspAP admin password [secret]: ").strip() or "secret"
install_llm = (input("Install Minodu LLM (y/n) [y]: ").strip().lower() or "y") == "y"

print()
admin_phone = input("Admin phone number [90000000]: ").strip() or "90000000"
admin_password = getpass.getpass("Admin password [secret]: ").strip() or "secret"
print()

minodu_repo = "https://github.com/MinoduLCN/minodu.git"

_mysql_password = secrets.token_urlsafe(24)
_mysql_root_password = secrets.token_urlsafe(24)
_jwt_secret = secrets.token_urlsafe(32)
_forum_admin_password = secrets.token_urlsafe(16)

_pass_hex = binascii.hexlify(raspap_password.encode()).decode()
_set_pass_php = (
    "<?php\n"
    f"$hash = password_hash(hex2bin('{_pass_hex}'), PASSWORD_DEFAULT);\n"
    "file_put_contents('/etc/raspap/raspap.webgui',\n"
    "    '<?php $userinfo = array(\"admin\" => \"' . $hash . '\"); ?>');\n"
    "echo \"RaspAP password updated.\\n\";\n"
)

_env_content = (
    f"MYSQL_USER=minodu_user\n"
    f"MYSQL_PASSWORD={_mysql_password}\n"
    f"MYSQL_ROOT_PASSWORD={_mysql_root_password}\n"
    f"DB_NAME=minodu\n"
    f"JWT_SECRET_KEY={_jwt_secret}\n"
    f"FORUM_ADMIN_PASSWORD={_forum_admin_password}\n"
    f"ADMIN_PASSWORD={admin_password}\n"
    f"ADMIN_PHONE={admin_phone}\n"
    f"ENVIRONMENT=production\n"
)
