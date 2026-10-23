"""Simplified fiber/QKD receiver model. No security proof or hardware control."""
from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class Link:
    distance_km: float = 40.0
    attenuation_db_km: float = 0.2
    connectors: int = 2
    connector_loss_db: float = 0.5
    splices: int = 2
    splice_loss_db: float = 0.1
    engineering_margin_db: float = 3.0
    transmitter_mean_photons: float = 0.1
    detector_efficiency: float = 0.2
    dark_click_probability: float = 1e-6
    optical_error_probability: float = 0.02
    pulse_rate_hz: float = 1e6

    def __post_init__(self):
        for name in ("distance_km", "attenuation_db_km", "connector_loss_db",
                     "splice_loss_db", "engineering_margin_db", "transmitter_mean_photons",
                     "pulse_rate_hz"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be nonnegative")
        if self.connectors < 0 or self.splices < 0:
            raise ValueError("component counts must be nonnegative")
        for name in ("detector_efficiency", "dark_click_probability", "optical_error_probability"):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")

    @property
    def physical_loss_db(self) -> float:
        return (self.distance_km * self.attenuation_db_km
                + self.connectors * self.connector_loss_db
                + self.splices * self.splice_loss_db)

    @property
    def planned_loss_db(self) -> float:
        return self.physical_loss_db + self.engineering_margin_db

    @property
    def signal_click_probability(self) -> float:
        # Poisson source; margin is planning reserve, not an extra physical attenuator.
        transmission = 10 ** (-self.physical_loss_db / 10)
        return 1 - exp(-self.transmitter_mean_photons * transmission * self.detector_efficiency)

    @property
    def click_probability(self) -> float:
        signal = self.signal_click_probability
        return signal + (1 - signal) * self.dark_click_probability

    @property
    def qber_estimate(self) -> float:
        clicks = self.click_probability
        if clicks == 0:
            return 0.0
        signal = self.signal_click_probability
        dark_only = (1 - signal) * self.dark_click_probability
        return (signal * self.optical_error_probability + 0.5 * dark_only) / clicks

    @property
    def raw_clicks_per_second(self) -> float:
        return self.pulse_rate_hz * self.click_probability


def main() -> None:
    print("distance_km loss_db planned_db clicks_per_s qber_percent")
    for distance in (0, 20, 40, 60, 80, 100):
        link = Link(distance_km=distance)
        print(f"{distance:>11} {link.physical_loss_db:>7.2f} {link.planned_loss_db:>10.2f} "
              f"{link.raw_clicks_per_second:>12.1f} {100*link.qber_estimate:>12.2f}")


if __name__ == "__main__":
    main()
