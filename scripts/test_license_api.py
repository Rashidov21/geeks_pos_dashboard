#!/usr/bin/env python3
"""
Litsenziya API ni tekshirish (verify → activate → check-status).

1) Pastdagi o'zgaruvchilarni to'ldiring.
2) Terminalda: python scripts/test_license_api.py
"""

import json
import sys

import requests

# ========== SHU YERNI TO'LDIRING ==========
BASE_URL = "https://pos.geeksandijan.uz"
TOKEN = "cb52532df1c672eb148085f886259abb77487a02"  # DRF token: Authorization: Token ...
CLIENT_KEY = "b7UIBoKRfwJ8wxlup8HFop2DfAhQOa974O_hvKTgd0NcDEiLnbFVz6eoqndiVhZk"  # .env dagi CLIENT_API_KEY bilan bir xil
ACTIVATION_KEY = "0qBMHcqBkrvb01UPm5MH0na8RZtnqroh"
HARDWARE_ID = "22a895c8-47c6-45de-8340-72ec4bdb97a9"
# ==========================================


def main() -> None:
    if not all([TOKEN, CLIENT_KEY, ACTIVATION_KEY, HARDWARE_ID]):
        print("Xato: TOKEN, CLIENT_KEY, ACTIVATION_KEY, HARDWARE_ID ni fayl ichida to'ldiring.", file=sys.stderr)
        sys.exit(1)

    base = BASE_URL.rstrip("/")
    headers = {
        "Authorization": f"Token {TOKEN}",
        "X-CLIENT-KEY": CLIENT_KEY,
        "Content-Type": "application/json",
    }
    meta = {"app_version": "1.0.0", "os": "python-test"}

    def show(name: str, resp: requests.Response) -> None:
        print(name, resp.status_code)
        try:
            print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        except Exception:
            print(resp.text)
        print()

    # 1) Kalitni tekshirish
    r1 = requests.post(
        f"{base}/api/v1/verify-activation-key/",
        headers=headers,
        json={"activation_key": ACTIVATION_KEY},
        timeout=30,
    )
    show("verify-activation-key", r1)

    # 2) Faollashtirish
    r2 = requests.post(
        f"{base}/api/v1/activate/",
        headers=headers,
        json={
            "activation_key": ACTIVATION_KEY,
            "hardware_id": HARDWARE_ID,
            "client_meta": meta,
        },
        timeout=30,
    )
    show("activate", r2)

    # 3) Holat
    r3 = requests.get(
        f"{base}/api/v1/check-status/",
        headers=headers,
        params={"activation_key": ACTIVATION_KEY, "hardware_id": HARDWARE_ID},
        timeout=30,
    )
    show("check-status", r3)

    if r1.status_code >= 400 or r2.status_code >= 400 or r3.status_code >= 400:
        sys.exit(1)


if __name__ == "__main__":
    main()
