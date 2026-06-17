"""Testy čistých funkcí pro práci s názvy souborů."""

from __future__ import annotations

from ttp_sz.naming import (
    choose_best_filename,
    diacritics_score,
    infer_ext_from_headers,
    parse_cd_filename,
    sanitize,
    strip_diacritics,
)


class TestSanitize:
    def test_nahrazuje_nepovolene_znaky(self):
        assert sanitize('a/b\\c:d*e?f"g<h>i|j') == "a_b_c_d_e_f_g_h_i_j"

    def test_sjednoti_bile_znaky(self):
        assert sanitize("  a   b\t c ") == "a b c"

    def test_prazdny_vstup(self):
        assert sanitize("") == ""
        assert sanitize(None) == ""


class TestStripDiacritics:
    def test_odstrani_ceskou_diakritiku(self):
        assert strip_diacritics("Příliš žluťoučký kůň") == "Prilis zlutoucky kun"

    def test_bez_diakritiky_beze_zmeny(self):
        assert strip_diacritics("Body trati TTP") == "Body trati TTP"


class TestDiacriticsScore:
    def test_pocita_diakritiku(self):
        assert diacritics_score("tratí") == 1
        assert diacritics_score("trati") == 0
        assert diacritics_score("ŘŠŽ") == 3


class TestParseCdFilename:
    def test_rfc5987(self):
        h = "attachment; filename*=utf-8''Tabulky%20trat%C3%AD.pdf"
        assert parse_cd_filename(h) == "Tabulky tratí.pdf"

    def test_klasicke_filename_v_uvozovkach(self):
        h = 'attachment; filename="seznam.pdf"'
        assert parse_cd_filename(h) == "seznam.pdf"

    def test_filename_bez_uvozovek(self):
        h = "attachment; filename=seznam.zip"
        assert parse_cd_filename(h) == "seznam.zip"

    def test_prazdna_hlavicka(self):
        assert parse_cd_filename(None) is None
        assert parse_cd_filename("") is None


class TestChooseBestFilename:
    def test_preferuje_bohatsi_diakritiku(self):
        assert choose_best_filename("trati.pdf", "tratí.pdf") == "tratí.pdf"

    def test_pri_rovnosti_delsi(self):
        assert choose_best_filename("a.pdf", "abc.pdf") == "abc.pdf"

    def test_jedno_prazdne(self):
        assert choose_best_filename("", "x.pdf") == "x.pdf"
        assert choose_best_filename("x.pdf", "") == "x.pdf"


class TestInferExtFromHeaders:
    def test_z_content_disposition(self):
        h = {"content-disposition": 'attachment; filename="a.zip"'}
        assert infer_ext_from_headers(h, "neco") == ".zip"

    def test_z_content_type_zip(self):
        h = {"content-type": "application/zip"}
        assert infer_ext_from_headers(h, "neco") == ".zip"

    def test_z_content_type_pdf(self):
        h = {"content-type": "application/pdf"}
        assert infer_ext_from_headers(h, "neco") == ".pdf"

    def test_fallback_z_nazvu(self):
        assert infer_ext_from_headers({}, "dokument.pdf") == ".pdf"

    def test_nic_nenalezeno(self):
        assert infer_ext_from_headers({}, "dokument") == ""
