"""Local key-delivery emulator; not a QKD device or production ETSI implementation."""
import base64
import json
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class KeyStore:
    def __init__(self, capacity: int = 4, key_size_bytes: int = 32,
                 qber_limit: float = 0.11):
        if capacity < 0 or key_size_bytes < 1 or not 0 <= qber_limit <= 1:
            raise ValueError("invalid key store parameters")
        self.capacity = capacity
        self.key_size_bytes = key_size_bytes
        self.qber_limit = qber_limit
        self.qber = 0.02
        self.online = True
        self.issued = {}
        self.lock = threading.Lock()

    def status(self):
        with self.lock:
            return {"source_online": self.online, "qber": self.qber,
                    "qber_limit": self.qber_limit,
                    "stored_key_count": self.capacity,
                    "key_size_bits": 8 * self.key_size_bytes}

    def take(self, sender: str, receiver: str, number: int):
        with self.lock:
            if not self.online:
                raise RuntimeError("key source offline")
            if self.qber > self.qber_limit:
                raise RuntimeError("QBER above local policy threshold")
            if number < 1 or number > 10:
                raise ValueError("number must be between 1 and 10")
            if number > self.capacity:
                raise RuntimeError("insufficient key stock")
            result = []
            for _ in range(number):
                key_id = str(uuid.uuid4())
                key = base64.b64encode(secrets.token_bytes(self.key_size_bytes)).decode("ascii")
                self.issued[key_id] = (sender, receiver, key)
                result.append({"key_ID": key_id, "key": key})
            self.capacity -= number
            return result

    def receive(self, sender: str, receiver: str, key_id: str):
        with self.lock:
            record = self.issued.get(key_id)
            if record is None or record[:2] != (sender, receiver):
                raise KeyError("unknown key or wrong endpoint pair")
            self.issued.pop(key_id)
            return {"key_ID": key_id, "key": record[2]}


def make_handler(store: KeyStore):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Never print key material; suppress default access logging in the lesson.
            pass

        def respond(self, status, payload):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlparse(self.path)
            parts = path.path.strip("/").split("/")
            if len(parts) != 5 or parts[:3] != ["api", "v1", "keys"]:
                return self.respond(404, {"error": "route not found"})
            peer, action = parts[3:]
            caller = self.headers.get("X-SAE-ID", "").strip()
            if not caller or caller == peer:
                return self.respond(400, {"error": "X-SAE-ID and distinct peer required"})
            query = parse_qs(path.query)
            try:
                if action == "status":
                    return self.respond(200, store.status())
                if action == "enc_keys":
                    number = int(query.get("number", ["1"])[0])
                    return self.respond(200, {"keys": store.take(caller, peer, number)})
                if action == "dec_keys":
                    key_id = query.get("key_ID", [""])[0]
                    if not key_id:
                        raise ValueError("key_ID required")
                    return self.respond(200, {"keys": [store.receive(peer, caller, key_id)]})
                return self.respond(404, {"error": "route not found"})
            except ValueError as error:
                return self.respond(400, {"error": str(error)})
            except KeyError as error:
                return self.respond(404, {"error": str(error)})
            except RuntimeError as error:
                return self.respond(503, {"error": str(error)})

    return Handler


def serve_local(store: KeyStore, port: int = 0):
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))


if __name__ == "__main__":
    server = serve_local(KeyStore(), 8080)
    print("Educational key API on http://127.0.0.1:8080; stop with Ctrl+C")
    server.serve_forever()
