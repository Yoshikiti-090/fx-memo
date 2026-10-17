"""為替の判断材料ツール：値段と見出しを集める → 大きく動いた日を数える → ページを作る をまとめて実行する。

使い方:
    python3 run.py          # データを取り直して docs/index.html を作り直す
    python3 run.py --open   # 終わったらページをブラウザで開く

売り買いを勧めるものではなく、事実の数字と見出しを並べるだけのツール。
"""
import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

from fxmemo import fetch, report, stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
PAGE_PATH = os.path.join(HERE, "docs", "index.html")
JST = timezone(timedelta(hours=9))

# 持っている物の一覧。あとで暗号資産などを足す時は、ここに1行足す。
HOLDINGS = [
    {
        "id": "GBPJPY",
        "name": "ポンド円",
        "base": "GBP",
        "quote": "JPY",
        # 見出しを探す言葉。持っている物に関係するものだけに絞る
        "news_query": "ポンド円 OR 為替介入 OR 英中銀 OR 日銀 金融政策",
    },
]


def main():
    parser = argparse.ArgumentParser(description="為替の判断材料を集めてページを作ります")
    parser.add_argument("--open", action="store_true", help="終わったらページをブラウザで開く")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now(JST)
    with open(os.path.join(HERE, "schedule.json"), encoding="utf-8") as f:
        schedule = json.load(f)

    pages = []
    for h in HOLDINGS:
        print(f"■ {h['name']}")
        rates = fetch.update_rates(DATA_DIR, h)
        print(f"  値段 {len(rates)} 日分（{rates[0][0]} 〜 {rates[-1][0]}）")
        try:
            headlines = fetch.update_headlines(DATA_DIR, h)
            print(f"  見出し {len(headlines)} 本（保存済みを含む）")
        except Exception as e:  # 見出しが取れなくても値段の分は作る
            print(f"  ！ 見出しの取得に失敗しました: {e}")
            headlines = fetch.load_headlines(DATA_DIR, h)
        pages.append(stats.build(h, rates, headlines, schedule, now))

    os.makedirs(os.path.dirname(PAGE_PATH), exist_ok=True)
    with open(PAGE_PATH, "w", encoding="utf-8") as f:
        f.write(report.render(pages, now))
    print(f"ページを作りました: {PAGE_PATH}")
    if args.open:
        subprocess.run(["open", PAGE_PATH])


if __name__ == "__main__":
    main()
