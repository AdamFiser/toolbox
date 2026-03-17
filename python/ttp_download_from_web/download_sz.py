from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import os, re, time, zipfile, io, unicodedata, urllib.parse, sys
from datetime import datetime
from collections import deque
from save_auth import save_auth

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- Nastavení ---
BASE_TTP_URL = "https://provoz.spravazeleznic.cz/Portal/ViewArticle.aspx?oid=5931"  # kořen TTP
AUTH_STATE_FILE = "auth_spravazeleznic.json"
OUT_BASE = os.path.join("SZ_TTP", datetime.now().strftime("%Y%m%d"))
REQUEST_THROTTLE = 0.05
EXCLUDED_MENU_TITLES = {"xml"}  # ignorovat větve "XML"

# přesné pravidlo: suffix "_xml" před příponou, typicky *_xml.zip
XML_SUFFIX_RE = re.compile(r"_xml$", re.IGNORECASE)

DIACRITICS_CHARS = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"


# --- Pomocné logování ---
def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


# --- Utility ---
def sanitize(s: str) -> str:
    s = re.sub(r"[\\/*?\"<>|:]", "_", s or "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "")


def strip_diacritics(s: str) -> str:
    # odstraní diakritiku, aby šlo robustně porovnávat "trati" vs "tratí"
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def diacritics_score(s: str) -> int:
    return sum(ch in DIACRITICS_CHARS for ch in (s or ""))


def is_xml_suffix(filename: str) -> bool:
    """
    True, pokud název souboru má suffix "_xml" na STEMu, typicky:
    - xxx_xml.zip
    - xxx_xml.pdf
    - xxx_xml  (bez přípony)
    """
    base = (os.path.basename(filename or "")).strip()
    if not base:
        return False
    stem, _ext = os.path.splitext(base)
    if stem and XML_SUFFIX_RE.search(stem):
        return True
    return bool(XML_SUFFIX_RE.search(base))


def is_body_trati_ttp_zip(filename: str) -> bool:
    """
    True, pokud jde o ZIP, jehož název (bez přípony) končí na 'Body tratí TTP'
    (robustně vůči diakritice a velikosti písmen).
    """
    base = (os.path.basename(filename or "")).strip()
    if not base:
        return False
    stem, ext = os.path.splitext(base)
    if ext.lower() != ".zip":
        return False

    stem_norm = strip_diacritics(stem).casefold().strip()
    target = strip_diacritics("Body tratí TTP").casefold()

    return stem_norm.endswith(target)


def parse_cd_filename(header: str) -> str | None:
    """Vytáhne jméno z Content-Disposition, vč. RFC5987."""
    if not header:
        return None
    m = re.search(r"filename\*\s*=\s*([^']+)''([^;]+)", header, flags=re.I)
    if m:
        enc = m.group(1).strip().lower()
        raw = m.group(2).strip()
        try:
            return nfc(urllib.parse.unquote(raw, encoding=enc, errors="replace"))
        except Exception:
            return nfc(urllib.parse.unquote(raw, encoding="utf-8", errors="replace"))

    m = re.search(r'filename\s*=\s*"([^"]+)"', header, flags=re.I)
    if not m:
        m = re.search(r"filename\s*=\s*([^;]+)", header, flags=re.I)
    if m:
        raw_str = m.group(1).strip().strip("'").strip('"')
        cands = [raw_str]
        try:
            b = raw_str.encode("latin-1", errors="replace")
            for enc in ("utf-8", "cp1250", "iso-8859-2"):
                try:
                    cands.append(b.decode(enc))
                except Exception:
                    pass
        except Exception:
            pass
        return nfc(max(cands, key=diacritics_score))
    return None


def choose_best_filename(cd_name: str | None, link_text: str | None) -> str:
    """Vybere jméno s lepší diakritikou; při rovnosti delší variantu."""
    a = nfc((cd_name or "").strip())
    b = nfc((link_text or "").strip())
    if not a and b:
        return b
    if not b and a:
        return a
    if diacritics_score(b) > diacritics_score(a):
        return b
    if diacritics_score(a) > diacritics_score(b):
        return a
    return b if len(b) > len(a) else a


def infer_ext_from_headers(headers: dict, fallback_name: str) -> str:
    cd = headers.get("content-disposition") or headers.get("Content-Disposition")
    if cd:
        cd_fn = parse_cd_filename(cd)
        if cd_fn:
            ext = os.path.splitext(cd_fn)[1]
            if ext:
                return ext
    ctype = (headers.get("content-type") or headers.get("Content-Type") or "").lower()
    if "zip" in ctype:
        return ".zip"
    if "pdf" in ctype:
        return ".pdf"
    if (fallback_name or "").lower().endswith(".pdf"):
        return ".pdf"
    return ""


def is_excluded_item(item: dict) -> bool:
    label = (item.get("label") or "").strip().lower()
    if label in EXCLUDED_MENU_TITLES:
        return True
    for p in item.get("path", []):
        if (p or "").strip().lower() in EXCLUDED_MENU_TITLES:
            return True
    return False


# --- Menu parsování ---
def read_leftmenu_ttp_tree(page):
    js = r"""
    (() => {
      const root = document.querySelector('#leftnav .leftmenu');
      if (!root) return [];
      function absUrl(href) {
        try { return new URL(href, window.location.href).href; }
        catch { return href; }
      }
      const ttpA = root.querySelector('a[href*="ViewArticle.aspx?oid=5931"]');
      if (!ttpA) return [];
      const ttpLi = ttpA.closest('li');
      if (!ttpLi) return [];
      const seenLi = new Set(), items = [];
      function directA(li) {
        return li.querySelector(':scope > a, :scope > a.current, :scope > a.subcurrent');
      }
      function labelOf(li) {
        const a = directA(li);
        return a ? (a.textContent || "").trim() : "";
      }
      function urlOf(li) {
        const a = directA(li);
        const href = a ? a.getAttribute('href') : null;
        if (!href) return null;
        if (!href.includes('ViewArticle.aspx?oid=')) return null;
        return absUrl(href);
      }
      function childULs(li) {
        const arr = [];
        li.querySelectorAll(':scope > ul').forEach(u => arr.push(u));
        const adj = li.nextElementSibling; // "li + ul"
        if (adj && adj.tagName && adj.tagName.toLowerCase() === 'ul') arr.push(adj);
        return arr;
      }
      function walk(li, pathSoFar) {
        if (!li || seenLi.has(li)) return;
        seenLi.add(li);
        const myLabel = labelOf(li);
        const myUrl = urlOf(li);
        const myPath = pathSoFar.slice();
        if (myLabel) myPath.push(myLabel);
        if (myUrl) items.push({ label: myLabel, url: myUrl, path: myPath.slice() });
        childULs(li).forEach(u => u.querySelectorAll(':scope > li').forEach(cli => walk(cli, myPath)));
      }
      walk(ttpLi, []);
      const seenUrl = new Set(), out = [];
      for (const it of items) {
        if (!it.url) continue;
        if (seenUrl.has(it.url)) continue;
        seenUrl.add(it.url);
        out.push(it);
      }
      return out;
    })()
    """
    return page.evaluate(js)


def find_show_links_with_names(page, context_url: str):
    anchors = page.eval_on_selector_all(
        'a[href*="Show.aspx?oid="]',
        "els => els.map(e => ({href: e.getAttribute('href'), text: (e.textContent || '').trim()}))"
    ) or []
    out = []
    for a in anchors:
        url = urljoin(context_url, (a.get("href") or "").strip())
        name = a.get("text") or "soubor"
        if "Show.aspx?oid=" in url:
            out.append({"url": url, "name": name})
    useen, unique = set(), []
    for it in out:
        if it["url"] in useen:
            continue
        useen.add(it["url"])
        unique.append(it)
    return unique


def build_target_dir(base: str, path_parts: list[str] | None, fallback_label: str) -> str:
    parts = [sanitize(p) for p in (path_parts or []) if p and p.strip()]
    if not parts:
        parts = [sanitize(fallback_label)]
    return os.path.join(base, *parts)


# --- Stahování ---
def download_via_context(context, url: str, suggested_name: str, target_dir: str):
    log(f"      → GET {url}")
    r = context.request.get(url)
    if not r.ok:
        log(f"      ⚠ HTTP {r.status}: {url}")
        return

    headers, body = r.headers, r.body()
    cd_name = parse_cd_filename(headers.get("content-disposition") or headers.get("Content-Disposition"))
    base_name = sanitize(choose_best_filename(cd_name, suggested_name))

    ext = os.path.splitext(base_name)[1]
    if not ext:
        ext = infer_ext_from_headers(headers, base_name) or ""
        base_name += ext

    # ✅ nepouštět *_xml.zip (suffix _xml)
    if is_xml_suffix(base_name):
        log(f"      ⏭ přeskočeno (suffix _xml): {base_name}")
        return

    # ✅ nepouštět ZIP, který končí na "Body tratí TTP"
    if is_body_trati_ttp_zip(base_name):
        log(f"      ⏭ přeskočeno (ZIP: Body tratí TTP): {base_name}")
        return

    out_path = os.path.join(target_dir, base_name)

    with open(out_path, "wb") as f:
        f.write(body)

    if out_path.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                zf.extractall(target_dir)

            os.remove(out_path)
            log(f"    ✅ rozbaleno ({base_name})")
        except zipfile.BadZipFile:
            log(f"      ⚠ soubor má .zip, ale nejde rozbalit: {base_name}")
    else:
        log(f"      ✅ uloženo: {base_name}")

# --- Main ---
def main():
    log("Start skriptu")
    if not os.path.exists(AUTH_STATE_FILE):
        log("🔐 Chybí auth stav — přihlašuji se automaticky…")
        save_auth()

    ensure_dir(OUT_BASE)

    with sync_playwright() as p:
        log("Spouštím prohlížeč…")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_STATE_FILE)
        page = context.new_page()

        log(f"Načítám TTP kořen: {BASE_TTP_URL}")
        page.goto(BASE_TTP_URL, wait_until="networkidle")
        page.wait_for_selector("#leftnav .leftmenu", timeout=15000)
        #time.sleep(REQUEST_THROTTLE)

        log("Skenuji strom menu…")
        items = [it for it in (read_leftmenu_ttp_tree(page) or []) if not is_excluded_item(it)]
        log(f"🌲 Načteno {len(items)} položek z menu (po filtraci XML).")

        # ✅ procházení větví (BFS) – původní funkční chování
        collected = {it["url"]: it for it in items}
        to_visit = deque(collected.keys())
        visited = set()

        while to_visit:
            url = to_visit.popleft()
            if url in visited:
                continue
            visited.add(url)

            log(f"🔎 Procházím stránku {url} ({len(visited)}/{len(collected)})…")
            page.goto(url, wait_until="networkidle")
            try:
                page.wait_for_selector("#leftnav .leftmenu", timeout=10000)
            except Exception:
                log("  ⚠ levé menu nenačteno (pokračuji)")
            #time.sleep(REQUEST_THROTTLE)

            more = [it for it in (read_leftmenu_ttp_tree(page) or []) if not is_excluded_item(it)]
            for it in more:
                if it["url"] not in collected:
                    collected[it["url"]] = it
                    to_visit.append(it["url"])

        all_items = list(collected.values())
        log(f"📦 Celkem TTP položek ke stažení: {len(all_items)}")

        for i, it in enumerate(all_items, start=1):
            target_dir = build_target_dir(OUT_BASE, it.get("path"), it.get("label"))
            ensure_dir(target_dir)

            log(f"\n📁 ({i}/{len(all_items)}) {os.path.relpath(target_dir, OUT_BASE)}")
            page.goto(it["url"], wait_until="networkidle")
            #time.sleep(REQUEST_THROTTLE)

            show_links = find_show_links_with_names(page, it["url"])
            log(f"  📑 nalezeno Show.aspx odkazů: {len(show_links)}")

            for idx, link in enumerate(show_links, start=1):
                suggested = sanitize(link["name"] or "soubor")

                # rychlé filtry už z názvu odkazu (hlavní filtr je i po CD v download_via_context)
                if is_xml_suffix(suggested):
                    log(f"    ({idx}/{len(show_links)}) ⏭ přeskočeno (suffix _xml): {suggested}")
                    continue
                if is_body_trati_ttp_zip(suggested):
                    log(f"    ({idx}/{len(show_links)}) ⏭ přeskočeno (ZIP: Body tratí TTP): {suggested}")
                    continue

                log(f"    ({idx}/{len(show_links)}) ⬇ stahuji: {suggested}")
                download_via_context(context, link["url"], suggested, target_dir)
                #time.sleep(REQUEST_THROTTLE)

        browser.close()
        log(f"\n✅ Hotovo. Výstup v: {os.path.abspath(OUT_BASE)}")


if __name__ == "__main__":
    main()
