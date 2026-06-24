#!/usr/bin/env python3
"""Tạo và quản lý mã QR cho một đường link (Tĩnh & Động).

Hỗ trợ 3 định dạng (tự nhận theo đuôi file đầu ra):
  - .png : ảnh raster (mức sửa lỗi cao, hợp dán/chia sẻ online)
  - .svg : vector, nét vô hạn, in khổ lớn không vỡ
  - .pdf : vector, sẵn sàng đem in

Đối với mã QR Động, link bên trong mã QR sẽ dẫn tới một server chuyển hướng trung gian.
Bạn có thể thay đổi link đích thực tế bất kỳ lúc nào qua dòng lệnh mà không phải in lại QR.
"""

import argparse
import os
import random
import string
import sys

import qrcode
from qrcode.constants import ERROR_CORRECT_H

# Import module quản lý database của chúng ta
import db

LINK_MAC_DINH = "YOUR_URL_LINK"


def _tao_qr(url: str, box_size: int, border: int) -> qrcode.QRCode:
    qr = qrcode.QRCode(
        version=None,                      # tự chọn kích thước nhỏ nhất vừa dữ liệu
        error_correction=ERROR_CORRECT_H,  # mức sửa lỗi cao nhất (~30%)
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr


def xuat_png(qr: qrcode.QRCode, output: str) -> None:
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output)


def xuat_svg(qr: qrcode.QRCode, output: str, box_size: int, border: int) -> None:
    """Vẽ SVG vector từ ma trận QR (mỗi ô đen là 1 hình vuông)."""
    matrix = qr.get_matrix()
    n = len(matrix)
    size = (n + 2 * border) * box_size  # kích thước cạnh ảnh (đơn vị user-unit)

    rects = []
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if val:
                x = (c + border) * box_size
                y = (r + border) * box_size
                rects.append(
                    f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}"/>'
                )

    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'shape-rendering="crispEdges">\n'
        f'<rect width="{size}" height="{size}" fill="#ffffff"/>\n'
        f'<g fill="#000000">{"".join(rects)}</g>\n'
        f'</svg>\n'
    )
    with open(output, "w", encoding="utf-8") as f:
        f.write(svg)


def xuat_pdf(qr: qrcode.QRCode, output: str, box_size: int, border: int) -> None:
    """Vẽ PDF vector từ ma trận QR bằng reportlab."""
    from reportlab.pdfgen import canvas

    matrix = qr.get_matrix()
    n = len(matrix)
    size = (n + 2 * border) * box_size  # cạnh ảnh tính theo point (1/72 inch)

    c = canvas.Canvas(output, pagesize=(size, size))
    # Nền trắng
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, size, size, fill=1, stroke=0)
    # Các ô đen. Lưu ý: PDF gốc tọa độ ở góc dưới-trái nên lật trục y.
    c.setFillColorRGB(0, 0, 0)
    for r, row in enumerate(matrix):
        for col, val in enumerate(row):
            if val:
                x = (col + border) * box_size
                y = size - (r + 1 + border) * box_size
                c.rect(x, y, box_size, box_size, fill=1, stroke=0)
    c.showPage()
    c.save()


def _sinh_id_ngau_nhien(length: int = 8) -> str:
    """Sinh một mã ID ngẫu nhiên không trùng lặp cho QR động."""
    ky_tu = string.ascii_lowercase + string.digits
    while True:
        qr_id = "".join(random.choice(ky_tu) for _ in range(length))
        # Kiểm tra xem ID đã tồn tại trong DB chưa
        if not db.get_redirect(qr_id):
            return qr_id


def hien_thi_danh_sach() -> None:
    """Liệt kê toàn bộ mã QR động trong DB ra màn hình dạng bảng."""
    db.init_db()
    redirects = db.list_redirects()
    if not redirects:
        print("Chưa có mã QR động nào được tạo trong hệ thống.")
        return

    print("-" * 100)
    print(f"{'ID QR động':<12} | {'Lượt quét':<9} | {'Ngày tạo':<19} | {'Liên kết đích hiện tại'}")
    print("-" * 100)
    for item in redirects:
        # Định dạng ngày tháng
        created = item['created_at']
        print(f"{item['id']:<12} | {item['clicks']:<9} | {created:<19} | {item['target_url']}")
    print("-" * 100)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tạo mã QR (PNG/SVG/PDF) tĩnh hoặc động và quản lý chúng."
    )
    
    # Các tham số cơ bản
    parser.add_argument("url", nargs="?", default=LINK_MAC_DINH,
                        help="Đường link cần mã hóa (mặc định: Google Form). Với --update, đây là link đích mới.")
    parser.add_argument("-o", "--output", default="qr.png",
                        help="File ảnh QR đầu ra (.png/.svg/.pdf; mặc định: qr.png).")
    parser.add_argument("--box-size", type=int, default=10,
                        help="Kích thước mỗi ô (px đối với PNG, point đối với PDF; mặc định: 10).")
    parser.add_argument("--border", type=int, default=4,
                        help="Độ rộng viền theo số ô (mặc định: 4).")

    # Các tùy chọn cho QR động
    parser.add_argument("-d", "--dynamic", action="store_true",
                        help="Tạo mã QR động. Link mã hóa trong QR sẽ trỏ về server chuyển hướng.")
    parser.add_argument("--base-url", default="http://localhost:5000",
                        help="Địa chỉ cơ sở của máy chủ chuyển hướng (mặc định: http://localhost:5000).")
    parser.add_argument("-u", "--update", metavar="ID",
                        help="Cập nhật link đích mới cho mã QR động có ID tương ứng. Cần truyền kèm tham số 'url'.")
    parser.add_argument("-l", "--list", action="store_true",
                        help="Liệt kê danh sách tất cả các mã QR động đã tạo kèm thống kê lượt quét.")
    parser.add_argument("--delete", metavar="ID",
                        help="Xóa một mã QR động khỏi cơ sở dữ liệu dựa trên ID.")

    args = parser.parse_args()

    # 1. Xử lý yêu cầu liệt kê danh sách
    if args.list:
        hien_thi_danh_sach()
        return

    # 2. Xử lý yêu cầu xóa mã QR động
    if args.delete:
        db.init_db()
        success = db.delete_redirect(args.delete)
        if success:
            print(f"Đã xóa thành công mã QR động có ID: {args.delete}")
        else:
            print(f"Lỗi: Không tìm thấy mã QR động có ID: {args.delete}", file=sys.stderr)
        return

    # 3. Xử lý yêu cầu cập nhật liên kết đích
    if args.update:
        db.init_db()
        existing = db.get_redirect(args.update)
        if not existing:
            print(f"Lỗi: Không tìm thấy mã QR động có ID: {args.update}", file=sys.stderr)
            sys.exit(1)
        
        # Cập nhật DB
        db.update_redirect(args.update, args.url)
        print(f"Đã cập nhật thành công link đích cho QR ID '{args.update}':")
        print(f"  - Từ: {existing['target_url']}")
        print(f"  - Sang: {args.url}")
        return

    # 4. Tạo mã QR mới (Tĩnh hoặc Động)
    ext = os.path.splitext(args.output)[1].lower()
    if ext not in [".png", ".svg", ".pdf"]:
        parser.error(f"Định dạng không hỗ trợ: '{ext}'. Dùng .png, .svg hoặc .pdf")

    if args.dynamic:
        db.init_db()
        # Sinh ID động mới
        qr_id = _sinh_id_ngau_nhien()
        # Lưu vào SQLite
        db.create_redirect(qr_id, args.url)
        # Link chuyển hướng sẽ được ghi vào mã QR
        base = args.base_url.rstrip("/")
        ma_hoa_url = f"{base}/r/{qr_id}"
    else:
        # QR tĩnh mã hóa trực tiếp url đích
        qr_id = None
        ma_hoa_url = args.url

    # Tạo đối tượng QR
    qr = _tao_qr(ma_hoa_url, args.box_size, args.border)

    # Xuất file tương ứng
    if ext == ".png":
        xuat_png(qr, args.output)
    elif ext == ".svg":
        xuat_svg(qr, args.output, args.box_size, args.border)
    elif ext == ".pdf":
        xuat_pdf(qr, args.output, args.box_size, args.border)

    # In kết quả báo cáo
    print(f"Đã tạo thành công mã QR: {args.output}")
    if args.dynamic:
        print(f"Loại QR: ĐỘNG (Dynamic)")
        print(f"ID QR động: {qr_id}")
        print(f"Link được mã hóa trong QR: {ma_hoa_url}")
        print(f"Link đích thực tế: {args.url}")
        print(f"-> Mẹo: Khởi chạy máy chủ 'python3 server.py' để bắt đầu chuyển hướng quét.")
    else:
        print(f"Loại QR: TĨNH (Static)")
        print(f"Link được mã hóa trong QR: {ma_hoa_url}")


if __name__ == "__main__":
    main()
