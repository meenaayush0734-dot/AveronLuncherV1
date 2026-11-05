# Averon Admin Backend (Flask)
Admin username: EliteShorter. Password is NOT in code; you set it as a hash.

1. pip install -r requirements.txt
2. python make_hash.py   (type your password, copy the hash)
3. Set env vars:
   ADMIN_PASSWORD_HASH=<hash>   SECRET_KEY=<any long random text>
4. python app.py   -> open http://localhost:5000
Deploy free on Render / Railway / PythonAnywhere. Always use HTTPS in production.
Put that URL in AveronApi.BASE_URL in the Android app.
