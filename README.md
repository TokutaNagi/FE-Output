# FE-Output - 基本情報技術者試験 用語アウトプットアプリ

このリポジトリは、基本情報技術者試験の用語学習に特化したDjangoベースのWebアプリケーションです。

ユーザーが解説を読んで用語を「思い出して入力する」ことで、知識の定着を図るアウトプット学習に特化した設計になっています。

---

# アプリコンセプト

**FE-Output** は、基本情報技術者試験の用語を入力形式で学習するWebアプリです。

参考書などで基礎知識を学んだ後の復習・知識の定着を目的としており、段階的なヒント機能と誤答追跡により、効率的なアウトプット学習をサポートします。

想定ユーザーは、基本情報技術者試験の学習者で、インプット学習後の知識定着を目的とした学習ツールとして設計しています。

---

# 使用技術

- **Language**
  - Python（75%）
  - HTML（16.5%）
  - CSS（8.5%）

- **Framework / Runtime**
  - Django 6.0.6

- **Database**
  - SQLite（開発環境）

- **Libraries / Tools**
  - Django ORM
  - Django TestCase
  - Ruff（静的解析）
  - Playwright（E2Eテスト）
  - coverage.py

---

# フォルダ構造

```text
config/                      Djangoプロジェクト設定
├── settings.py              言語設定・DB設定・アプリ登録
├── urls.py                  ルートURL設定
├── wsgi.py
└── asgi.py

terms/                       メインアプリケーション
├── models.py                Category・Term・Alias・Resultなど
├── views.py                 画面処理・ゲーム処理・認証処理
├── utils.py                 回答判定・ヒント生成・文字正規化
├── forms.py                 Django Form
├── urls.py                  URL定義
├── admin.py                 管理画面設定
├── templates/
│   └── terms/
│       ├── base.html
│       ├── top.html
│       ├── question.html
│       ├── result.html
│       ├── mypage.html
│       ├── login.html
│       ├── signup.html
│       └── mistake_quiz.html
└── static/
    └── terms/
        ├── css/
        │   └── style.css
        └── images/

templates/
├── 404.html
├── 500.html
└── game_error.html

manage.py

要件定義書.md
テスト仕様書.md
```

---

# アプリ設計

アプリの処理の流れは以下のようになっています。

```text
トップ画面
    ↓
分野選択
    ↓
問題開始
（問題IDをSessionへ保存）
    ↓
問題画面
    ↓
回答入力
    ↓
normalize()
（表記ゆれ吸収）
    ↓
is_correct_answer()
（用語・Alias判定）
    ↓
正解
      または
ヒント表示
    ↓
全問題終了
    ↓
Result保存
    ↓
マイページ
```

ログインしているユーザーは **UserTermStat** に誤答情報を保存し、

- 苦手問題一覧
- 苦手問題のみ出題

を利用できます。

---

# 機能一覧

- 分野選択
- 用語アウトプット形式の学習
- 段階的ヒント機能
- 表記ゆれを吸収した回答判定
- エイリアス（別名）対応
- リザルト表示
- ユーザー登録
- ログイン・ログアウト
- プレイ履歴
- 苦手問題一覧
- 苦手問題のみ出題
- Django管理画面から問題管理
- CSVインポートによる問題登録

---

# 回答判定

回答判定では `normalize()` を使用し、

- 全角・半角の統一
- 大文字・小文字の統一
- 不要な記号の除去
- 前後スペース削除

などを行った後、

`is_correct_answer()` によって

1. 用語
2. Alias

を照合し、どちらか一致すれば正解となります。

---

# 環境構築とテスト

## 依存ライブラリ

```bash
pip install -r requirements.txt
```

---

## マイグレーション

```bash
python manage.py migrate
```

---

## 初期データ投入

```bash
python manage.py loaddata
```

または

- Django Admin

から登録できます。

---

## 開発サーバー起動

```bash
python manage.py runserver
```

アクセス

```
http://127.0.0.1:8000
```

---

## テスト

```bash
python manage.py test terms.tests
```

---

## Ruff

```bash
ruff check .
```

---

## Playwright

```bash
pytest
```

---

# 追加予定機能

- 分野追加
  - OS
  - ソフトウェア
  - ハードウェア
  - アルゴリズム
  - システム開発
  - ストラテジ
  - マネジメント

- ランダム出題

- 分野横断モード

- UI改善

- ダークモード

- スマートフォン対応