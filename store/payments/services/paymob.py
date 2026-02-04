import requests
from django.conf import settings

BASE_URL = "https://accept.paymob.com/api"

def get_auth_token():
    res = requests.post(
        f"{BASE_URL}/auth/tokens",
        json={"api_key": settings.PAYMOB_API_KEY}
    )
    return res.json()["token"]