jp = """\
```
つかいかた:

ホスト
  warzone部屋建て --yyk 部屋名（デフォルト無制限）
  lazuaoe部屋建て --lzyyk 部屋名（デフォルトLN）
  1～6人を募集 --yyk1～6 部屋名
  爆破する --bakuha 部屋番号（1つしか建ててないときは省略可能）

参加者
  参加する --no 部屋番号（1つしか部屋がないときは省略可能）
  ぬける   --nuke 部屋番号（1つの部屋にしか入ってないときは省略可能）

その他
  部屋一覧 --rooms
  無理矢理部屋を消す（干しっぱなし用、管理者使用推奨） --force-bakuha-tekumakumayakonn-tekumakumayakonn 部屋番号
  つかいかたを出す --help
  How to use in English: --help-en
```
"""

en = """\
```
How to use:
  Send a [--commands] below on #general（de）.

Host
  Create room: --yyk [room name]（無制限 is default）
  無制限 means all welcome.
    --yyk is the same as these:
      --call, --create, --reserve, --heybros

  Call 1 to 6 brothers: --yyk1to6 [room name]（無制限 is default）
    --yyk1to6 is the same as these:
      --call1to6, --create1to6, --reserve1to6, --heybros1to6

    Example: Call 3 brothers for ranked match.
      --call3 [room name]

  Cencel: --bakuha [room number] (The room number can be omitted if there is only one room)
    --bakuha is the same as these:
      --destroy, --explosion, --del, --cancel, --hakai
    --hakai is Japanese 破壊 it means destroy.

Guest
  Join: --no [room number] (The room number can be omitted if there is only one room)
    --no is the same as these:
      --in, --join

  Dismiss: --nuke [room number] (The room number can be omitted if you are in only one room)
    --nuke is the same as these:
      --out, --leave, --dismiss

Others
  See room list: --rooms
  DANGER (DO NOT USE): --force-bakuha-tekumakumayakonn-tekumakumayakonn
    tekumaku mayakonn is the magical words in Japan.
  日本語でつかいかたを出す: --help
  See this help: --help-en
```
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
