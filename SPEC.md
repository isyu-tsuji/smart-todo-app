# Smart ToDo App - 仕様書 (SPEC.md)

## プロジェクト概要

外部APIと連携したインテリジェントなToDoアプリケーション。基本的なCRUD機能に加えて、天気情報やリマインダー通知などのスマート機能を提供します。

**プロジェクト名**: Smart ToDo App  
**技術スタック**: Python, Flask, SQLite, REST API  
**対象ユーザー**: 効率的にタスク管理したい個人ユーザー

---

## 機能要件

### Phase 1: 基本機能（MVP）

#### 1.1 タスクCRUD
- タスクの作成、表示、更新、削除
- 各タスクの情報：
  - タイトル（必須）
  - 説明（任意）
  - 期限（任意）
  - 優先度（高/中/低）
  - ステータス（未完了/完了）
  - カテゴリ（仕事/個人/買い物/その他）

#### 1.2 タスク一覧表示
- すべてのタスクを表示
- ステータスでフィルタリング（未完了/完了/すべて）
- 優先度でソート
- 期限でソート

#### 1.3 タスク検索
- タイトルと説明でキーワード検索
- カテゴリで絞り込み

### Phase 2: API連携機能

#### 2.1 天気連携（OpenWeatherMap API）
- タスクに位置情報を関連付け
- 外出タスクの場合、当日の天気を表示
- 悪天候（雨/雪）の場合、警告アイコン表示

**API**: OpenWeatherMap API  
**エンドポイント**: `https://api.openweathermap.org/data/2.5/weather`

#### 2.2 通知機能（オプション）
- 期限が近いタスクをコンソールに表示
- 期限の1日前、当日に通知

### Phase 3: 拡張機能（オプション）

#### 3.1 統計ダッシュボード
- 完了タスク数
- カテゴリ別タスク分布
- 今週の達成率

#### 3.2 繰り返しタスク
- 毎日/毎週/毎月の繰り返し設定

---

## 技術仕様

### アーキテクチャ

```
smart-todo-app/
├── app.py                 # Flaskアプリケーション本体
├── models.py              # データモデル
├── api_client.py          # 外部API通信
├── config.py              # 設定ファイル
├── requirements.txt       # 依存パッケージ
├── .env                   # 環境変数（APIキーなど）
├── .gitignore
├── README.md
├── SPEC.md
├── static/                # 静的ファイル（CSS, JS）
│   ├── style.css
│   └── script.js
├── templates/             # HTMLテンプレート
│   ├── base.html
│   ├── index.html
│   ├── task_form.html
│   └── task_detail.html
└── tests/                 # テストコード
    └── test_app.py
```

### データモデル

**Task テーブル**
```python
class Task:
    id: Integer (Primary Key)
    title: String(200) - 必須
    description: Text - 任意
    due_date: DateTime - 任意
    priority: String(10) - 'high', 'medium', 'low' (デフォルト: 'medium')
    status: String(20) - 'pending', 'completed' (デフォルト: 'pending')
    category: String(50) - 'work', 'personal', 'shopping', 'other'
    location: String(100) - 任意（天気取得用）
    created_at: DateTime - 自動設定
    updated_at: DateTime - 自動更新
```

### API設計

#### RESTful エンドポイント

**タスク一覧取得**
```
GET /api/tasks
Query Parameters:
  - status: pending|completed|all (default: all)
  - category: work|personal|shopping|other
  - sort: priority|due_date|created_at (default: created_at)

Response:
{
  "tasks": [
    {
      "id": 1,
      "title": "会議資料作成",
      "description": "Q4報告用",
      "due_date": "2025-11-20T10:00:00",
      "priority": "high",
      "status": "pending",
      "category": "work",
      "location": "Tokyo",
      "weather": {
        "temp": 15.5,
        "condition": "晴れ",
        "icon": "01d"
      }
    }
  ]
}
```

**タスク作成**
```
POST /api/tasks
Body:
{
  "title": "タスク名",
  "description": "説明",
  "due_date": "2025-11-20T10:00:00",
  "priority": "high",
  "category": "work",
  "location": "Tokyo"
}

Response: 201 Created
{
  "id": 1,
  "message": "Task created successfully"
}
```

**タスク詳細取得**
```
GET /api/tasks/<id>

Response:
{
  "id": 1,
  "title": "会議資料作成",
  ...
}
```

**タスク更新**
```
PUT /api/tasks/<id>
Body:
{
  "title": "更新されたタスク名",
  "status": "completed"
}

Response: 200 OK
{
  "message": "Task updated successfully"
}
```

**タスク削除**
```
DELETE /api/tasks/<id>

Response: 200 OK
{
  "message": "Task deleted successfully"
}
```

**タスク検索**
```
GET /api/tasks/search?q=会議

Response:
{
  "results": [...]
}
```

#### Web UI エンドポイント

```
GET /                      # トップページ（タスク一覧）
GET /tasks/new             # タスク作成フォーム
POST /tasks                # タスク作成処理
GET /tasks/<id>            # タスク詳細
GET /tasks/<id>/edit       # タスク編集フォーム
POST /tasks/<id>/update    # タスク更新処理
POST /tasks/<id>/delete    # タスク削除処理
POST /tasks/<id>/toggle    # ステータス切り替え
```

### 外部API仕様

**OpenWeatherMap API**
```python
# エンドポイント
https://api.openweathermap.org/data/2.5/weather

# パラメータ
params = {
    'q': 'Tokyo',           # 都市名
    'appid': API_KEY,       # APIキー
    'units': 'metric',      # 摂氏
    'lang': 'ja'            # 日本語
}

# レスポンス例
{
  "weather": [{"main": "Clear", "description": "晴れ"}],
  "main": {"temp": 15.5},
  "name": "Tokyo"
}
```

---

## 実装の優先順位

### Priority 1: 必須機能（MVP）
1. データベース設定（SQLite + SQLAlchemy）
2. Taskモデル実装
3. 基本CRUD API実装
4. シンプルなWeb UI実装
5. タスク一覧/作成/編集/削除

### Priority 2: API連携
1. OpenWeatherMap API連携モジュール
2. 天気情報の取得と表示
3. エラーハンドリング

### Priority 3: 拡張機能
1. 検索機能
2. フィルタリング・ソート
3. 統計ダッシュボード

---

## 実装ガイドライン

### コーディング規約

**Python**
- PEP 8に準拠
- 関数にはdocstringを記述
- タイプヒントを使用

```python
def create_task(title: str, description: str = None) -> Task:
    """
    新しいタスクを作成します。
    
    Args:
        title: タスクのタイトル
        description: タスクの説明（任意）
    
    Returns:
        作成されたTaskオブジェクト
    """
    pass
```

**命名規則**
- 変数・関数: snake_case
- クラス: PascalCase
- 定数: UPPER_SNAKE_CASE

### エラーハンドリング

```python
# APIエラー
try:
    response = requests.get(url)
    response.raise_for_status()
except requests.RequestException as e:
    return {"error": "API request failed"}, 500

# バリデーションエラー
if not title:
    return {"error": "Title is required"}, 400
```

### テスト

```python
# 各機能にユニットテストを追加
def test_create_task():
    task = create_task("テストタスク")
    assert task.title == "テストタスク"
    assert task.status == "pending"
```

---

## セットアップ手順

### 1. 依存パッケージ

**requirements.txt**
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
python-dotenv==1.0.0
requests==2.31.0
pytest==7.4.3
```

### 2. 環境変数

**.env**
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///tasks.db
OPENWEATHER_API_KEY=your-api-key-here
```

### 3. データベース初期化

```bash
python3 -c "from app import db; db.create_all()"
```

### 4. アプリ起動

```bash
flask run
# または
python app.py
```

---

## API キーの取得

### OpenWeatherMap
1. https://openweathermap.org/ にアクセス
2. Sign Upでアカウント作成
3. API keys タブでAPIキーを生成
4. `.env` ファイルに追加

**無料プラン**: 1分間に60回、1日1000回まで

---

## UI/UXガイドライン

### デザイン方針
- **シンプル**: 余計な装飾を避け、使いやすさ重視
- **レスポンシブ**: モバイルでも使える
- **直感的**: 最小限のクリックで操作完了

### カラーパレット
```css
--primary: #3b82f6      /* 青 - メインアクション */
--success: #10b981      /* 緑 - 完了タスク */
--warning: #f59e0b      /* オレンジ - 期限間近 */
--danger: #ef4444       /* 赤 - 期限切れ */
--gray: #6b7280         /* グレー - 通常テキスト */
```

### 主要UI要素

**タスクカード**
```
┌─────────────────────────────────────┐
│ ☐ 会議資料作成              [高] 🏢 │
│   Q4報告用                          │
│   📅 2025-11-20  🌤️ 晴れ 15°C      │
│   [編集] [削除]                     │
└─────────────────────────────────────┘
```

**ボタンスタイル**
- プライマリアクション: 青背景、白テキスト
- セカンダリアクション: 白背景、青ボーダー
- 削除アクション: 赤テキスト

---

## 開発フロー

### Gitコミット戦略

**ブランチ**
```
main              # 本番
develop           # 開発
feature/crud      # CRUD機能
feature/weather   # 天気連携
bugfix/xxx        # バグ修正
```

**コミットメッセージ**
```
feat: タスクCRUD機能を実装
fix: 日付フォーマットのバグを修正
docs: READMEを更新
style: コードフォーマット調整
refactor: API関数を整理
test: タスク作成のテストを追加
```

### 実装の進め方

**Step 1: プロジェクトセットアップ**
```bash
# venv作成
python3 -m venv venv
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# .envファイル作成
# データベース初期化
```

**Step 2: モデル実装**
- `models.py` でTaskモデル定義
- データベーステーブル作成

**Step 3: API実装**
- `app.py` でFlaskアプリ作成
- CRUD エンドポイント実装
- Postmanなどでテスト

**Step 4: UI実装**
- `templates/` でHTMLテンプレート作成
- `static/` でCSS/JS追加
- ブラウザで動作確認

**Step 5: API連携**
- `api_client.py` で天気API実装
- タスク表示時に天気情報を追加

**Step 6: テスト・改善**
- ユニットテスト追加
- バグ修正
- UI/UX改善

---

## トラブルシューティング

### よくある問題

**問題: データベースが作成されない**
```bash
# 解決: 手動で作成
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

**問題: API呼び出しが失敗する**
- APIキーが正しいか確認
- `.env` ファイルが読み込まれているか確認
- ネットワーク接続を確認

**問題: Flaskアプリが起動しない**
```bash
# ポートが使用中の場合
flask run --port 5001
```

---

## 参考リンク

- [Flask公式ドキュメント](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [REST API設計](https://restfulapi.net/)

---

## 今後の拡張アイデア

### 追加機能案
- ユーザー認証（ログイン/登録）
- タスクの共有機能
- Slack/Discord通知連携
- カレンダー連携（Google Calendar API）
- GitHub Issues連携
- タスクのインポート/エクスポート（CSV/JSON）
- ダークモード
- 音声入力でタスク作成

### 技術的改善
- PostgreSQLへの移行（本番環境）
- Redis for キャッシング
- Celeryで非同期タスク処理
- Dockerコンテナ化
- CI/CDパイプライン構築

---

**作成日**: 2025年11月16日  
**バージョン**: 1.0  
**ステータス**: 実装準備完了