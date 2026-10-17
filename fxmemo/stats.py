"""保存した値段と見出しから、ページに載せる事実の数字を作る。予想や売り買いの判断はしない。"""
import re
import statistics
from datetime import date, datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
BIG_MOVE = 0.01      # 1日で1%以上を「大きく動いた日」とする
RECENT_DAYS = 30     # 大きく動いた日を何日さかのぼって載せるか
AFTER = [(1, "1日後"), (5, "1週間後")]  # 営業日の数

OPINION = re.compile(r"見通し(?!通り)|予想|展望|見方|テクニカル|シナリオ|戦略|レンジ|サポート|抵抗|売り・買い要因|一目|均衡表")
NOISE = re.compile(r"四本値")


def _same_story(title):
    """配信先が違うだけの同じ記事をまとめるための目印。"""
    t = re.split(r"[｜|]", title)[0]
    t = re.sub(r"^【[^】]*】|[（(][^）)]*[）)]$|\s", "", t)
    return t[:40]


def _jst_day(iso):
    return datetime.fromisoformat(iso).astimezone(JST).date().isoformat()


def _similar(days, prices, rets, i):
    """i日目と同じ向きに、同じくらい（0.75〜1.33倍）動いた過去の日について、その後どうなったかを数える。"""
    sign = 1 if rets[i] > 0 else -1
    lo, hi = max(BIG_MOVE, abs(rets[i]) * 0.75), abs(rets[i]) * 1.33
    out = {"count": 0, "since": days[1][:4], "lo": lo, "hi": hi, "after": []}
    hits = [j for j in range(1, i) if lo <= rets[j] * sign <= hi and j + AFTER[-1][0] < i]
    out["count"] = len(hits)
    for n, label in AFTER:
        moves = [prices[j + n] / prices[j] - 1 for j in hits]
        if not moves:
            continue
        back = sum(1 for m in moves if m * sign < 0)
        out["after"].append({
            "label": label,
            "back": back,                 # 逆向きに動いた（戻った）回数
            "more": len(moves) - back,    # 同じ向きに続いた回数
            "median": statistics.median(moves),
        })
    return out


def build(holding, rates, headlines, schedule, now):
    days = [d for d, _ in rates]
    prices = [p for _, p in rates]
    rets = [0.0] + [prices[k] / prices[k - 1] - 1 for k in range(1, len(prices))]
    last = len(prices) - 1

    # 見出しを「出来事」と「他の人の見方」に分ける
    events, opinions, seen = [], [], set()
    for h in headlines:
        key = _same_story(h["title"])
        if NOISE.search(h["title"]) or key in seen:
            continue
        seen.add(key)
        (opinions if OPINION.search(h["title"]) else events).append(h)

    by_day = {}
    for h in events:
        by_day.setdefault(_jst_day(h["published"]), []).append(h)

    since = (date.fromisoformat(days[last]) - timedelta(days=RECENT_DAYS)).isoformat()
    big = []
    for i in range(last, 0, -1):
        if days[i] < since:
            break
        if abs(rets[i]) >= BIG_MOVE:
            big.append({
                "date": days[i],
                "ret": rets[i],
                "price": prices[i],
                "prev": prices[i - 1],
                "headlines": by_day.get(days[i], [])[:4],
                "similar": _similar(days, prices, rets, i),
            })

    one_year = [abs(r) for r in rets[-260:]]  # 直近およそ1年（営業日）
    today = now.date().isoformat()
    upcoming = [e for e in schedule["events"] if e["date"] >= today][:4]
    for e in upcoming:
        e["in_days"] = (date.fromisoformat(e["date"]) - now.date()).days

    week = max(0, last - 5)
    return {
        "name": holding["name"],
        "pair": f"{holding['base']}/{holding['quote']}",
        "latest": {
            "date": days[last],
            "price": prices[last],
            "chg_1d": prices[last] - prices[last - 1],
            "ret_1d": rets[last],
            "ret_1w": prices[last] / prices[week] - 1,
        },
        "typical_move": statistics.median(one_year) if one_year else None,
        "big_threshold": BIG_MOVE,
        "big_days": big,
        "events": events[:8],
        "opinions": opinions[:3],
        "upcoming": upcoming,
        "history_from": days[0],
    }
