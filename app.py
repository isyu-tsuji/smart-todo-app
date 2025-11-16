"""
Flaskアプリケーション本体
Phase 1: 基本機能（CRUD、一覧表示、検索）
"""
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from sqlalchemy import case
from models import db, Task
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# データベース初期化
db.init_app(app)

# データベーステーブル作成
with app.app_context():
    db.create_all()


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
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks]
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
        location=data.get('location')
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
        タスク情報
    """
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())


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
    
    return render_template('index.html', tasks=tasks, 
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
        location=request.form.get('location')
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
    db.session.commit()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

