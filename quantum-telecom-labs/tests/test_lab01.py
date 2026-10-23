import unittest

from lab01.link_budget import Link


class LinkTests(unittest.TestCase):
    def test_budget_units_and_margin(self):
        link = Link(distance_km=40)
        self.assertAlmostEqual(link.physical_loss_db, 9.2)
        self.assertAlmostEqual(link.planned_loss_db, 12.2)

    def test_distance_reduces_counts_and_increases_dark_noise_share(self):
        near, far = Link(distance_km=0), Link(distance_km=100)
        self.assertGreater(near.raw_clicks_per_second, far.raw_clicks_per_second)
        self.assertLess(near.qber_estimate, far.qber_estimate)

    def test_zero_photons_leaves_only_random_dark_clicks(self):
        link = Link(transmitter_mean_photons=0)
        self.assertAlmostEqual(link.qber_estimate, 0.5)
        self.assertAlmostEqual(link.raw_clicks_per_second, 1)

    def test_bad_parameters_rejected(self):
        with self.assertRaises(ValueError):
            Link(detector_efficiency=1.2)


if __name__ == "__main__":
    unittest.main()
