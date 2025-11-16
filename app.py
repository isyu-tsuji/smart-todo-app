"""
Flaskアプリケーション本体
Phase 1: 基本機能（CRUD、一覧表示、検索）
Phase 2: 天気API連携
"""
from datetime import datetime, timedelta
from typing import Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for
from sqlalchemy import case, func
from models import db, Task
from config import Config
from api_client import get_weather_safe

app = Flask(__name__)
app.config.from_object(Config)

# データベース初期化
db.init_app(app)

# データベーステーブル作成
with app.app_context():
    db.create_all()


# ==================== ヘルパー関数 ====================

def generate_repeat_task(parent_task: Task) -> Optional[Task]:
    """
    繰り返しタスクを生成します。
    
    Args:
        parent_task: 親タスク（繰り返し設定があるタスク）
    
    Returns:
        生成されたタスク、またはNone（生成できない場合）
    """
    if not parent_task.repeat_type or parent_task.repeat_type == 'none':
        return None
    
    if not parent_task.due_date:
        # 期限がない場合は生成しない
        return None
    
    # 次の期限日を計算
    next_due_date = None
    if parent_task.repeat_type == 'daily':
        next_due_date = parent_task.due_date + timedelta(days=1)
    elif parent_task.repeat_type == 'weekly':
        next_due_date = parent_task.due_date + timedelta(weeks=1)
    elif parent_task.repeat_type == 'monthly':
        # 月の加算（簡易版）
        next_due_date = parent_task.due_date + timedelta(days=30)
    
    if not next_due_date:
        return None
    
    # 既に同じ親タスクから生成されたタスクが存在するかチェック
    existing_task = Task.query.filter(
        Task.parent_task_id == parent_task.id,
        Task.due_date == next_due_date,
        Task.status == 'pending'
    ).first()
    
    if existing_task:
        # 既に存在する場合は生成しない
        return None
    
    # 新しいタスクを作成
    new_task = Task(
        title=parent_task.title,
        description=parent_task.description,
        due_date=next_due_date,
        priority=parent_task.priority,
        status='pending',
        category=parent_task.category,
        location=parent_task.location,
        repeat_type=parent_task.repeat_type,
        parent_task_id=parent_task.id
    )
    
    return new_task


def check_and_generate_repeat_tasks():
    """
    期限が過ぎた繰り返しタスクをチェックし、必要に応じて新しいタスクを生成します。
    この関数は定期的に呼び出されることを想定しています。
    """
    now = datetime.utcnow()
    
    # 期限が過ぎた繰り返しタスク（未完了）を取得
    overdue_repeat_tasks = Task.query.filter(
        Task.repeat_type != 'none',
        Task.due_date < now,
        Task.status == 'pending',
        Task.parent_task_id.is_(None)  # 親タスクのみ（生成されたタスクではない）
    ).all()
    
    generated_count = 0
    for task in overdue_repeat_tasks:
        new_task = generate_repeat_task(task)
        if new_task:
            db.session.add(new_task)
            generated_count += 1
    
    if generated_count > 0:
        db.session.commit()
    
    return generated_count


def add_weather_to_task(task_dict: dict) -> dict:
    """
    タスク辞書に天気情報を追加します。
    
    Args:
        task_dict: タスク情報を含む辞書
    
    Returns:
        天気情報が追加されたタスク辞書
    """
    location = task_dict.get('location')
    if location:
        weather = get_weather_safe(location)
        if weather:
            task_dict['weather'] = weather
    return task_dict


# ==================== REST API エンドポイント ====================

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """
    タスク一覧取得
    
    Query Parameters:
        status: pending|completed|all (default: all)
        category: work|personal|shopping|other
        sort: priority|due_date|created_at (default: created_at)
    
    Returns:
        JSON形式のタスク一覧
    """
    # クエリパラメータ取得
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', None)
    sort_by = request.args.get('sort', 'created_at')
    
    # クエリ構築
    query = Task.query
    
    # ステータスフィルタ
    if status_filter == 'pending':
        query = query.filter(Task.status == 'pending')
    elif status_filter == 'completed':
        query = query.filter(Task.status == 'completed')
    
    # カテゴリフィルタ
    if category_filter:
        query = query.filter(Task.category == category_filter)
    
    # ソート
    if sort_by == 'priority':
        # 優先度の順序: high > medium > low
        priority_order = case(
            (Task.priority == 'high', 1),
            (Task.priority == 'medium', 2),
            (Task.priority == 'low', 3),
            else_=4
        )
        query = query.order_by(priority_order)
    elif sort_by == 'due_date':
        query = query.order_by(Task.due_date.asc().nulls_last())
    else:
        query = query.order_by(Task.created_at.desc())
    
    tasks = query.all()
    
    # タスクに天気情報を追加
    tasks_with_weather = []
    for task in tasks:
        task_dict = task.to_dict()
        add_weather_to_task(task_dict)
        tasks_with_weather.append(task_dict)
    
    return jsonify({
        'tasks': tasks_with_weather
    })


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """
    タスク作成
    
    Body:
        title: タスクタイトル（必須）
        description: 説明（任意）
        due_date: 期限（任意、ISO形式）
        priority: 優先度（high/medium/low）
        category: カテゴリ（work/personal/shopping/other）
        location: 位置情報（任意）
    
    Returns:
        作成されたタスクのID
    """
    data = request.get_json()
    
    # バリデーション
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    # 期限のパース
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({'error': 'Invalid date format. Use ISO format.'}), 400
    
    # タスク作成
    task = Task(
        title=data['title'],
        description=data.get('description'),
        due_date=due_date,
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'pending'),
        category=data.get('category'),
        location=data.get('location'),
        repeat_type=data.get('repeat_type', 'none')
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        'id': task.id,
        'message': 'Task created successfully'
    }), 201


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id: int):
    """
    タスク詳細取得
    
    Args:
        task_id: タスクID
    
    Returns:
        タスク情報（天気情報を含む）
    """
    task = Task.query.get_or_404(task_id)
    task_dict = task.to_dict()
    add_weather_to_task(task_dict)
    return jsonify(task_dict)


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id: int):
    """
    タスク更新
    
    Args:
        task_id: タスクID
    
    Body:
        更新したいフィールドのみを送信
    
    Returns:
        更新成功メッセージ
    """
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # フィールド更新
    if 'title' in data:
        if not data['title']:
            return jsonify({'error': 'Title cannot be empty'}), 400
        task.title = data['title']
    
    if 'description' in data:
        task.description = data['description']
    
    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return jsonify({'error': 'Invalid date format. Use ISO format.'}), 400
        else:
            task.due_date = None
    
    if 'priority' in data:
        if data['priority'] not in ['high', 'medium', 'low']:
            return jsonify({'error': 'Invalid priority. Use high, medium, or low.'}), 400
        task.priority = data['priority']
    
    if 'status' in data:
        if data['status'] not in ['pending', 'completed']:
            return jsonify({'error': 'Invalid status. Use pending or completed.'}), 400
        task.status = data['status']
    
    if 'category' in data:
        task.category = data['category']
    
    if 'location' in data:
        task.location = data['location']
    
    if 'repeat_type' in data:
        if data['repeat_type'] not in ['none', 'daily', 'weekly', 'monthly']:
            return jsonify({'error': 'Invalid repeat_type. Use none, daily, weekly, or monthly.'}), 400
        task.repeat_type = data['repeat_type']
    
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Task updated successfully'
    })


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id: int):
    """
    タスク削除
    
    Args:
        task_id: タスクID
    
    Returns:
        削除成功メッセージ
    """
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({
        'message': 'Task deleted successfully'
    })


@app.route('/api/tasks/search', methods=['GET'])
def search_tasks():
    """
    タスク検索
    
    Query Parameters:
        q: 検索キーワード（タイトルと説明で検索）
        category: カテゴリで絞り込み（任意）
    
    Returns:
        検索結果
    """
    query_param = request.args.get('q', '')
    category_filter = request.args.get('category', None)
    
    if not query_param:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    # 検索クエリ構築
    query = Task.query.filter(
        db.or_(
            Task.title.contains(query_param),
            Task.description.contains(query_param)
        )
    )
    
    # カテゴリフィルタ
    if category_filter:
        query = query.filter(Task.category == category_filter)
    
    tasks = query.all()
    
    return jsonify({
        'results': [task.to_dict() for task in tasks]
    })


# ==================== Web UI エンドポイント ====================

@app.route('/')
def index():
    """
    トップページ（タスク一覧）
    """
    # 繰り返しタスクの自動生成をチェック（ページアクセス時に実行）
    check_and_generate_repeat_tasks()
    
    # クエリパラメータ取得
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', None)
    sort_by = request.args.get('sort', 'created_at')
    search_query = request.args.get('q', None)
    
    # クエリ構築
    query = Task.query
    
    # 検索
    if search_query:
        query = query.filter(
            db.or_(
                Task.title.contains(search_query),
                Task.description.contains(search_query)
            )
        )
    
    # ステータスフィルタ
    if status_filter == 'pending':
        query = query.filter(Task.status == 'pending')
    elif status_filter == 'completed':
        query = query.filter(Task.status == 'completed')
    
    # カテゴリフィルタ
    if category_filter:
        query = query.filter(Task.category == category_filter)
    
    # ソート
    if sort_by == 'priority':
        priority_order = case(
            (Task.priority == 'high', 1),
            (Task.priority == 'medium', 2),
            (Task.priority == 'low', 3),
            else_=4
        )
        query = query.order_by(priority_order)
    elif sort_by == 'due_date':
        query = query.order_by(Task.due_date.asc().nulls_last())
    else:
        query = query.order_by(Task.created_at.desc())
    
    tasks = query.all()
    
    # タスクに天気情報を追加（テンプレート用）
    tasks_with_weather = []
    for task in tasks:
        task_dict = task.to_dict()
        add_weather_to_task(task_dict)
        # タスクオブジェクトに天気情報を追加（テンプレートでアクセス可能にする）
        task.weather = task_dict.get('weather')
        tasks_with_weather.append(task)
    
    return render_template('index.html', tasks=tasks_with_weather, 
                         status_filter=status_filter,
                         category_filter=category_filter,
                         sort_by=sort_by,
                         search_query=search_query)


@app.route('/tasks/new', methods=['GET'])
def new_task_form():
    """
    タスク作成フォーム
    """
    return render_template('task_form.html', task=None)


@app.route('/tasks', methods=['POST'])
def create_task_web():
    """
    タスク作成処理（Web UI）
    """
    title = request.form.get('title')
    if not title:
        return redirect(url_for('new_task_form'))
    
    # 期限のパース
    due_date = None
    due_date_str = request.form.get('due_date')
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    task = Task(
        title=title,
        description=request.form.get('description'),
        due_date=due_date,
        priority=request.form.get('priority', 'medium'),
        category=request.form.get('category'),
        location=request.form.get('location'),
        repeat_type=request.form.get('repeat_type', 'none')
    )
    
    db.session.add(task)
    db.session.commit()
    
    return redirect(url_for('index'))


@app.route('/tasks/<int:task_id>')
def task_detail(task_id: int):
    """
    タスク詳細
    """
    task = Task.query.get_or_404(task_id)
    # タスクに天気情報を追加（テンプレート用）
    task_dict = task.to_dict()
    add_weather_to_task(task_dict)
    task.weather = task_dict.get('weather')
    return render_template('task_detail.html', task=task)


@app.route('/tasks/<int:task_id>/edit', methods=['GET'])
def edit_task_form(task_id: int):
    """
    タスク編集フォーム
    """
    task = Task.query.get_or_404(task_id)
    return render_template('task_form.html', task=task)


@app.route('/tasks/<int:task_id>/update', methods=['POST'])
def update_task_web(task_id: int):
    """
    タスク更新処理（Web UI）
    """
    task = Task.query.get_or_404(task_id)
    
    title = request.form.get('title')
    if not title:
        return redirect(url_for('edit_task_form', task_id=task_id))
    
    task.title = title
    task.description = request.form.get('description')
    
    # 期限のパース
    due_date_str = request.form.get('due_date')
    if due_date_str:
        try:
            task.due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    else:
        task.due_date = None
    
    task.priority = request.form.get('priority', 'medium')
    task.category = request.form.get('category')
    task.location = request.form.get('location')
    task.repeat_type = request.form.get('repeat_type', 'none')
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return redirect(url_for('task_detail', task_id=task_id))


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task_web(task_id: int):
    """
    タスク削除処理（Web UI）
    """
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    return redirect(url_for('index'))


@app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task_status(task_id: int):
    """
    タスクステータス切り替え（Web UI）
    """
    task = Task.query.get_or_404(task_id)
    task.status = 'completed' if task.status == 'pending' else 'pending'
    task.updated_at = datetime.utcnow()
    
    # タスクが完了した場合、繰り返しタスクを生成
    if task.status == 'completed' and task.repeat_type != 'none':
        new_task = generate_repeat_task(task)
        if new_task:
            db.session.add(new_task)
    
    db.session.commit()
    
    return redirect(url_for('index'))


@app.route('/api/tasks/generate-repeat', methods=['POST'])
def generate_repeat_tasks_api():
    """
    繰り返しタスクを生成するAPIエンドポイント（手動実行用）
    """
    try:
        count = check_and_generate_repeat_tasks()
        return jsonify({
            'message': f'{count}件の繰り返しタスクを生成しました',
            'generated_count': count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """
    統計ダッシュボード
    """
    # 総タスク数
    total_tasks = Task.query.count()
    
    # 完了タスク数
    completed_tasks = Task.query.filter(Task.status == 'completed').count()
    
    # 完了率
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # ステータス別の分布
    status_distribution = {
        'pending': Task.query.filter(Task.status == 'pending').count(),
        'completed': completed_tasks
    }
    
    # 優先度別の分布
    priority_distribution = {
        'high': Task.query.filter(Task.priority == 'high').count(),
        'medium': Task.query.filter(Task.priority == 'medium').count(),
        'low': Task.query.filter(Task.priority == 'low').count()
    }
    
    # 期限切れタスクの数（期限が過去で、未完了のタスク）
    now = datetime.utcnow()
    overdue_tasks = Task.query.filter(
        Task.due_date < now,
        Task.status == 'pending'
    ).count()
    
    # カテゴリ別の分布
    category_distribution = db.session.query(
        Task.category,
        func.count(Task.id).label('count')
    ).group_by(Task.category).all()
    category_data = {cat or '未設定': count for cat, count in category_distribution}
    category_labels = list(category_data.keys())
    category_values = list(category_data.values())
    
    # 今週のタスク作成数（日別）
    week_ago = now - timedelta(days=7)
    daily_created = db.session.query(
        func.date(Task.created_at).label('date'),
        func.count(Task.id).label('count')
    ).filter(
        Task.created_at >= week_ago
    ).group_by(func.date(Task.created_at)).all()
    
    # SQLiteのfunc.date()は文字列を返すため、そのまま使用
    daily_created_data = {
        str(date): count 
        for date, count in daily_created
    }
    
    stats = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),
        'status_distribution': status_distribution,
        'priority_distribution': priority_distribution,
        'overdue_tasks': overdue_tasks,
        'category_distribution': category_data,
        'category_labels': category_labels,
        'category_values': category_values,
        'daily_created': daily_created_data
    }
    
    return render_template('dashboard.html', stats=stats)


if __name__ == '__main__':
    app.run(debug=True)

