# ポンド円メモ

持っている通貨（ポンド円）について、起きたことと過去の数字だけを並べるページです。売り買いを勧めるものではありません。

- ページ：https://yoshikiti-090.github.io/fx-memo/
- 30分ごとに GitHub が `run.py` を動かし、`data/` と `docs/index.html` を作り直します（`.github/workflows/update.yml`）。
- 手元で動かす時：`python3 run.py --open`
- 予定は `schedule.json` に、英中銀・日銀の公表を見て年に1回足します。
- 対象を増やす時は `run.py` の `HOLDINGS` に1行足します。

## データの出どころ
- 値段：[Frankfurter](https://frankfurter.dev/)（欧州中央銀行の基準レート。日ごと）
- 見出し：Google ニュース（見出しと元記事へのリンクだけ）
- 予定：英中銀・日銀の公表
