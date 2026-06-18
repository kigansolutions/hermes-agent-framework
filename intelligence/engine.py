import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.environ.get('DATABASE_PATH', './data/aios.db')

def get_context_summary():
    context_files = {
        'business': './context/business.md',
        'products': './context/products.md',
        'processes': './context/processes.md',
        'goals': './context/goals.md'
    }
    
    summary = {}
    for key, path in context_files.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                summary[key] = f.read()
    
    return summary

def get_tasks_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT status, COUNT(*) FROM tasks GROUP BY status
    ''')
    status_counts = dict(cursor.fetchall())
    
    cursor.execute('''
        SELECT priority, COUNT(*) FROM tasks WHERE status = 'pending' GROUP BY priority
    ''')
    pending_by_priority = dict(cursor.fetchall())
    
    cursor.execute('''
        SELECT title, priority, due_date FROM tasks 
        WHERE status = 'pending' AND due_date IS NOT NULL
        AND due_date <= datetime('now', '+3 days')
        ORDER BY due_date
        LIMIT 5
    ''')
    upcoming = cursor.fetchall()
    
    conn.close()
    
    return {
        'status_counts': status_counts,
        'pending_by_priority': pending_by_priority,
        'upcoming': [{'title': t[0], 'priority': t[1], 'due_date': t[2]} for t in upcoming]
    }

def get_metrics_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, value, unit, recorded_at FROM metrics
        WHERE recorded_at >= datetime('now', '-7 days')
        ORDER BY recorded_at DESC
        LIMIT 20
    ''')
    recent = cursor.fetchall()
    
    cursor.execute('''
        SELECT category, COUNT(*) FROM metrics 
        WHERE recorded_at >= datetime('now', '-30 days')
        GROUP BY category
    ''')
    by_category = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        'recent': [{'name': m[0], 'value': m[1], 'unit': m[2], 'recorded_at': m[3]} for m in recent],
        'by_category': by_category
    }

def get_recent_notes_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, content, source, created_at FROM notes
        WHERE created_at >= datetime('now', '-7 days')
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    
    notes = cursor.fetchall()
    conn.close()
    
    return [{'title': n[0], 'content': n[1], 'source': n[2], 'created_at': n[3]} for n in notes]

def generate_brief_data():
    return {
        'generated_at': datetime.now().isoformat(),
        'context': get_context_summary(),
        'tasks': get_tasks_summary(),
        'metrics': get_metrics_summary(),
        'notes': get_recent_notes_summary()
    }

def save_brief(content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO daily_briefs (content, generated_at)
        VALUES (?, ?)
    ''', (content, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    data = generate_brief_data()
    print(json.dumps(data, indent=2))