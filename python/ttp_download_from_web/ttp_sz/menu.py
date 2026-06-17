"""Parsování levého navigačního menu portálu SŽ a odkazů na soubory.

JavaScript běžící v prohlížeči je izolovaný zde. Funkce vyžadují živou
Playwright ``page`` a nejsou tedy unit-testovatelné bez prohlížeče.
"""

from __future__ import annotations

import os
from urllib.parse import urljoin

from .naming import sanitize

# JS, který projde podstrom „TTP“ levého menu a vrátí seznam položek s URL.
_LEFTMENU_JS = r"""
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


def read_leftmenu_ttp_tree(page) -> list[dict]:
    """Vrátí položky podstromu „TTP“ z levého menu (label, url, path)."""
    return page.evaluate(_LEFTMENU_JS)


def find_show_links_with_names(page, context_url: str) -> list[dict]:
    """Najde na stránce odkazy ``Show.aspx?oid=`` s textem (názvem souboru)."""
    anchors = page.eval_on_selector_all(
        'a[href*="Show.aspx?oid="]',
        "els => els.map(e => ({href: e.getAttribute('href'), text: (e.textContent || '').trim()}))",
    ) or []
    out = []
    for a in anchors:
        url = urljoin(context_url, (a.get("href") or "").strip())
        name = a.get("text") or "soubor"
        if "Show.aspx?oid=" in url:
            out.append({"url": url, "name": name})

    seen, unique = set(), []
    for it in out:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        unique.append(it)
    return unique


def build_target_dir(base, path_parts: list[str] | None, fallback_label: str) -> str:
    """Sestaví cílový adresář z cesty v menu (sanitizované části)."""
    parts = [sanitize(p) for p in (path_parts or []) if p and p.strip()]
    if not parts:
        parts = [sanitize(fallback_label)]
    return os.path.join(str(base), *parts)
