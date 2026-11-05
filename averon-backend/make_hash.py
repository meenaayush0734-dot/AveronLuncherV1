# Run: python make_hash.py  -> prints a password hash to put in ADMIN_PASSWORD_HASH
import getpass
from werkzeug.security import generate_password_hash
print(generate_password_hash(getpass.getpass("Choose admin password: ")))
