import os
import base64
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("GRAFANA_INSTANCE_ID")
token = os.getenv("GRAFANA_API_TOKEN")

print(f"Instance ID: {username}")
print(f"Token: {token[:20]}...")  # Should show glc_...
print(f"Token length: {len(token)}")

credentials = f"{username}:{token}"
encoded = base64.b64encode(credentials.encode()).decode()
print(f"Basic auth: {encoded[:40]}...")