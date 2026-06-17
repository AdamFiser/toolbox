"""Testy bezpečnostních a čistých částí downloaderu (bez prohlížeče)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from ttp_sz.downloader import _extract_zip, _is_within, _resolve_filename


class TestIsWithin:
    def test_uvnitr(self, tmp_path):
        assert _is_within(tmp_path, tmp_path / "a" / "b.pdf") is True

    def test_mimo_pres_dotdot(self, tmp_path):
        assert _is_within(tmp_path, tmp_path / ".." / "evil.pdf") is False


class TestResolveFilename:
    def test_z_content_disposition(self):
        headers = {"content-disposition": 'attachment; filename="tabulka.pdf"'}
        assert _resolve_filename(headers, "odkaz") == "tabulka.pdf"

    def test_doplni_priponu_z_content_type(self):
        headers = {"content-type": "application/pdf"}
        assert _resolve_filename(headers, "dokument") == "dokument.pdf"


class TestExtractZipBezpecnost:
    def _make_zip(self, members: dict[str, bytes]) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for name, data in members.items():
                zf.writestr(name, data)
        return buf.getvalue()

    def test_rozbali_normalni_cleny(self, tmp_path):
        body = self._make_zip({"a.pdf": b"x", "sub/b.pdf": b"y"})
        _extract_zip(body, tmp_path)
        assert (tmp_path / "a.pdf").read_bytes() == b"x"
        assert (tmp_path / "sub" / "b.pdf").read_bytes() == b"y"

    def test_odmitne_zip_slip(self, tmp_path):
        target = tmp_path / "cil"
        target.mkdir()
        body = self._make_zip({"../evil.pdf": b"hack", "ok.pdf": b"ok"})
        _extract_zip(body, target)
        # Legitimní soubor se rozbalil, únik mimo cílovou složku ne.
        assert (target / "ok.pdf").read_bytes() == b"ok"
        assert not (tmp_path / "evil.pdf").exists()
