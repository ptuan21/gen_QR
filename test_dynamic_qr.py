import os
import unittest
from server import app
import db


class TestDynamicQR(unittest.TestCase):

    def setUp(self):
        # Đảm bảo database đã được tạo và làm sạch trước mỗi test
        db.init_db()
        # Xóa các bản ghi cũ nếu có để tránh ảnh hưởng đến test
        with db.get_db_connection() as conn:
            conn.execute("DELETE FROM qr_redirects")
            conn.commit()

        # Tạo Flask test client
        app.testing = True
        self.client = app.test_client()

    def test_database_crud(self):
        """Kiểm tra các thao tác CRUD cơ bản trên DB."""
        # 1. Tạo mới
        success = db.create_redirect("test_id", "https://google.com")
        self.assertTrue(success)

        # Trùng ID không cho tạo
        fail = db.create_redirect("test_id", "https://yahoo.com")
        self.assertFalse(fail)

        # 2. Đọc thông tin
        data = db.get_redirect("test_id")
        self.assertIsNotNone(data)
        self.assertEqual(data["target_url"], "https://google.com")
        self.assertEqual(data["clicks"], 0)

        # 3. Cập nhật
        update_success = db.update_redirect("test_id", "https://github.com")
        self.assertTrue(update_success)
        
        data_after_update = db.get_redirect("test_id")
        self.assertEqual(data_after_update["target_url"], "https://github.com")

        # 4. Liệt kê danh sách
        db.create_redirect("test_id_2", "https://youtube.com")
        redirects = db.list_redirects()
        self.assertEqual(len(redirects), 2)
        
        # 5. Xóa
        delete_success = db.delete_redirect("test_id")
        self.assertTrue(delete_success)
        self.assertIsNone(db.get_redirect("test_id"))

    def test_redirect_server(self):
        """Kiểm tra chức năng chuyển hướng của server Flask."""
        # Tạo sẵn bản ghi trong DB
        db.create_redirect("my_link", "https://openai.com")

        # 1. Test trường hợp QR ID không tồn tại (lỗi 404)
        response_404 = self.client.get("/r/invalid_id")
        self.assertEqual(response_404.status_code, 404)
        self.assertIn("Không tìm thấy", response_404.data.decode("utf-8"))

        # 2. Test trường hợp chuyển hướng thành công (302)
        response_302 = self.client.get("/r/my_link")
        self.assertEqual(response_302.status_code, 302)
        self.assertEqual(response_302.headers["Location"], "https://openai.com")

        # Kiểm tra lượt click tăng lên
        data = db.get_redirect("my_link")
        self.assertEqual(data["clicks"], 1)

        # Quét lần 2
        self.client.get("/r/my_link")
        data = db.get_redirect("my_link")
        self.assertEqual(data["clicks"], 2)


if __name__ == "__main__":
    unittest.main()
