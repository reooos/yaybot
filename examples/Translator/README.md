# Translator

メンションして投稿すると翻訳した文章を返信します。

### 実行方法

以下のスクリプトをコンソール上で実行してください。

```bash
python translator.py
```

### 使い方

---

#### [@メンション], [原文の言語], [翻訳したい言語], [本文]

---

上のように投稿してください。

例) @ユーザー名 en ja Hello, World!

### 設定

- メールアドレス、パスワードは _.env_ ファイルに設定してください。
- 通知を再度取得するまでの時間を指定するには、start()関数の引数に整数を入力してください。  
  ※ デフォルト値は 30 秒です。

```python
bot.start(15) # 15秒毎に通知を取得する
```

---

_by @qualia-5w4_