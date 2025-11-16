# Smart ToDo App

外部APIと連携したインテリジェントなToDoアプリケーション

## 機能

- タスクのCRUD操作
- 天気情報との連携（OpenWeatherMap API）
- 優先度・カテゴリによる管理
- シンプルで使いやすいUI

## セットアップ
```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# アプリ起動
flask run
```

## 技術スタック

- Python 3.x
- Flask
- SQLite
- OpenWeatherMap API

## 開発者

Created with Cursor + Claude

## 実装状況

- ✅ Phase 1: 基本CRUD機能（完了）
- ⏳ Phase 2: 天気API連携（未実装）
- ⏳ Phase 3: 拡張機能（未実装）

## スクリーンショット

ToDoアプリが動作中！
