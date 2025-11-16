# Smart ToDo App 開発ログ

## プロジェクト概要
Flask + SQLAlchemy を使ったタスク管理アプリケーション

---

## 環境構築

### 前提条件
- Windows + WSL (Ubuntu 24.04)
- Python 3.12
- Cursor エディタ

### セットアップ
```bash
# プロジェクト作成
cd /mnt/d/work
mkdir smart-todo-app && cd smart-todo-app

# venv作成
python3 -m venv venv
source venv/bin/activate

# Git初期化
git init
gh repo create smart-todo-app --public --source=. --remote=origin --push
```

### Cursor設定
- **フォルダ**: `smart-todo-app` を開く（work全体ではない）
- **ターミナル**: WSL (Ubuntu-24.04) をデフォルトに設定
- **Pythonインタープリタ**: `${workspaceFolder}/venv/bin/python`

---

## 実装フェーズ

### Phase 1: 基本CRUD機能
**実装内容:**
- タスクモデル（タイトル、説明、場所、期限、優先度、ステータス）
- REST API（CRUD操作）
- Web UI（一覧、作成、編集、削除、検索）

**主要ファイル:**
- `models.py` - データモデル
- `app.py` - アプリケーションロジック
- `config.py` - 設定
- `templates/` - HTMLテンプレート

---

### Phase 2: 天気API連携
**実装内容:**
- OpenWeatherMap API連携
- タスクの場所に基づく天気情報表示
- 悪天候警告機能

**主要ファイル:**
- `api_client.py` - API通信
- `.env` - APIキー管理

**環境変数:**
```bash
OPENWEATHER_API_KEY=あなたのAPIキー
SECRET_KEY=ランダムな文字列
DATABASE_URL=sqlite:///tasks.db
```

---

### Phase 3: 拡張機能
**実装内容:**
- 統計ダッシュボード（完了率、分布グラフ）
- 繰り返しタスク（daily/weekly/monthly）

**主要エンドポイント:**
- `/dashboard` - 統計表示

---

## 運用

### 開発サーバー起動
```bash
cd /mnt/d/work/smart-todo-app
source venv/bin/activate
flask run
# http://localhost:5000
```

### Git操作
```bash
# コミット
git add .
git commit -m "feat: 機能の説明"
git push

# 認証エラーが出たら
gh auth setup-git
```

---

## トラブルシューティング

### Port 5000が使用中
```bash
pkill -f flask
flask run
```

### Pythonインタープリターエラー
**Ctrl + Shift + P** → `Python: Select Interpreter`
→ `./venv/bin/python` を選択

### PowerShellプロファイルエラー
無視してOK（WSL動作には影響なし）

---

## 便利なツール

### レビューチェックリスト
```bash
curl -o docs/REVIEW_CHECKLIST.md https://raw.githubusercontent.com/isyu-tsuji/dev-templates/main/code-review/REVIEW_CHECKLIST.md
```

**Cursorで使用:**
```
@docs/REVIEW_CHECKLIST.md に従って @api_client.py を日本語でレビューして
```

---

## 今後の改善案
- [ ] テスト追加（pytest）
- [ ] デプロイ（Heroku/Render）
- [ ] 通知機能
- [ ] カレンダー表示
