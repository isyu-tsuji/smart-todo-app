"""
データベースマイグレーションスクリプト
Phase 3の新機能（repeat_type, parent_task_id）を既存のデータベースに追加します。
"""
from app import app, db
from sqlalchemy import text

def migrate_database():
    """
    データベースに新しいカラムを追加します。
    """
    with app.app_context():
        try:
            # SQLiteの場合、ALTER TABLEでカラムを追加
            with db.engine.connect() as conn:
                # repeat_typeカラムを追加（既に存在する場合はスキップ）
                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN repeat_type VARCHAR(20) DEFAULT 'none'"))
                    conn.commit()
                    print("✓ repeat_typeカラムを追加しました")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("✓ repeat_typeカラムは既に存在します")
                    else:
                        raise
                
                # parent_task_idカラムを追加（既に存在する場合はスキップ）
                try:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER"))
                    conn.commit()
                    print("✓ parent_task_idカラムを追加しました")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("✓ parent_task_idカラムは既に存在します")
                    else:
                        raise
                
                # 外部キー制約を追加（SQLiteでは制限があるため、スキップされる場合があります）
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id 
                        ON tasks(parent_task_id)
                    """))
                    conn.commit()
                    print("✓ parent_task_idのインデックスを作成しました")
                except Exception as e:
                    print(f"インデックスの作成で警告: {e}")
            
            print("\n✓ マイグレーションが完了しました！")
            
        except Exception as e:
            print(f"✗ マイグレーションエラー: {e}")
            print("\n既存のデータベースを削除して再作成する場合は、以下を実行してください:")
            print("  python -c \"from app import app, db; app.app_context().push(); db.drop_all(); db.create_all()\"")
            raise

if __name__ == '__main__':
    migrate_database()

