jp = """\
```
つかいかた:

ホスト
  アラビア部屋建て --yyk 部屋名（デフォルト無制限）
  LN部屋建て -ln 部屋名
  みち部屋建て -michi 部屋名
  爆ラン部屋建て -bakuran 部屋名
  1～6人を募集 --yyk1～6, -ln1～6, -michi1～6, -bakuran1～6（追慕は -kick @名前 のあと他の人の参加で）
  キック（不在時等） -kick @メンション
  爆破する -bakuha 部屋番号（1つしか建ててないときは省略可能）

参加者
  参加する -no 部屋番号（1つしか部屋がないときは省略可能）
  ぬける   -nuke 部屋番号（1つの部屋にしか入ってないときは省略可能）

勝敗報告
  勝ち（ホスト視点） -win（部屋番号が必要なことも。チーム番号ではなく、部屋番号）
  負け（ホスト視点） -lose

情報表示
  プレイヤー情報表示 -info プレイヤー名（部分一致）
  プレイヤー一覧(CSV)取得 -players レーティング種類(arabia, LN, michi, bakuranから選択）
  全体レートに対する位置 -graph1 レーティング種類 プレイヤー名（部分一致）
  レート推移 -graph2 レイティング種類 プレイヤー名（部分一致）
  自動登録の初期レート表示 -getinit
  その可視化 -getinitvisual

移行・移行直後調整用（ひとまずrakou用）
  -register @メンション
  -setrate @メンション レーティング（arabia, LN, michi, bakuran） レートの数

その他
  部屋一覧 -rooms
  無理矢理部屋を消す（干しっぱなし用、管理者使用推奨） -force-bakuha-tekumakumayakonn-tekumakumayakonn 部屋番号
  つかいかたを出す -help
  How to use in English: -help-en
```
プレイヤー一覧ページ: https://warzone.stars.ne.jp/
マニュアル: https://warzone.stars.ne.jp/how-to-use.html
"""

en = """\
Please see this refecenses with translate: https://warzone.stars.ne.jp/how-to-use.html
Player list: https://warzone.stars.ne.jp/
"""
