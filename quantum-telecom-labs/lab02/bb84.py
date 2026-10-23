"""Prepare-and-measure BB84 toy model with intercept-resend and channel noise."""
import argparse
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Trial:
    sent: int
    sifted: int
    errors: int
    alice_sample: tuple[int, ...]
    bob_sample: tuple[int, ...]

    @property
    def qber(self) -> float:
        return self.errors / self.sifted if self.sifted else 0.0


def measure(bit: int, prepared_basis: int, measured_basis: int, rng: random.Random) -> int:
    return bit if prepared_basis == measured_basis else rng.randrange(2)


def run(n: int = 10000, noise: float = 0.0, intercept: bool = False,
        seed: int = 2026) -> Trial:
    if n < 1 or not 0 <= noise <= 1:
        raise ValueError("n must be positive and noise must be between 0 and 1")
    rng = random.Random(seed)
    alice, bob = [], []
    for _ in range(n):
        a_bit, a_basis, b_basis = rng.randrange(2), rng.randrange(2), rng.randrange(2)
        transmitted_bit, transmitted_basis = a_bit, a_basis
        if intercept:
            eve_basis = rng.randrange(2)
            transmitted_bit = measure(a_bit, a_basis, eve_basis, rng)
            transmitted_basis = eve_basis
        b_bit = measure(transmitted_bit, transmitted_basis, b_basis, rng)
        if rng.random() < noise:
            b_bit ^= 1
        if a_basis == b_basis:
            alice.append(a_bit)
            bob.append(b_bit)
    return Trial(n, len(alice), sum(a != b for a, b in zip(alice, bob)),
                 tuple(alice[:12]), tuple(bob[:12]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pulses", type=int, default=10000)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--intercept", action="store_true")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    trial = run(args.pulses, args.noise, args.intercept, args.seed)
    print(f"sent={trial.sent} sifted={trial.sifted} errors={trial.errors} QBER={trial.qber:.2%}")
    print(f"Alice sample: {trial.alice_sample}")
    print(f"Bob sample:   {trial.bob_sample}")
    print("This is a sifted-key experiment, not a secure final key.")


if __name__ == "__main__":
    main()
