# デプロイ手順

Smart ToDo Appのデプロイ手順です。

## 前提条件

- Gitリポジトリにコミット済み
- 環境変数の設定が必要（APIキーなど）

## デプロイ先別の手順

### 1. Heroku

#### セットアップ

```bash
# Heroku CLIをインストール（未インストールの場合）
# https://devcenter.heroku.com/articles/heroku-cli

# Herokuにログイン
heroku login

# アプリケーションを作成
heroku create smart-todo-app

# 環境変数を設定
heroku config:set SECRET_KEY=your-secret-key-here
heroku config:set OPENWEATHER_API_KEY=your-api-key-here
heroku config:set FLASK_ENV=production

# データベースアドオンを追加（PostgreSQL推奨）
heroku addons:create heroku-postgresql:mini

# デプロイ
git push heroku main

# データベースマイグレーション
heroku run python migrate_db.py

# アプリケーションを開く
heroku open
```

#### 注意事項

- HerokuはPostgreSQLを使用するため、`DATABASE_URL`が自動的に設定されます
- 無料プランは2022年11月に終了しました（有料プランが必要）

---

### 2. Railway

#### セットアップ

1. [Railway](https://railway.app/)にアクセスしてアカウント作成
2. GitHubリポジトリを接続
3. 新しいプロジェクトを作成
4. 環境変数を設定：
   - `SECRET_KEY`
   - `OPENWEATHER_API_KEY`
   - `FLASK_ENV=production`
5. PostgreSQLデータベースを追加（オプション）
6. デプロイボタンをクリック

#### 環境変数の設定

Railwayのダッシュボードで以下を設定：

```
SECRET_KEY=your-secret-key-here
OPENWEATHER_API_KEY=your-api-key-here
FLASK_ENV=production
DATABASE_URL=postgresql://... (PostgreSQLを使用する場合)
```

---

### 3. Render

#### セットアップ

1. [Render](https://render.com/)にアクセスしてアカウント作成
2. 新しいWebサービスを作成
3. GitHubリポジトリを接続
4. 設定：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3
5. 環境変数を設定
6. デプロイ

#### 環境変数の設定

Renderのダッシュボードで以下を設定：

```
SECRET_KEY=your-secret-key-here
OPENWEATHER_API_KEY=your-api-key-here
FLASK_ENV=production
```

---

### 4. VPS (Ubuntu/Debian)

#### セットアップ

```bash
# サーバーにSSH接続
ssh user@your-server-ip

# システムパッケージを更新
sudo apt update && sudo apt upgrade -y

# Pythonとpipをインストール
sudo apt install python3 python3-pip python3-venv nginx -y

# プロジェクトディレクトリを作成
mkdir -p /var/www/smart-todo-app
cd /var/www/smart-todo-app

# Gitリポジトリをクローン
git clone https://github.com/your-username/smart-todo-app.git .

# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定（.envファイルを作成）
nano .env
# 以下を追加:
# SECRET_KEY=your-secret-key-here
# OPENWEATHER_API_KEY=your-api-key-here
# FLASK_ENV=production

# データベースを初期化
python migrate_db.py

# Gunicornをsystemdサービスとして設定
sudo nano /etc/systemd/system/smart-todo-app.service
```

#### systemdサービスファイル

```ini
[Unit]
Description=Smart ToDo App Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/smart-todo-app
Environment="PATH=/var/www/smart-todo-app/venv/bin"
ExecStart=/var/www/smart-todo-app/venv/bin/gunicorn --workers 3 --bind unix:/var/www/smart-todo-app/smart-todo-app.sock app:app

[Install]
WantedBy=multi-user.target
```

```bash
# サービスを有効化
sudo systemctl daemon-reload
sudo systemctl start smart-todo-app
sudo systemctl enable smart-todo-app

# Nginx設定
sudo nano /etc/nginx/sites-available/smart-todo-app
```

#### Nginx設定ファイル

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/smart-todo-app/smart-todo-app.sock;
    }
}
```

```bash
# Nginx設定を有効化
sudo ln -s /etc/nginx/sites-available/smart-todo-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 環境変数の設定

すべてのデプロイ先で以下の環境変数を設定してください：

### 必須

- `SECRET_KEY`: Flaskのセッション暗号化キー（ランダムな文字列）
  ```bash
  # 生成方法
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- `OPENWEATHER_API_KEY`: OpenWeatherMap APIキー
  - [OpenWeatherMap](https://openweathermap.org/api)で取得

### オプション

- `FLASK_ENV`: `production`（本番環境）
- `DATABASE_URL`: データベース接続URL（PostgreSQL推奨）

---

## デプロイ後の確認事項

1. **アプリケーションが起動しているか確認**
   - ブラウザでアクセスして動作確認

2. **データベースマイグレーション**
   - 初回デプロイ時は`migrate_db.py`を実行

3. **ログの確認**
   - エラーがないか確認

4. **環境変数の確認**
   - すべての環境変数が正しく設定されているか確認

---

## トラブルシューティング

### アプリケーションが起動しない

- ログを確認: `heroku logs --tail` (Herokuの場合)
- 環境変数が設定されているか確認
- データベース接続を確認

### CSRFエラーが発生する

- `SECRET_KEY`が設定されているか確認
- セッションクッキーが正しく設定されているか確認

### データベースエラー

- データベースURLが正しいか確認
- マイグレーションが実行されているか確認

---

## セキュリティチェックリスト

- [ ] `SECRET_KEY`が強力なランダム文字列である
- [ ] `DEBUG=False`（本番環境）
- [ ] 環境変数に機密情報が含まれていない（.envファイルをGitにコミットしていない）
- [ ] HTTPSが有効（Let's Encryptなど）
- [ ] データベースのバックアップ設定

---

## 参考リンク

- [Flask Deployment Options](https://flask.palletsprojects.com/en/latest/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)

