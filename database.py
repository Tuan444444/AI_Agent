# File: database.py
import sqlite3
import datetime

DB_NAME = "chat_history.db"

def init_db():
    """Khởi tạo Database nếu chưa có"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tạo bảng lịch sử: ID tự tăng, Session ID, Vai trò (User/AI), Nội dung, Thời gian
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(session_id, role, content):
    """Lưu tin nhắn mới vào DB"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO history (session_id, role, content) VALUES (?, ?, ?)", 
                  (session_id, role, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Lỗi lưu DB: {e}")

def get_chat_history(session_id, limit=10):
    """
    Lấy lịch sử chat để nạp vào Context cho AI.
    Trả về dạng chuỗi hội thoại.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Lấy 10 tin nhắn gần nhất của phiên này
    c.execute("""
        SELECT role, content FROM history 
        WHERE session_id = ? 
        ORDER BY id ASC
    """, (session_id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return ""

    # Format thành dạng hội thoại cho AI đọc
    history_str = ""
    for role, content in rows:
        speaker = "Khách hàng (Human)" if role == "user" else "AI Chuyên gia"
        history_str += f"{speaker}: {content}\n"
    
    return history_str

# Chạy khởi tạo ngay khi import
init_db()
# ... (Giữ nguyên các hàm init_db, save_message...)

def get_history_for_frontend(session_id):
    """
    Lấy lịch sử trả về dạng List Dictionary để Frontend hiển thị.
    Output: [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Lấy toàn bộ tin nhắn của session đó, sắp xếp theo thời gian
    c.execute("SELECT role, content FROM history WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = c.fetchall()
    conn.close()

    messages = []
    for role, content in rows:
        # Map role từ DB ('ai') sang chuẩn Streamlit ('assistant')
        ui_role = "assistant" if role == "ai" else "user"
        messages.append({"role": ui_role, "content": content})
        
    return messages
# --- FILE: database.py ---

# ... (Giữ nguyên các hàm cũ) ...

def check_session_exists(session_id):
    """
    Kiểm tra xem session_id này đã từng có tin nhắn chưa.
    Trả về: True (Đã tồn tại) / False (Chưa có)
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM history WHERE session_id = ? LIMIT 1", (session_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists