#!/usr/bin/env python3
"""Tạo mã QR cho một đường link.

Hỗ trợ 3 định dạng (tự nhận theo đuôi file đầu ra):
  - .png : ảnh raster (mức sửa lỗi cao, hợp dán/chia sẻ online)
  - .svg : vector, nét vô hạn, in khổ lớn không vỡ
  - .pdf : vector, sẵn sàng đem in

Mã QR dùng vĩnh viễn, không hết hạn — chỉ cần link bên trong còn sống.
"""

import argparse
import os

import qrcode
from qrcode.constants import ERROR_CORRECT_H

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo mã QR (PNG/SVG/PDF) cho một link.")
    parser.add_argument("url", nargs="?", default=LINK_MAC_DINH,
                        help="Đường link cần tạo QR (mặc định là link Google Form).")
    parser.add_argument("-o", "--output", default="qr.png",
                        help="File đầu ra. Đuôi .png/.svg/.pdf quyết định định dạng.")
    parser.add_argument("--box-size", type=int, default=10,
                        help="Kích thước mỗi ô (px với PNG, point với PDF; mặc định 10).")
    parser.add_argument("--border", type=int, default=4,
                        help="Độ rộng viền tính theo số ô (mặc định 4).")
    args = parser.parse_args()

    ext = os.path.splitext(args.output)[1].lower()
    qr = _tao_qr(args.url, args.box_size, args.border)

    if ext == ".png":
        xuat_png(qr, args.output)
    elif ext == ".svg":
        xuat_svg(qr, args.output, args.box_size, args.border)
    elif ext == ".pdf":
        xuat_pdf(qr, args.output, args.box_size, args.border)
    else:
        parser.error(f"Định dạng không hỗ trợ: '{ext}'. Dùng .png, .svg hoặc .pdf")

    print(f"Đã tạo mã QR: {args.output}")
    print(f"Link mã hóa: {args.url}")


if __name__ == "__main__":
    main()
