"""Testy sdíleného čtení konfigurace."""

from __future__ import annotations

from pathlib import Path

from ttp_common.config import env_bool, env_int, resolve_target


class TestResolveTarget:
    def test_s_target_dir(self, monkeypatch):
        monkeypatch.setenv("TARGET_DIR", r"C:\temp\TTP")
        assert resolve_target("TTP SŽ") == Path(r"C:\temp\TTP") / "TTP SŽ"

    def test_bez_target_dir_fallback(self, monkeypatch):
        monkeypatch.delenv("TARGET_DIR", raising=False)
        assert resolve_target("TTP ŽSR") == Path(".") / "TTP ŽSR"


class TestEnvHelpers:
    def test_env_bool_varianty(self, monkeypatch):
        for val in ("1", "true", "ANO", "on"):
            monkeypatch.setenv("X", val)
            assert env_bool("X", False) is True
        monkeypatch.setenv("X", "0")
        assert env_bool("X", True) is False

    def test_env_bool_default(self, monkeypatch):
        monkeypatch.delenv("X", raising=False)
        assert env_bool("X", True) is True

    def test_env_int(self, monkeypatch):
        monkeypatch.setenv("N", "12")
        assert env_int("N", 6) == 12
        monkeypatch.setenv("N", "nesmysl")
        assert env_int("N", 6) == 6
