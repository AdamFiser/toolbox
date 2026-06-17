"""Testy session/zámků downloaderu (bez sítě a prohlížeče)."""

from __future__ import annotations

import json

from ttp_sz.downloader import DirLocks, build_session


class TestDirLocks:
    def test_stejny_klic_stejny_zamek(self):
        locks = DirLocks()
        a = locks.get("C:/temp/x")
        b = locks.get("C:/temp/x")
        assert a is b

    def test_ruzny_klic_ruzny_zamek(self):
        locks = DirLocks()
        assert locks.get("C:/temp/x") is not locks.get("C:/temp/y")


class TestBuildSession:
    def test_nacte_cookies_ze_storage_state(self, tmp_path):
        state = {
            "cookies": [
                {"name": "sid", "value": "abc", "domain": "provoz.example.cz", "path": "/"},
            ],
            "origins": [],
        }
        p = tmp_path / "auth.json"
        p.write_text(json.dumps(state), encoding="utf-8")

        session = build_session(p)
        assert session.cookies.get("sid") == "abc"
        assert "User-Agent" in session.headers
