from __future__ import annotations

import math

import pytest

from app.services.ingest import decay_risk

TAU = 3600.0


class TestDecayRiskBasic:
    def test_dt_zero_means_no_decay(self):
        assert decay_risk(10.0, 0.0, tau=TAU) == pytest.approx(10.0)

    def test_zero_prev_stays_zero(self):
        assert decay_risk(0.0, 1234.0, tau=TAU) == pytest.approx(0.0)

    def test_decay_is_exponential_at_tau(self):
        result = decay_risk(10.0, TAU, tau=TAU)
        assert result == pytest.approx(10.0 / math.e)

    def test_decay_is_exponential_at_two_tau(self):
        result = decay_risk(10.0, 2 * TAU, tau=TAU)
        assert result == pytest.approx(10.0 / (math.e**2))

    def test_decay_to_near_zero_at_ten_tau(self):
        result = decay_risk(10.0, 10 * TAU, tau=TAU)
        assert result < 0.001
        assert result > 0.0


class TestDecayRiskMonotonicity:
    @pytest.mark.parametrize("prev", [1.0, 5.0, 10.0, 100.0])
    def test_strictly_decreases_with_dt(self, prev: float):
        r0 = decay_risk(prev, 0.0, tau=TAU)
        r1 = decay_risk(prev, TAU / 2, tau=TAU)
        r2 = decay_risk(prev, TAU, tau=TAU)
        r3 = decay_risk(prev, 5 * TAU, tau=TAU)

        assert r0 > r1 > r2 > r3 > 0.0

    def test_proportional_to_prev(self):
        dt = TAU / 3
        assert decay_risk(2.0, dt, tau=TAU) == pytest.approx(
            2 * decay_risk(1.0, dt, tau=TAU)
        )
        assert decay_risk(50.0, dt, tau=TAU) == pytest.approx(
            50 * decay_risk(1.0, dt, tau=TAU)
        )


class TestDecayRiskClockSkew:
    def test_negative_dt_treated_as_zero(self):
        assert decay_risk(10.0, -1.0, tau=TAU) == pytest.approx(10.0)
        assert decay_risk(10.0, -3600.0, tau=TAU) == pytest.approx(10.0)
        assert decay_risk(10.0, -1e9, tau=TAU) == pytest.approx(10.0)

    def test_negative_dt_does_not_amplify(self):
        for dt in (-100.0, -TAU, -1e6):
            assert decay_risk(5.0, dt, tau=TAU) <= 5.0


class TestDecayRiskCustomTau:
    def test_custom_tau_changes_decay_rate(self):
        dt = 600.0
        fast = decay_risk(10.0, dt, tau=300.0)
        slow = decay_risk(10.0, dt, tau=3600.0)
        assert fast < slow

    def test_at_custom_tau_decays_to_one_over_e(self):
        custom_tau = 60.0
        assert decay_risk(10.0, 60.0, tau=custom_tau) == pytest.approx(10.0 / math.e)


class TestDecayRiskNumericStability:
    def test_handles_large_dt_without_overflow(self):
        result = decay_risk(1e6, 1e9, tau=TAU)
        assert result == pytest.approx(0.0, abs=1e-12)

    def test_returns_float(self):
        assert isinstance(decay_risk(1, 1, tau=TAU), float)
        assert isinstance(decay_risk(1.0, 1, tau=TAU), float)
