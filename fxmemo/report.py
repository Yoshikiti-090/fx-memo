"""stats.build の結果から、スマホで読む1枚のページ（docs/index.html）を作る。外部の読み込みは使わない。"""
from datetime import date, datetime, timedelta, timezone
from html import escape

JST = timezone(timedelta(hours=9))
WEEK = "月火水木金土日"


def _d(iso_day):
    d = date.fromisoformat(iso_day)
    return f"{d.month}/{d.day}（{WEEK[d.weekday()]}）"


def _t(iso):
    t = datetime.fromisoformat(iso).astimezone(JST)
    return f"{t.month}/{t.day} {t:%H:%M}"


def _pct(r, sign=True, digits=1):
    return f"{r * 100:+.{digits}f}%" if sign else f"{abs(r) * 100:.{digits}f}%"


def _dir(r):
    # ポンド円が上がる＝円安（ポンド高）。良い悪いの色は付けない（持ち方で意味が変わるため）
    return ("up", "▲ 円安（ポンド高）") if r > 0 else ("down", "▼ 円高（ポンド安）")


def _link(h):
    url = h["link"] if h["link"].startswith("https://") else "#"
    src = f'<span class="src">{escape(h["source"])}</span>' if h["source"] else ""
    return (f'<li class="hl" data-ts="{escape(h["published"])}"><a href="{escape(url)}" target="_blank" rel="noopener">'
            f'{escape(h["title"])}</a><span class="when">{_t(h["published"])}</span>{src}</li>')


def _similar(s, r):
    if not s["count"]:
        return '<p class="muted">同じくらい動いた日は、過去にありません。</p>'
    rows = "".join(
        f'<tr><th>{a["label"]}</th><td>戻った <b>{a["back"]}</b>回</td><td>続いた <b>{a["more"]}</b>回</td>'
        f'<td>真ん中の値 {_pct(a["median"], digits=2)}</td></tr>' for a in s["after"])
    way = "上がった" if r > 0 else "下がった"
    span = f'{_pct(s["lo"], False)}〜{_pct(s["hi"], False)}'
    return (f'<p class="sim-lead">{s["since"]}年からの過去に、1日で{span}{way}日は <b>{s["count"]}回</b>。その後：</p>'
            f'<div class="tbl"><table class="sim">{rows}</table></div>')


def _big_day(b):
    cls, label = _dir(b["ret"])
    hl = "".join(_link(h) for h in b["headlines"]) or '<li class="muted">この日の見出しは保存されていません（見出しはツールを動かし始めた日から貯まります）</li>'
    return f"""
    <article class="day" data-ts="{b['date']}T23:59:59+09:00">
      <header class="day-h"><span class="date">{_d(b['date'])}</span>
        <span class="move {cls}">{label} {_pct(b['ret'])}</span>
        <span class="muted">{b['prev']:.2f} → {b['price']:.2f}円</span></header>
      <h4>同じ日の見出し</h4><ul class="hls">{hl}</ul>
      <h4>過去に似た動きと、その後</h4>{_similar(b['similar'], b['ret'])}
    </article>"""


def _section(p):
    L = p["latest"]
    cls, label = _dir(L["ret_1d"])
    big = "".join(_big_day(b) for b in p["big_days"]) or (
        f'<p class="muted">直近30日に、1日で{_pct(p["big_threshold"], False)}以上動いた日はありません。</p>')
    up = "".join(
        f'<li><span class="date">{_d(e["date"])} {escape(e["time"])}</span>'
        f'<span>{escape(e["title"])}</span><span class="muted">あと{e["in_days"]}日・'
        f'<a href="{escape(e["url"])}" target="_blank" rel="noopener">{escape(e["source"])}の公表</a></span></li>'
        for e in p["upcoming"]) or '<li class="muted">登録された予定はありません</li>'
    ev = "".join(_link(h) for h in p["events"]) or '<li class="muted">見出しはまだありません</li>'
    op = "".join(_link(h) for h in p["opinions"]) or '<li class="muted">見出しはまだありません</li>'
    typical = f'ふだんの1日の動きは {_pct(p["typical_move"], False)} ほど（直近1年の真ん中の値）。' if p["typical_move"] else ""
    return f"""
  <section class="holding">
    <div class="now">
      <div class="pair">{escape(p['name'])}<span>{escape(p['pair'])}</span></div>
      <div class="price">{L['price']:.2f}<small>円</small></div>
      <div class="chg"><span class="move {cls}">{label}</span>
        前の日から {L['chg_1d']:+.2f}円（{_pct(L['ret_1d'])}）・1週間で {_pct(L['ret_1w'])}</div>
      <p class="muted">{_d(L['date'])}の基準の値段（欧州中央銀行・日本時間の夜11時ごろ）。{typical}</p>
    </div>

    <div class="since" id="since" hidden></div>

    <h2>大きく動いた日<span class="h-sub">直近30日・1日で{_pct(p['big_threshold'], False)}以上</span></h2>
    {big}

    <h2>これからの予定</h2>
    <ul class="plan">{up}</ul>

    <h2>最近の出来事の見出し<span class="h-sub">直近7日</span></h2>
    <ul class="hls">{ev}</ul>

    <h2>他の人の見方<span class="h-sub">出典つき・このページの予想ではありません</span></h2>
    <ul class="hls">{op}</ul>
  </section>"""


CSS = """
:root{
  /* 縦1列のスマホ用。上から：今の値段 → 前に開いてから → 大きく動いた日 → 予定 → 見出し */
  --bg:#F3F4F1; --card:#FFFFFF; --ink:#1B2230; --muted:#5E6675; --line:#DADDD8; --soft:#E9ECE6;
  --accent:#1F4E79; --up:#7A4A0E; --up-soft:#F6EBDA; --down:#145A5A; --down-soft:#DCEFEC; --new:#9B2C4B;
  --font:"Hiragino Sans","Noto Sans JP",system-ui,-apple-system,sans-serif;
  color-scheme: light;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:#11151C; --card:#191E27; --ink:#E6E9EE; --muted:#9AA2AF; --line:#2A313C; --soft:#222934;
    --accent:#8DB7E2; --up:#F0C27A; --up-soft:#3A2C17; --down:#7FD1C7; --down-soft:#173331; --new:#F08AA5;
    color-scheme: dark; }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font);font-size:15px;line-height:1.7;
  padding-block:20px 40px;padding-left:max(16px, env(safe-area-inset-left, 0px));padding-right:max(16px, env(safe-area-inset-right, 0px))}
.wrap{max-width:640px;margin:0 auto}
a{color:var(--accent)} a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap}
.top h1{font-size:15px;margin:0;letter-spacing:.08em;color:var(--muted)}
.muted{color:var(--muted);font-size:13px}
.now{margin-top:10px}
.pair{font-size:20px;font-weight:700} .pair span{font-size:12px;color:var(--muted);margin-left:8px;letter-spacing:.06em}
.price{font-size:44px;font-weight:700;line-height:1.1;font-variant-numeric:tabular-nums;margin-top:4px}
.price small{font-size:18px;margin-left:4px}
.chg{font-size:14px;margin-top:6px;font-variant-numeric:tabular-nums}
.move{display:inline-block;font-weight:700;font-size:13px;padding:1px 8px;border-radius:4px;margin-right:6px;font-variant-numeric:tabular-nums}
.move.up{background:var(--up-soft);color:var(--up)} .move.down{background:var(--down-soft);color:var(--down)}
.since{margin-top:16px;padding:12px 14px;border-radius:10px;background:var(--card);border:1px solid var(--line);font-size:14px}
.since b{color:var(--new)}
h2{font-size:17px;margin:30px 0 10px;padding-top:16px;border-top:1px solid var(--line);text-wrap:balance}
.h-sub{display:block;font-size:12px;font-weight:400;color:var(--muted)}
h4{font-size:13px;margin:12px 0 4px;color:var(--muted);font-weight:600;letter-spacing:.04em}
.day{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px}
.day-h{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}
.date{font-weight:700;font-variant-numeric:tabular-nums}
ul{list-style:none;margin:0;padding:0}
.hls li{padding:8px 0;border-bottom:1px solid var(--soft);min-width:0}
.hls li:last-child{border-bottom:0}
.hls a{display:block;text-decoration:none;color:var(--ink);font-size:14px;line-height:1.55}
.hls a:hover{text-decoration:underline}
.when,.src{font-size:12px;color:var(--muted);margin-right:8px;font-variant-numeric:tabular-nums}
.hl.new a::before,.day.new .date::before{content:"新";display:inline-block;font-size:11px;font-weight:700;color:var(--new);border:1px solid var(--new);border-radius:3px;padding:0 4px;margin-right:6px;line-height:1.4}
.plan li{display:grid;gap:2px;padding:8px 0;border-bottom:1px solid var(--soft)}
.sim-lead{font-size:14px;margin:4px 0}
.tbl{overflow-x:auto}
.sim{border-collapse:collapse;font-size:13.5px;font-variant-numeric:tabular-nums;width:100%}
.sim th,.sim td{text-align:left;padding:5px 8px 5px 0;border-bottom:1px solid var(--soft);vertical-align:top}
.sim th{white-space:nowrap}
.sim th{color:var(--muted);font-weight:600}
footer{margin-top:36px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
footer p{margin:4px 0}
"""

JS = """
(function(){
  var KEY="fxmemo:lastVisit", last=null;
  try{ last=localStorage.getItem(KEY); }catch(_){}
  var box=document.getElementById("since");
  if(last){
    var newDays=0,newHl=0;
    document.querySelectorAll("[data-ts]").forEach(function(el){
      if(new Date(el.getAttribute("data-ts"))>new Date(last)){
        el.classList.add("new");
        if(el.classList.contains("day")) newDays++; else newHl++;
      }
    });
    var t=new Date(last);
    var when=(t.getMonth()+1)+"/"+t.getDate()+" "+String(t.getHours()).padStart(2,"0")+":"+String(t.getMinutes()).padStart(2,"0");
    if(box){
      box.textContent="";
      var s=document.createElement("span");
      s.innerHTML="前に開いた "+when+" から：大きく動いた日 <b>"+newDays+"</b>日・新しい見出し <b>"+newHl+"</b>本（「新」の印）";
      box.appendChild(s); box.hidden=false;
    }
  }
  try{ localStorage.setItem(KEY,new Date().toISOString()); }catch(_){}
})();
"""


def render(pages, now):
    body = "".join(_section(p) for p in pages)
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">
<title>ポンド円メモ</title>
<style>{CSS}</style></head>
<body><div class="wrap">
  <div class="top"><h1>ポンド円メモ</h1><span class="muted">更新 {now.month}/{now.day} {now:%H:%M}</span></div>
  {body}
  <footer>
    <p>このページは、起きたことと過去の数字を並べるだけです。売り買いを勧めるものではありません。判断はご自身でしてください。</p>
    <p>値段：<a href="https://frankfurter.dev/" target="_blank" rel="noopener">Frankfurter</a>（欧州中央銀行の基準レート、{escape(pages[0]['history_from'][:4])}年から）。見出し：Google ニュース（各見出しの出典へリンク）。予定：英中銀・日銀の公表。</p>
  </footer>
</div>
<script>{JS}</script>
</body></html>
"""
