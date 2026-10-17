"""値段と見出しを取りに行き、data/ に保存する。

- 値段：Frankfurter（欧州中央銀行の基準レート。キー不要・商用でも無料・手元保存は公式が推奨）
- 見出し：Google ニュースの検索RSS（見出しと元記事へのリンクだけを使い、本文は写さない）
"""
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from email.utils import parsedate_to_datetime

UA = "fxmemo/0.1 (personal use)"
FIRST_DAY = "1999-01-04"  # 欧州中央銀行の基準レートが始まった日


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _path(data_dir, holding, kind):
    return os.path.join(data_dir, f"{holding['id']}_{kind}.json")


def update_rates(data_dir, holding):
    """日ごとの値段を [(日付, 値段), ...] の古い順で返す。過去分は保存済みを使い、足りない所だけ取る。"""
    path = _path(data_dir, holding, "rates")
    saved = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
    # 最後の日の1週間前から取り直す（遅れて直る値に備える）
    start = FIRST_DAY
    if saved:
        start = (date.fromisoformat(max(saved)) - timedelta(days=7)).isoformat()
    url = (f"https://api.frankfurter.dev/v1/{start}..?"
           + urllib.parse.urlencode({"base": holding["base"], "symbols": holding["quote"]}))
    body = json.loads(_get(url))
    for day, v in body.get("rates", {}).items():
        saved[day] = v[holding["quote"]]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, sort_keys=True)
    return sorted(saved.items())


def load_headlines(data_dir, holding):
    path = _path(data_dir, holding, "headlines")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def update_headlines(data_dir, holding, keep_days=400):
    """新しい見出しを足して、保存済みと合わせて新しい順で返す。古い物は keep_days で捨てる。"""
    q = holding["news_query"] + " when:7d"
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q, "hl": "ja", "gl": "JP", "ceid": "JP:ja"})
    root = ET.fromstring(_get(url))
    items = {h["link"]: h for h in load_headlines(data_dir, holding)}
    for it in root.iter("item"):
        link = (it.findtext("link") or "").strip()
        title = (it.findtext("title") or "").strip()
        source = (it.findtext("source") or "").strip()
        pub = it.findtext("pubDate")
        if not link.startswith("https://") or not title or not pub:
            continue
        if source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        items.setdefault(link, {
            "title": title,
            "source": source,
            "link": link,
            "published": parsedate_to_datetime(pub).isoformat(),
        })
    cutoff = (date.today() - timedelta(days=keep_days)).isoformat()
    rows = sorted((h for h in items.values() if h["published"] >= cutoff),
                  key=lambda h: h["published"], reverse=True)
    with open(_path(data_dir, holding, "headlines"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    return rows
