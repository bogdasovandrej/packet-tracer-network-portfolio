import unittest

from lab02.bb84 import run


class BB84Tests(unittest.TestCase):
    def test_ideal_channel_has_no_errors(self):
        trial = run(n=10000)
        self.assertEqual(trial.errors, 0)
        self.assertTrue(4500 < trial.sifted < 5500)

    def test_intercept_resend_approaches_quarter_qber(self):
        trial = run(n=100000, intercept=True)
        self.assertTrue(0.23 < trial.qber < 0.27, trial.qber)

    def test_channel_noise_is_measured(self):
        trial = run(n=100000, noise=0.05)
        self.assertTrue(0.04 < trial.qber < 0.06, trial.qber)

    def test_seed_reproduces_result(self):
        self.assertEqual(run(n=100, seed=12), run(n=100, seed=12))

    def test_bad_parameters_rejected(self):
        with self.assertRaises(ValueError):
            run(n=0)


if __name__ == "__main__":
    unittest.main()
