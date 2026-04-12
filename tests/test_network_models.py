"""Unit tests for network data models and config."""

from __future__ import annotations

from yoyopy.network.models import (
    GpsCoordinate,
    ModemState,
    ModemPhase,
    SignalInfo,
)


def test_modem_state_defaults():
    """ModemState should have sensible defaults for an uninitialized modem."""
    state = ModemState()
    assert state.phase == ModemPhase.OFF
    assert state.signal is None
    assert state.carrier == ""
    assert state.network_type == ""
    assert state.gps is None


def test_signal_info_bars_mapping():
    """SignalInfo.bars should map raw CSQ 0-31 to 0-4 bars."""
    assert SignalInfo(csq=0).bars == 0
    assert SignalInfo(csq=5).bars == 1
    assert SignalInfo(csq=12).bars == 2
    assert SignalInfo(csq=20).bars == 3
    assert SignalInfo(csq=28).bars == 4
    assert SignalInfo(csq=99).bars == 0  # 99 = not detectable


def test_gps_coordinate_fields():
    """GpsCoordinate should store lat/lng/altitude/speed."""
    coord = GpsCoordinate(lat=48.8566, lng=2.3522, altitude=35.0, speed=0.0)
    assert coord.lat == 48.8566
    assert coord.lng == 2.3522


from yoyopy.config.models import YoyoPodConfig, build_config_model


def test_network_config_defaults():
    """NetworkConfig should be disabled by default with sane defaults."""
    config = build_config_model(YoyoPodConfig, {})
    assert config.network.enabled is False
    assert config.network.serial_port == "/dev/ttyS0"
    assert config.network.baud_rate == 115200
    assert config.network.apn == ""
    assert config.network.gps_enabled is True
    assert config.network.ppp_timeout == 30


def test_network_config_from_yaml_data():
    """NetworkConfig should load from YAML data."""
    data = {"network": {"enabled": True, "apn": "internet", "serial_port": "/dev/ttyAMA0"}}
    config = build_config_model(YoyoPodConfig, data)
    assert config.network.enabled is True
    assert config.network.apn == "internet"
    assert config.network.serial_port == "/dev/ttyAMA0"
