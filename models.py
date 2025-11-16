"""
データモデル定義
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    """
    タスクモデル
    
    Attributes:
        id: タスクID（主キー）
        title: タスクのタイトル（必須）
        description: タスクの説明（任意）
        due_date: 期限（任意）
        priority: 優先度（high/medium/low、デフォルト: medium）
        status: ステータス（pending/completed、デフォルト: pending）
        category: カテゴリ（work/personal/shopping/other）
        location: 位置情報（任意、天気取得用）
        created_at: 作成日時（自動設定）
        updated_at: 更新日時（自動更新）
    """
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(10), default='medium', nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    category = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    repeat_type = db.Column(db.String(20), default='none', nullable=False)  # none/daily/weekly/monthly
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)  # 繰り返しタスクの親タスクID
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> dict:
        """
        タスクを辞書形式に変換します。
        
        Returns:
            タスク情報を含む辞書
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'priority': self.priority,
            'status': self.status,
            'category': self.category,
            'location': self.location,
            'repeat_type': self.repeat_type,
            'parent_task_id': self.parent_task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f'<Task {self.id}: {self.title}>'







