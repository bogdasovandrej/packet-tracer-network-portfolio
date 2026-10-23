"""Run a complete local sender/receiver key exchange through HTTP."""
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from lab03.service import KeyStore, serve_local


def request(base: str, peer: str, action: str, caller: str, query: str = ""):
    req = Request(f"{base}/api/v1/keys/{peer}/{action}{query}",
                  headers={"X-SAE-ID": caller})
    try:
        with urlopen(req, timeout=3) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def main():
    store = KeyStore(capacity=2)
    server = serve_local(store)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status, body = request(base, "bob", "status", "alice")
        print("initial status:", status, body)
        status, body = request(base, "bob", "enc_keys", "alice")
        key = body["keys"][0]
        print("Alice received key ID:", key["key_ID"], "HTTP", status)
        status, received = request(base, "alice", "dec_keys", "bob",
                                   f"?key_ID={key['key_ID']}")
        print("Bob got matching key:", status, received["keys"][0]["key"] == key["key"])
        status, _ = request(base, "alice", "dec_keys", "bob",
                            f"?key_ID={key['key_ID']}")
        print("repeat read rejected:", status)
        store.qber = 0.20
        status, body = request(base, "bob", "enc_keys", "alice")
        print("high QBER blocks delivery:", status, body["error"])
        store.qber = 0.02
        store.online = False
        status, body = request(base, "bob", "enc_keys", "alice")
        print("outage blocks delivery:", status, body["error"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
