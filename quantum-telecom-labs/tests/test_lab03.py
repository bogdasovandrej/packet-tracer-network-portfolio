import threading
import unittest

from lab03.demo import request
from lab03.service import KeyStore, serve_local


class KeyAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = KeyStore(capacity=3)
        cls.server = serve_local(cls.store)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def setUp(self):
        self.store.capacity = 3
        self.store.issued.clear()
        self.store.qber = 0.02
        self.store.online = True

    def test_pair_receives_same_key_once(self):
        status, body = request(self.base, "bob", "enc_keys", "alice")
        self.assertEqual(status, 200)
        original = body["keys"][0]
        status, body = request(self.base, "alice", "dec_keys", "bob",
                               f"?key_ID={original['key_ID']}")
        self.assertEqual(status, 200)
        self.assertEqual(original, body["keys"][0])
        status, _ = request(self.base, "alice", "dec_keys", "bob",
                            f"?key_ID={original['key_ID']}")
        self.assertEqual(status, 404)

    def test_wrong_peer_cannot_read(self):
        _, body = request(self.base, "bob", "enc_keys", "alice")
        key_id = body["keys"][0]["key_ID"]
        status, _ = request(self.base, "alice", "dec_keys", "mallory", f"?key_ID={key_id}")
        self.assertEqual(status, 404)

    def test_stock_qber_and_outage(self):
        status, _ = request(self.base, "bob", "enc_keys", "alice", "?number=4")
        self.assertEqual(status, 503)
        self.store.qber = 0.2
        status, _ = request(self.base, "bob", "enc_keys", "alice")
        self.assertEqual(status, 503)
        self.store.qber = 0.02
        self.store.online = False
        status, _ = request(self.base, "bob", "enc_keys", "alice")
        self.assertEqual(status, 503)

    def test_status_does_not_expose_keys(self):
        status, body = request(self.base, "bob", "status", "alice")
        self.assertEqual(status, 200)
        self.assertNotIn("key", body)
        self.assertEqual(body["key_size_bits"], 256)


if __name__ == "__main__":
    unittest.main()
