import smtplib
import os

def load_env():
    env_path = ".env"
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

env = load_env()
user = env.get("SMTP_USER", "")
password = env.get("SMTP_PASSWORD", "")
host = env.get("SMTP_HOST", "smtp.gmail.com")
port = int(env.get("SMTP_PORT", 587))

print(f"Testing SMTP authentication for: {user}")
try:
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        print("SUCCESS: SMTP Authentication Succeeded (235 Authentication Successful)!")
except Exception as e:
    print("SMTP AUTH ERROR:", e)
