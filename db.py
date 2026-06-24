import os
import sqlite3
from datetime import datetime
from typing import Optional, List

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qr_database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Khởi tạo bảng cơ sở dữ liệu nếu chưa tồn tại."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS qr_redirects (
                id TEXT PRIMARY KEY,
                target_url TEXT NOT NULL,
                clicks INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def get_redirect(qr_id: str) -> Optional[dict]:
    """Lấy thông tin của một mã QR từ ID."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, target_url, clicks, created_at FROM qr_redirects WHERE id = ?",
            (qr_id,),
        ).fetchone()
        if row:
            return dict(row)
        return None


def create_redirect(qr_id: str, target_url: str) -> bool:
    """Tạo mới một bản ghi chuyển hướng QR động."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO qr_redirects (id, target_url, clicks) VALUES (?, ?, 0)",
                (qr_id, target_url),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


def update_redirect(qr_id: str, target_url: str) -> bool:
    """Cập nhật đường dẫn đích mới cho QR ID hiện tại."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "UPDATE qr_redirects SET target_url = ? WHERE id = ?",
            (target_url, qr_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_redirect(qr_id: str) -> bool:
    """Xóa bỏ một QR ID khỏi cơ sở dữ liệu."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM qr_redirects WHERE id = ?",
            (qr_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_redirects() -> List[dict]:
    """Liệt kê toàn bộ danh sách QR động."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, target_url, clicks, created_at FROM qr_redirects ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def increment_clicks(qr_id: str) -> bool:
    """Tăng số lượt click/quét cho QR ID tương ứng."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "UPDATE qr_redirects SET clicks = clicks + 1 WHERE id = ?",
            (qr_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
