# Smart ToDo App

Flask製のタスク管理アプリケーション。天気情報連携と統計ダッシュボード付き。

## 機能

- ✅ タスクCRUD（作成・編集・削除）
- ��️ 天気情報表示（OpenWeatherMap API）
- 📊 統計ダッシュボード
- 🔄 繰り返しタスク（日次・週次・月次）
- 🔍 検索・フィルタリング

## セットアップ

### 1. クローン
```bash
git clone https://github.com/isyu-tsuji/smart-todo-app.git
cd smart-todo-app
```

### 2. 仮想環境
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 環境変数
```bash
cp .env.example .env
# .envを編集してAPIキーを設定
```

### 4. 起動
```bash
flask run
```

http://localhost:5000 にアクセス

## 技術スタック

- **Backend**: Flask 3.0, SQLAlchemy
- **Frontend**: HTML, CSS, Chart.js
- **API**: OpenWeatherMap
- **Database**: SQLite

## ドキュメント

詳細は [開発ログ](./docs/DEVELOPMENT_LOG.md) を参照

## ライセンス

MIT
