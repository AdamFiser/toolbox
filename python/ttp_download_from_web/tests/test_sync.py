"""Testy idempotentního syncu do cílové složky."""

from __future__ import annotations

from ttp_common.sync import Action, plan_for_dated, sync_file
from ttp_common.versioning import parse_version


def _v(name: str):
    return parse_version(name)


class TestPlanForDated:
    def test_novy_soubor_bez_existujicich(self):
        plan = plan_for_dated(_v("304C_01_20260618.pdf"), [])
        assert plan.action is Action.WRITE
        assert plan.remove == []

    def test_starsi_verze_se_nahradi(self):
        existing = [_v("304C_01_20260415.pdf")]
        plan = plan_for_dated(_v("304C_01_20260618.pdf"), existing)
        assert plan.action is Action.REPLACE
        assert plan.remove == ["304C_01_20260415.pdf"]

    def test_aktualni_verze_se_preskoci(self):
        existing = [_v("304C_01_20260618.pdf")]
        plan = plan_for_dated(_v("304C_01_20260618.pdf"), existing)
        assert plan.action is Action.SKIP

    def test_novejsi_na_cili_se_preskoci(self):
        existing = [_v("304C_01_20260701.pdf")]
        plan = plan_for_dated(_v("304C_01_20260618.pdf"), existing)
        assert plan.action is Action.SKIP

    def test_jine_soubory_neovlivni(self):
        existing = [_v("304C_02_20260101.pdf"), _v("301A_01_20260101.pdf")]
        plan = plan_for_dated(_v("304C_01_20260618.pdf"), existing)
        assert plan.action is Action.WRITE
        assert plan.remove == []


class TestSyncFileDatovany:
    def test_zapise_novy(self, tmp_path):
        out = sync_file(tmp_path, "304C_01_20260618.pdf", b"data")
        assert out.action is Action.WRITE
        assert (tmp_path / "304C_01_20260618.pdf").read_bytes() == b"data"

    def test_nahradi_starsi_a_smaze(self, tmp_path):
        (tmp_path / "304C_01_20260415.pdf").write_bytes(b"stara")
        out = sync_file(tmp_path, "304C_01_20260618.pdf", b"nova")
        assert out.action is Action.REPLACE
        assert (tmp_path / "304C_01_20260618.pdf").read_bytes() == b"nova"
        assert not (tmp_path / "304C_01_20260415.pdf").exists()
        assert tmp_path / "304C_01_20260415.pdf" in out.removed

    def test_preskoci_aktualni(self, tmp_path):
        (tmp_path / "304C_01_20260618.pdf").write_bytes(b"data")
        out = sync_file(tmp_path, "304C_01_20260618.pdf", b"data")
        assert out.action is Action.SKIP


class TestSyncFileNedatovany:
    def test_zapise_novy(self, tmp_path):
        out = sync_file(tmp_path, "Vysvětlivky.pdf", b"obsah")
        assert out.action is Action.WRITE
        assert (tmp_path / "Vysvětlivky.pdf").read_bytes() == b"obsah"

    def test_identicky_obsah_preskoci(self, tmp_path):
        (tmp_path / "Vysvětlivky.pdf").write_bytes(b"obsah")
        out = sync_file(tmp_path, "Vysvětlivky.pdf", b"obsah")
        assert out.action is Action.SKIP

    def test_zmeneny_obsah_prepise(self, tmp_path):
        (tmp_path / "Vysvětlivky.pdf").write_bytes(b"stara")
        out = sync_file(tmp_path, "Vysvětlivky.pdf", b"nova")
        assert out.action is Action.REPLACE
        assert (tmp_path / "Vysvětlivky.pdf").read_bytes() == b"nova"
