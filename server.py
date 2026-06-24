import sys
from flask import Flask, redirect, abort, render_template_string

import db

app = Flask(__name__)

db.init_db()

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mã QR không tồn tại</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f7f9fc;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #e74c3c;
            margin-bottom: 10px;
            font-size: 24px;
        }
        p {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        .btn {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 6px;
            transition: background-color 0.2s;
        }
        .btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Lỗi: Không tìm thấy liên kết</h1>
        <p>Mã QR ID <strong>{{ qr_id }}</strong> không tồn tại hoặc đã bị xóa khỏi hệ thống chuyển hướng.</p>
        <p>Vui lòng kiểm tra lại mã QR hoặc liên hệ với người quản trị.</p>
    </div>
</body>
</html>
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Code Redirect Server</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f2f5;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            background: white;
            padding: 50px;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 28px;
        }
        p {
            color: #7f8c8d;
            margin-bottom: 25px;
            line-height: 1.6;
        }
        .status-badge {
            display: inline-block;
            background-color: #2ecc71;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>QR Redirect Server</h1>
        <p>Máy chủ chuyển hướng mã QR động đang hoạt động bình thường.</p>
        <span class="status-badge">Active</span>
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE)


@app.route("/r/<qr_id>")
def redirect_to_target(qr_id):
    redirect_info = db.get_redirect(qr_id)
    if not redirect_info:
        return render_template_string(ERROR_TEMPLATE, qr_id=qr_id), 404

    # Tăng số lượt quét
    db.increment_clicks(qr_id)

    target_url = redirect_info["target_url"]

    # Đảm bảo target_url có schema http hoặc https
    if not target_url.startswith(("http://", "https://")):
        target_url = "http://" + target_url

    return redirect(target_url, code=302)


if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    print(f"Khởi động Server chuyển hướng QR động tại http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
