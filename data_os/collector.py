import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get('DATABASE_PATH', './data/aios.db')

def record_metric(name, value, unit=None, category=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO metrics (name, value, unit, category, recorded_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, value, unit, category, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_metrics(category=None, days=30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if category:
        cursor.execute('''
            SELECT name, value, unit, recorded_at 
            FROM metrics 
            WHERE category = ? AND recorded_at >= datetime('now', '-' || ? || ' days')
            ORDER BY recorded_at DESC
        ''', (category, days))
    else:
        cursor.execute('''
            SELECT name, value, unit, recorded_at 
            FROM metrics 
            WHERE recorded_at >= datetime('now', '-' || ? || ' days')
            ORDER BY recorded_at DESC
        ''', (days,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def add_task(title, description=None, priority='medium', due_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (title, description, priority, due_date)
        VALUES (?, ?, ?, ?)
    ''', (title, description, priority, due_date))
    
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def get_tasks(status=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if status:
        cursor.execute('''
            SELECT id, title, description, status, priority, due_date, created_at
            FROM tasks 
            WHERE status = ?
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                created_at DESC
        ''', (status,))
    else:
        cursor.execute('''
            SELECT id, title, description, status, priority, due_date, created_at
            FROM tasks 
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                created_at DESC
        ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def complete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE tasks 
        SET status = 'completed', completed_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), task_id))
    
    conn.commit()
    conn.close()

def add_note(title, content, source='manual', tags=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO notes (title, content, source, tags)
        VALUES (?, ?, ?, ?)
    ''', (title, content, source, tags))
    
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return note_id

def get_recent_notes(days=7):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, content, source, tags, created_at
        FROM notes
        WHERE created_at >= datetime('now', '-' || ? || ' days')
        ORDER BY created_at DESC
    ''', (days,))
    
    results = cursor.fetchall()
    conn.close()
    return results

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python collector.py <command> [args]")
        print("Commands:")
        print("  metric <name> <value> [unit] [category]")
        print("  task <title> [description] [priority] [due_date]")
        print("  note <title> <content> [tags]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'metric':
        name = sys.argv[2]
        value = sys.argv[3]
        unit = sys.argv[4] if len(sys.argv) > 4 else None
        category = sys.argv[5] if len(sys.argv) > 5 else None
        record_metric(name, float(value), unit, category)
        print(f"Metric recorded: {name} = {value} {unit or ''}")
    
    elif cmd == 'task':
        title = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else None
        priority = sys.argv[4] if len(sys.argv) > 4 else 'medium'
        due_date = sys.argv[5] if len(sys.argv) > 5 else None
        task_id = add_task(title, description, priority, due_date)
        print(f"Task created: {task_id}")
    
    elif cmd == 'note':
        title = sys.argv[2]
        content = sys.argv[3]
        tags = sys.argv[4] if len(sys.argv) > 4 else None
        note_id = add_note(title, content, 'manual', tags)
        print(f"Note created: {note_id}")