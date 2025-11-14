#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import psycopg2
import os

class DatabaseHandler:
    def __init__(self):
        self.conn = None
        
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host="db",
                database="mydb", 
                user="postgres",
                password="password",
                port=5432
            )
            print("✅ Подключились к PostgreSQL!")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            return False
    
    def init_db(self):
        if self.connect():
            try:
                cur = self.conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS visits (
                        id SERIAL PRIMARY KEY,
                        page VARCHAR(255),
                        visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.conn.commit()
                cur.close()
                print("✅ База данных готова!")
            except Exception as e:
                print(f"❌ Ошибка создания таблицы: {e}")

db = DatabaseHandler()

class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Логируем посещение
        self.log_visit()
        
        if self.path == '/':
            self.show_main_page()
        elif self.path == '/stats':
            self.show_stats()
        elif self.path == '/api/health':
            self.show_health()
        else:
            self.show_404()
    
    def log_visit(self):
        print(f"📝 Логируем посещение: {self.path}")
        if db.connect():
            try:
                cur = db.conn.cursor()
                cur.execute(
                    "INSERT INTO visits (page) VALUES (%s)",
                    (self.path,)
                )
                db.conn.commit()
                cur.close()
                print(f"✅ Записали в БД: {self.path}")
            except Exception as e:
                print(f"❌ Ошибка записи в БД: {e}")
        else:
            print("❌ Не удалось подключиться к БД")
    
    def show_main_page(self):
        visit_count = self.get_visit_count()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = f"""
        <html>
        <head><title>Моё приложение с БД</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h1>🎊 ПРИЛОЖЕНИЕ С БАЗОЙ ДАННЫХ</h1>
            <p><b>Всего посещений:</b> {visit_count}</p>
            <p><b>Текущее время:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><b>Путь:</b> {self.path}</p>
            
            <div style="margin-top: 20px;">
                <a href="/stats" style="padding: 10px; background: #4CAF50; color: white; text-decoration: none;">
                    📈 Посмотреть статистику
                </a>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
        print(f"📊 Показали главную. Посещений: {visit_count}")
    
    def show_stats(self):
        stats = self.get_visit_stats()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        stats_html = ""
        for stat in stats:
            stats_html += f"<li>{stat['page']}: {stat['count']} посещений</li>"
        
        html = f"""
        <html>
        <body style="font-family: Arial; margin: 40px;">
            <h1>📈 Статистика посещений</h1>
            <a href="/">← Назад</a>
            <ul>{stats_html}</ul>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
        print(f"📈 Показали статистику: {stats}")
    
    def get_visit_count(self):
        if db.connect():
            try:
                cur = db.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM visits")
                count = cur.fetchone()[0]
                cur.close()
                return count
            except Exception as e:
                print(f"❌ Ошибка получения статистики: {e}")
        return 0
    
    def get_visit_stats(self):
        if db.connect():
            try:
                cur = db.conn.cursor()
                cur.execute("""
                    SELECT page, COUNT(*) as count 
                    FROM visits 
                    GROUP BY page 
                    ORDER BY count DESC
                """)
                stats = [{"page": row[0], "count": row[1]} for row in cur.fetchall()]
                cur.close()
                return stats
            except Exception as e:
                print(f"❌ Ошибка получения статистики: {e}")
        return [{"page": "Ошибка", "count": 0}]
    
    def show_health(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        db_status = "connected" if db.connect() else "disconnected"
        response = {
            "status": "healthy",
            "timestamp": time.time(),
            "database": db_status
        }
        self.wfile.write(json.dumps(response).encode())
    
    def show_404(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 - Page not found")

if __name__ == '__main__':
    print("🚀 Запускаю веб-сервер с БД...")
    db.init_db()
    print("🌐 Сервер запущен на http://0.0.0.0:8000")
    server = HTTPServer(('0.0.0.0', 8000), WebHandler)
    server.serve_forever()

