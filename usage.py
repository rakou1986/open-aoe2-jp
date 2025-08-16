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

管理用（-register, -setrateは移行用）
  -register @メンション
  -setrate @メンション レーティング（arabia, LN, michi, bakuran） レートの数
  -force-win [部屋番号]（ホスト視点で使用のこと）
  -force-lose [部屋番号]（ホスト視点で使用のこと）

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

no_token = """\
botの実行にはトークンが必要です。
warzone-aoeで認証済みのbotのトークンはrakouが発行しますが、rakouがいない場合はDiscord Developer Portalでアプリケーションを作成し、warzone-aoeで認証し、有効なトークンをセットしなければなりません。

2025/04現在の手順
  ブラウザ版Discordにログイン
  https://discord.com/developers/docs/intro を開く
  Applications > New Application > rakou_botなどと入力 > Create

  SETTINGS > OAuth2 > OAuth2 URL Generator > bot をチェック
  下に出てくる BOT PERMISSIONSで以下をチェック
    - Send Messages
    - Manage Messages
    - Read Message History
    - Mention Everyone

  一番下に出てくるGENERATED URLをCopyしてwarzone-aoeのテキストに貼り付け

  @rate_counseler（名前が黄色い人）を呼んで、貼り付けたURLを押してもらって、botを認証してもらう。

  Dicord Developerの画面に戻り、 SETTINGS > Bot を開く
  TOKEN > Reset Token を押すたびに1度だけ出てくる Token をコピーして、token.txt という名前で bot4wz.exe と同じフォルダに保存する。
  ファイル名は token.txt でなければなりません。

  【注意】さらにReset Tokenを押すと、過去のトークンが無効になります。トークンは常に最新の1つだけが有効です。
  もしReset Tokenを押してしまったら、token.txt を削除して、新しいトークンを token.txt に保存してください。

手順を実行したらこのウインドウを閉じて、再度bot4wz.exeをダブルクリックすればbotが起動します。

botが起動すると、# bot_statusチャンネルに、botを起動したPCのホスト名が出ます。
恥ずかしいホスト名とか、人に見られたくないホスト名は、事前に変更をおすすめします。
できれば誰のPCか分かる名前だとよいでしょう。
Windows 10では、設定 > システム > バージョン情報 > デバイス名
これがホスト名です。「このPCの名前を変更」で変更します。

botを起動後、botが1回応答すると、5つの.pickleファイルが作られます。これらを触らないようにしてください。
ただしbotがなにか動作不良を起こした場合はこれらを削除すると初期化できます。
"""

at_launch = """\

終了するには Ctrl + C または kill -SIGINT <pid>
部屋の状態などを保存するための.pickleファイルが3つ作られますが、触らないでください。
"""
