
import sys
import math
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QFileDialog, QMessageBox, QFrame, QScrollArea,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

SKIMAGE_AVAILABLE = False


class ComparisonDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.setWindowTitle("Perbandingan Hasil Uji")
        self.resize(1180, 760)
        self.setStyleSheet("background-color: #f5f7fb;")
        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        title = QLabel("Perbandingan Hasil Deteksi MRI Tumor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1f2937; border:none;")
        main_layout.addWidget(title)

        subtitle = QLabel(
            "Popup ini menampilkan 2 gambar hasil uji yang sudah disimpan, lalu dibandingkan bersama data area, titik pusat, dan lokasi tumor."
        )
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #475569; border:none;")
        main_layout.addWidget(subtitle)

        images_row = QHBoxLayout()
        images_row.setSpacing(16)
        for idx, item in enumerate(self.results, 1):
            images_row.addWidget(self.build_result_card(idx, item))
        main_layout.addLayout(images_row)

        table_card = QFrame()
        table_card.setStyleSheet("QFrame { background-color: white; border: 2px solid #d5dde8; border-radius: 18px; }")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(14, 14, 14, 14)
        table_layout.setSpacing(10)

        table_title = QLabel("Tabel Perbandingan")
        table_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #203040; border:none;")
        table_layout.addWidget(table_title)

        table = QTableWidget(len(self.results), 8)
        table.setHorizontalHeaderLabels([
            "No", "Kelas", "Status", "Luas px", "Luas cm²",
            "Diameter cm", "Titik Pusat", "Lokasi"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            "QTableWidget { background-color:white; font-size:12px; gridline-color:#dfe7f1; }"
            "QHeaderView::section { background-color:#3b6af3; color:white; font-weight:800; padding:7px; border:none; }"
        )

        for row, item in enumerate(self.results):
            values = [
                str(row + 1),
                item.get("mode", "-"),
                item.get("status", "-"),
                str(item.get("area_px", "-")),
                str(item.get("area_cm2", "-")),
                str(item.get("diameter_cm", "-")),
                str(item.get("center", "-")),
                str(item.get("lokasi", "-")),
            ]
            for col, val in enumerate(values):
                qitem = QTableWidgetItem(val)
                qitem.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, qitem)
        table_layout.addWidget(table)
        main_layout.addWidget(table_card)

        conclusion = QLabel(self.build_summary_text())
        conclusion.setWordWrap(True)
        conclusion.setStyleSheet(
            "background-color: white; border: 2px solid #d5dde8; border-radius: 16px; padding: 12px;"
            "font-size: 12px; color:#2c3e50; font-weight: 700;"
        )
        main_layout.addWidget(conclusion)

        close_btn = QPushButton("Tutup")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(140, 40)
        close_btn.setStyleSheet(
            "QPushButton { background-color:#3b6af3; color:white; font-weight:800; border:none; border-radius:20px; }"
            "QPushButton:hover { background-color:#2a52cf; }"
        )
        close_btn.clicked.connect(self.accept)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(close_btn)
        footer.addStretch()
        main_layout.addLayout(footer)

    def build_result_card(self, idx, item):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: white; border: 2px solid #d5dde8; border-radius: 18px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel(f"Hasil Uji {idx} - {item.get('mode', '-')}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #203040; border:none;")
        layout.addWidget(title)

        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setFixedSize(500, 260)
        lbl_img.setStyleSheet(
            "background-color:#f8fafc; border: 2px solid #dbe4f0; border-radius: 14px; color:#64748b;"
        )

        preview = item.get("result_preview")
        if preview is None:
            preview = item.get("original_preview")
        if preview is not None:
            lbl_img.setPixmap(self.cv2_to_pixmap(preview, lbl_img.width(), lbl_img.height()))
        else:
            lbl_img.setText("Preview tidak tersedia")
        layout.addWidget(lbl_img)

        info = QLabel(
            f"Status: {item.get('status', '-')}\n"
            f"Titik pusat: {item.get('center', '-')}\n"
            f"Luas: {item.get('area_px', '-')} px | {item.get('area_cm2', '-')} cm²"
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 12px; color:#334155; font-weight:700; border:none;")
        layout.addWidget(info)
        return card

    def build_summary_text(self):
        if len(self.results) < 2:
            return "Kesimpulan: data uji minimal 2 gambar diperlukan untuk perbandingan."

        a = self.results[0]
        b = self.results[1]
        area_a = int(a.get("area_px", 0)) if str(a.get("area_px", "0")).isdigit() else 0
        area_b = int(b.get("area_px", 0)) if str(b.get("area_px", "0")).isdigit() else 0

        if area_a > 0 and area_b == 0:
            detail = "Hasil uji kedua menunjukkan tidak ada tumor terdeteksi, sehingga dapat dipakai sebagai contoh perbaikan kondisi pasien setelah follow-up." \
                     " Ini cocok untuk skenario pasien sebelumnya masih terdeteksi glioma, kemudian setelah operasi hasilnya bersih."
        elif area_a == 0 and area_b > 0:
            detail = "Hasil uji kedua menunjukkan area tumor muncul/masih terdeteksi, sehingga kondisi perlu dipantau lebih lanjut."
        elif area_b < area_a:
            detail = "Luas area pada hasil uji kedua lebih kecil dibanding hasil pertama, sehingga secara visual terlihat adanya penurunan area kandidat tumor."
        elif area_b > area_a:
            detail = "Luas area pada hasil uji kedua lebih besar dibanding hasil pertama, sehingga secara visual terlihat peningkatan area kandidat tumor."
        else:
            detail = "Nilai area kedua hasil uji relatif sama, sehingga kondisi visual terlihat stabil pada dua pemeriksaan."

        return (
            "Kesimpulan Perbandingan:\n"
            f"- Hasil uji 1: {a.get('mode', '-')} | status: {a.get('status', '-')}\n"
            f"- Hasil uji 2: {b.get('mode', '-')} | status: {b.get('status', '-')}\n"
            f"- {detail}"
        )

    @staticmethod
    def cv2_to_pixmap(cv_img, target_w, target_h):
        safe_img = np.ascontiguousarray(cv_img)
        if len(safe_img.shape) == 2:
            h, w = safe_img.shape
            q_img = QImage(safe_img.data, w, h, w, QImage.Format_Grayscale8)
        else:
            h, w, ch = safe_img.shape
            q_img = QImage(safe_img.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img).scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class DeteksiTumorApp(QMainWindow):
    PIXEL_TO_CM = 0.026

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MRI Tumor Tracker - Skull Stripping + Contour Refinement")
        self.setGeometry(30, 30, 1420, 820)
        self.setStyleSheet("background-color: #f0f4f8;")

        self.img_bgr = None
        self.final_result_img = None
        self.mode = "Meningioma"
        self.menu_buttons = {}

        self.last_result_data = None
        self.comparison_results = []

        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout_utama = QHBoxLayout(main_widget)
        layout_utama.setContentsMargins(20, 20, 20, 20)
        layout_utama.setSpacing(20)

        sidebar = QFrame()
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("QFrame { background-color: #e4ebf3; border-radius: 22px; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 28, 15, 28)
        sidebar_layout.setSpacing(14)

        lbl_judul = QLabel("🧠 MRI Tumor\nTracker")
        lbl_judul.setAlignment(Qt.AlignCenter)
        lbl_judul.setStyleSheet("font-size: 19px; font-weight: 800; color: #203040; border: none;")
        sidebar_layout.addWidget(lbl_judul)
        sidebar_layout.addSpacing(18)

        menus = ["Meningioma", "Glioma", "No Tumor"]
        for menu in menus:
            btn = QPushButton(menu)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, m=menu: self.ubah_mode(m))
            self.menu_buttons[menu] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        note = QLabel("Dataset:\nKaggle Brain Tumor MRI\n\nKelas dipakai:\nMeningioma, Glioma,\nNo Tumor")
        note.setWordWrap(True)
        note.setStyleSheet(
            "background-color: white; color: #34495e; border-radius: 14px; padding: 12px; font-size: 11px; font-weight: 600;"
        )
        sidebar_layout.addWidget(note)

        layout_utama.addWidget(sidebar)
        self.refresh_menu_style()

        konten_kanan = QVBoxLayout()
        konten_kanan.setSpacing(18)

        title = QLabel("Deteksi Tumor MRI - Skull Stripping + Contour Refinement")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 23px; font-weight: 900; color: #17202a; padding: 6px; border: none;")
        konten_kanan.addWidget(title)

        baris_atas = QHBoxLayout()
        baris_atas.setSpacing(18)
        self.panel_asli, self.lbl_asli = self.buat_panel_gambar("1. Gambar Asli", 255)
        self.panel_masking, self.lbl_masking = self.buat_panel_gambar("2. Masking / Skull Stripping", 255)
        self.panel_thresh, self.lbl_thresh = self.buat_panel_gambar("3. Threshold Candidate", 255)
        baris_atas.addWidget(self.panel_asli)
        baris_atas.addWidget(self.panel_masking)
        baris_atas.addWidget(self.panel_thresh)
        konten_kanan.addLayout(baris_atas)

        baris_bawah = QHBoxLayout()
        baris_bawah.setSpacing(18)

        panel_slider = QVBoxLayout()
        panel_slider.setSpacing(15)
        panel_slider.setAlignment(Qt.AlignTop)

        self.slider_thresh, self.lbl_val_th = self.buat_slider_ui("Batas Kecerahan", 0, 255, 0, "0 = Otsu")
        self.slider_circ, self.lbl_val_circ = self.buat_slider_ui("Toleransi Bentuk", 1, 90, 15, "semakin besar semakin selektif")
        self.slider_area, self.lbl_val_area = self.buat_slider_ui("Minimum Area Tumor", 50, 12000, 250, "filter noise kecil")
        panel_slider.addLayout(self.slider_thresh)
        panel_slider.addLayout(self.slider_circ)
        panel_slider.addLayout(self.slider_area)
        panel_slider.addSpacing(12)

        self.lbl_info_klinis = QLabel("📊 Data Klinis Tumor:\n\nMenunggu gambar MRI...")
        self.lbl_info_klinis.setWordWrap(True)
        self.lbl_info_klinis.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl_info_klinis.setStyleSheet(
            "background-color: white; border: none; padding: 14px; font-size: 12px; color: #2c3e50; font-weight: 700;"
        )

        self.scroll_info_klinis = QScrollArea()
        self.scroll_info_klinis.setWidgetResizable(True)
        self.scroll_info_klinis.setWidget(self.lbl_info_klinis)
        self.scroll_info_klinis.setMinimumHeight(205)
        self.scroll_info_klinis.setMaximumHeight(245)
        self.scroll_info_klinis.setStyleSheet(
            "QScrollArea { background-color: white; border: 2px solid #d5dde8; border-radius: 16px; }"
            "QScrollBar:vertical { background: #eef3f8; width: 10px; margin: 8px 2px 8px 2px; border-radius: 5px; }"
            "QScrollBar::handle:vertical { background: #3b6af3; min-height: 25px; border-radius: 5px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )
        panel_slider.addWidget(self.scroll_info_klinis)

        self.panel_final, self.lbl_final = self.buat_panel_gambar("4. Final Detection", 285)
        self.panel_zoom, self.lbl_zoom = self.buat_panel_gambar("5. Zoom Area Tumor", 285)

        panel_hasil = QHBoxLayout()
        panel_hasil.setSpacing(18)
        panel_hasil.addWidget(self.panel_final)
        panel_hasil.addWidget(self.panel_zoom)

        panel_kanan = QVBoxLayout()
        panel_kanan.setAlignment(Qt.AlignCenter)
        panel_kanan.setSpacing(12)

        btn_upload = QPushButton("Upload MRI")
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.setFixedSize(170, 42)
        btn_upload.setStyleSheet(self.style_button("#3b6af3", "#2a52cf"))
        btn_upload.clicked.connect(self.upload_gambar)

        self.btn_download = QPushButton("Download Hasil")
        self.btn_download.setCursor(Qt.PointingHandCursor)
        self.btn_download.setFixedSize(170, 42)
        self.btn_download.setEnabled(False)
        self.btn_download.setStyleSheet(self.style_button("#e74c3c", "#c0392b", disabled="#f5a29a"))
        self.btn_download.clicked.connect(self.download_gambar)

        self.btn_save_compare = QPushButton("Simpan Uji")
        self.btn_save_compare.setCursor(Qt.PointingHandCursor)
        self.btn_save_compare.setFixedSize(170, 38)
        self.btn_save_compare.setEnabled(False)
        self.btn_save_compare.setStyleSheet(self.style_button("#16a085", "#138d75", disabled="#a9dfbf"))
        self.btn_save_compare.clicked.connect(self.simpan_hasil_uji)

        self.btn_show_compare = QPushButton("Lihat Perbandingan")
        self.btn_show_compare.setCursor(Qt.PointingHandCursor)
        self.btn_show_compare.setFixedSize(170, 38)
        self.btn_show_compare.setEnabled(False)
        self.btn_show_compare.setStyleSheet(self.style_button("#7f8c8d", "#626567", disabled="#bdc3c7"))
        self.btn_show_compare.clicked.connect(self.tampilkan_perbandingan)

        self.btn_reset_compare = QPushButton("Reset Perbandingan")
        self.btn_reset_compare.setCursor(Qt.PointingHandCursor)
        self.btn_reset_compare.setFixedSize(170, 38)
        self.btn_reset_compare.setEnabled(False)
        self.btn_reset_compare.setStyleSheet(self.style_button("#95a5a6", "#7f8c8d", disabled="#d5dbdb"))
        self.btn_reset_compare.clicked.connect(self.reset_perbandingan)

        panel_kanan.addWidget(btn_upload, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_download, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_save_compare, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_show_compare, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_reset_compare, alignment=Qt.AlignHCenter)

        baris_bawah.addLayout(panel_slider, stretch=1)
        baris_bawah.addLayout(panel_hasil, stretch=2)
        baris_bawah.addLayout(panel_kanan, stretch=0)

        konten_kanan.addLayout(baris_bawah)
        layout_utama.addLayout(konten_kanan)

    def style_button(self, bg, hover, disabled=None):
        disabled_css = ""
        if disabled:
            disabled_css = f"QPushButton:disabled {{ background-color: {disabled}; color: white; }}"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                font-weight: 800;
                border-radius: 21px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            {disabled_css}
        """

    def refresh_menu_style(self):
        for menu, btn in self.menu_buttons.items():
            if menu == self.mode:
                btn.setStyleSheet(
                    "QPushButton { background-color: #3b6af3; color: white; font-weight: 800; border-radius: 13px; padding: 12px; text-align: left; padding-left: 20px; border: none; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { background-color: transparent; color: #566573; font-weight: 800; border-radius: 13px; padding: 12px; text-align: left; padding-left: 20px; border: none; }"
                    "QPushButton:hover { background-color: #d1dced; }"
                )

    def ubah_mode(self, mode_baru):
        self.mode = mode_baru
        self.refresh_menu_style()
        if self.img_bgr is not None:
            self.proses_gambar()

    def buat_panel_gambar(self, title, size):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        layout.setAlignment(Qt.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFixedHeight(34)
        lbl_title.setStyleSheet("background-color: #3b6af3; color: white; font-weight: 800; border-radius: 17px;")

        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setFixedSize(size, size)
        lbl_img.setStyleSheet(
            "background-color: white; border: 2px solid #d5dde8; border-radius: 16px; color: #7f8c8d; font-weight: 700;"
        )

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_img)
        return panel, lbl_img

    def buat_slider_ui(self, nama, min_val, max_val, default_val, hint):
        layout = QVBoxLayout()
        layout.setSpacing(4)
        lbl = QLabel(f"{nama}: {default_val}  |  {hint}")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #34495e; font-weight: 800; font-size: 12px; border: none;")

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default_val)
        slider.setStyleSheet(
            "QSlider::groove:horizontal { border: none; height: 6px; background: #ccd6e2; border-radius: 3px; }"
            "QSlider::handle:horizontal { background: #3b6af3; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }"
        )
        slider.sliderReleased.connect(self.proses_gambar)
        slider.valueChanged.connect(lambda val, l=lbl, n=nama, h=hint: l.setText(f"{n}: {val}  |  {h}"))

        layout.addWidget(lbl)
        layout.addWidget(slider)
        return layout, slider

    def upload_gambar(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Buka Citra MRI", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.img_bgr = cv2.imread(file_name)
            if self.img_bgr is None:
                QMessageBox.warning(self, "Error", "Gagal memuat gambar!")
                return
            self.btn_download.setEnabled(True)
            self.btn_save_compare.setEnabled(True)
            self.proses_gambar()

    def download_gambar(self):
        if self.final_result_img is None:
            QMessageBox.information(self, "Info", "Belum ada hasil yang bisa disimpan.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Simpan Hasil Deteksi", "hasil_mri_tumor_tracker.jpg", "JPEG (*.jpg);;PNG (*.png)")
        if path:
            cv2.imwrite(path, self.final_result_img)
            QMessageBox.information(self, "Sukses", f"Gambar hasil berhasil disimpan:\n{path}")

    def simpan_hasil_uji(self):
        if not self.last_result_data:
            QMessageBox.information(self, "Info", "Belum ada hasil uji yang bisa disimpan.")
            return
        if len(self.comparison_results) >= 3:
            QMessageBox.information(self, "Info", "Daftar perbandingan sudah berisi 3 hasil. Klik Reset Perbandingan jika ingin mengulang.")
            return

        saved = {}
        for key, value in self.last_result_data.items():
            if isinstance(value, np.ndarray):
                saved[key] = value.copy()
            else:
                saved[key] = value
        self.comparison_results.append(saved)
        self.btn_show_compare.setEnabled(len(self.comparison_results) >= 2)
        self.btn_reset_compare.setEnabled(True)

        QMessageBox.information(
            self, "Hasil Disimpan",
            f"Hasil uji {self.last_result_data['mode']} berhasil disimpan.\n"
            f"Total data perbandingan: {len(self.comparison_results)}"
        )

    def reset_perbandingan(self):
        self.comparison_results.clear()
        self.btn_show_compare.setEnabled(False)
        self.btn_reset_compare.setEnabled(False)
        QMessageBox.information(self, "Reset", "Data perbandingan sudah dikosongkan.")

    def tampilkan_perbandingan(self):
        if len(self.comparison_results) < 2:
            QMessageBox.information(self, "Info", "Simpan minimal 2 hasil uji terlebih dahulu.")
            return
        # Fokus tampilkan 2 hasil pertama/terbaru untuk presentasi.
        results = self.comparison_results[:2]
        dialog = ComparisonDialog(results, self)
        dialog.exec_()

    def cv2_ke_qpixmap(self, cv_img, target_label):
        if cv_img is None:
            return QPixmap()
        safe_img = np.ascontiguousarray(cv_img)
        if len(safe_img.shape) == 2:
            h, w = safe_img.shape
            q_img = QImage(safe_img.data, w, h, w, QImage.Format_Grayscale8)
        else:
            h, w, ch = safe_img.shape
            q_img = QImage(safe_img.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img).scaled(target_label.width(), target_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def show_image(self, label, img):
        label.clear()
        label.setPixmap(self.cv2_ke_qpixmap(img, label))

    def clear_label_text(self, label, text):
        label.clear()
        label.setText(text)
        label.setAlignment(Qt.AlignCenter)

    @staticmethod
    def crop_margin_non_white(img_rgb, img_gray):
        not_white = img_gray < 254
        rows = np.any(not_white, axis=1)
        cols = np.any(not_white, axis=0)
        if rows.any() and cols.any():
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            return (img_rgb[rmin:rmax + 1, cmin:cmax + 1], img_gray[rmin:rmax + 1, cmin:cmax + 1].copy())
        return img_rgb, img_gray.copy()

    @staticmethod
    def draw_dashed_circle(img, center, radius, color, thickness=2, dash_angle=12, gap_angle=8):
        for start in range(0, 360, dash_angle + gap_angle):
            end = min(start + dash_angle, 360)
            cv2.ellipse(img, center, (radius, radius), 0, start, end, color, thickness, cv2.LINE_AA)

    @staticmethod
    def draw_polyline(img, points, color, thickness=2):
        if points is None or len(points) < 3:
            return
        pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(img, [pts], True, color, thickness, cv2.LINE_AA)

    def get_location_label(self, cx, cy, skull_bbox):
        x, y, w, h = skull_bbox
        mid_x = x + w / 2
        mid_y = y + h / 2
        horizontal = "kiri" if cx < mid_x else "kanan"
        vertical = "atas" if cy < mid_y else "bawah"
        return f"{vertical}-{horizontal}"

    def refine_active_contour(self, gray_img, cnt, cx, cy, r):
        perimeter = cv2.arcLength(cnt, True)
        if perimeter <= 0:
            return cnt.reshape(-1, 2)
        epsilon = 0.006 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        if approx is None or len(approx) < 5:
            hull = cv2.convexHull(cnt)
            return hull.reshape(-1, 2)
        return approx.reshape(-1, 2)

    def make_zoom(self, img_rgb, cx, cy, r, padding=70):
        h, w = img_rgb.shape[:2]
        rad = max(r + padding, 90)
        x1 = max(cx - rad, 0)
        y1 = max(cy - rad, 0)
        x2 = min(cx + rad, w)
        y2 = min(cy + rad, h)
        zoom = img_rgb[y1:y2, x1:x2].copy()
        if zoom.size == 0:
            return img_rgb.copy(), (0, 0)
        return zoom, (x1, y1)

    def make_report_image(self, full_rgb, zoom_rgb):
        target_h = 720

        def resize_to_height(img, height):
            h, w = img.shape[:2]
            scale = height / h
            return cv2.resize(img, (int(w * scale), height), interpolation=cv2.INTER_AREA)

        full = resize_to_height(full_rgb, target_h)
        zoom = resize_to_height(zoom_rgb, target_h)
        gap = np.ones((target_h, 36, 3), dtype=np.uint8) * 255
        report_rgb = np.hstack([full, gap, zoom])

        cv2.putText(report_rgb, "Deteksi Tumor - Full View", (20, 32), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)
        x_zoom_title = full.shape[1] + gap.shape[1] + 20
        cv2.putText(report_rgb, "Zoom Area Tumor", (x_zoom_title, 32), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 0), 2, cv2.LINE_AA)
        return cv2.cvtColor(report_rgb, cv2.COLOR_RGB2BGR)

    def proses_gambar(self):
        if self.img_bgr is None:
            return

        val_thresh = self.lbl_val_th.value()
        val_circ = self.lbl_val_circ.value() / 100.0
        val_area = self.lbl_val_area.value()

        img_rgb = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB)
        img_gray = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2GRAY)
        self.show_image(self.lbl_asli, img_rgb)

        mri_rgb, mri_gray = self.crop_margin_non_white(img_rgb, img_gray)
        mri_gray[mri_gray > 253] = 0
        h, w = mri_gray.shape

        _, head_mask = cv2.threshold(mri_gray, 15, 255, cv2.THRESH_BINARY)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        closed_head = cv2.morphologyEx(head_mask, cv2.MORPH_CLOSE, kernel_close)
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned_head = cv2.morphologyEx(closed_head, cv2.MORPH_OPEN, kernel_clean)
        kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
        brain_mask = cv2.erode(cleaned_head, kernel_erode, iterations=1)
        brain_only = cv2.bitwise_and(mri_gray, brain_mask)
        self.show_image(self.lbl_masking, brain_only)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        brain_enhanced = clahe.apply(brain_only)
        blurred_brain = cv2.bilateralFilter(brain_enhanced, 7, 55, 55)

        brain_pixels = blurred_brain[brain_mask > 0]
        if len(brain_pixels) > 0:
            if val_thresh == 0:
                otsu_val, _ = cv2.threshold(brain_pixels, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                _, thresh = cv2.threshold(blurred_brain, otsu_val, 255, cv2.THRESH_BINARY)
            else:
                _, thresh = cv2.threshold(blurred_brain, val_thresh, 255, cv2.THRESH_BINARY)
        else:
            thresh = np.zeros_like(blurred_brain)

        thresh = cv2.bitwise_and(thresh, brain_mask)
        kernel_morph = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        thresh_closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_morph)
        thresh_closed = cv2.morphologyEx(thresh_closed, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        self.show_image(self.lbl_thresh, thresh_closed)

        contours, _ = cv2.findContours(thresh_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        valid = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < val_area or area > (h * w * 0.25):
                continue
            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            circ = 4 * np.pi * area / (peri ** 2)
            if circ < val_circ:
                continue
            (cx, cy), r = cv2.minEnclosingCircle(cnt)
            cx, cy, r = int(cx), int(cy), int(r)
            if cx < 10 or cx > w - 10 or cy < 10 or cy > h - 10:
                continue
            valid.append({"cnt": cnt, "area": area, "circ": circ, "cx": cx, "cy": cy, "r": r})

        valid = sorted(valid, key=lambda item: item["area"], reverse=True)
        final_img = mri_rgb.copy()

        contours_kepala, _ = cv2.findContours(cleaned_head, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_kepala:
            kontur_terbesar = max(contours_kepala, key=cv2.contourArea)
            x_kep, y_kep, w_kep, h_kep = cv2.boundingRect(kontur_terbesar)
        else:
            x_kep, y_kep, w_kep, h_kep = 0, 0, w, h
        skull_bbox = (x_kep, y_kep, w_kep, h_kep)
        cv2.rectangle(final_img, (x_kep, y_kep), (x_kep + w_kep, y_kep + h_kep), (160, 160, 160), 1)
        cv2.putText(final_img, "Skull Bounds", (x_kep + 5, max(y_kep + 16, 16)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (190, 190, 190), 1, cv2.LINE_AA)

        if not valid or self.mode == "No Tumor":
            img_normal = final_img.copy()
            cv2.putText(img_normal, "STATUS: NORMAL / NO TUMOR", (18, 34), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 0), 2, cv2.LINE_AA)
            self.show_image(self.lbl_final, img_normal)
            self.clear_label_text(self.lbl_zoom, "Area Bersih\nTidak ada kandidat tumor")
            self.lbl_info_klinis.setText(
                "📊 Data Klinis:\n\n✅ Status: NORMAL / NO TUMOR\nTidak ada kandidat area tumor yang melewati filter.\n\n"
                "Catatan:\nEvaluasi masih berbasis visual dan rule-based OpenCV."
            )
            self.last_result_data = {
                "mode": self.mode,
                "status": "NORMAL / NO TUMOR",
                "area_px": 0,
                "area_cm2": "0.00",
                "diameter_cm": "0.00",
                "center": "-",
                "lokasi": "tidak ada",
                "original_preview": mri_rgb.copy(),
                "result_preview": img_normal.copy(),
            }
            self.final_result_img = cv2.cvtColor(img_normal, cv2.COLOR_RGB2BGR)
            return

        main = valid[0]
        cnt = main["cnt"]
        area_px = main["area"]
        cx, cy, r = main["cx"], main["cy"], main["r"]
        active_pts = self.refine_active_contour(blurred_brain, cnt, cx, cy, r)

        init_radius = max(r + 22, int(r * 1.28))
        self.draw_dashed_circle(final_img, (cx, cy), init_radius, (255, 0, 0), 2)
        self.draw_polyline(final_img, active_pts, (0, 0, 255), 3)
        cv2.circle(final_img, (cx, cy), 4, (255, 255, 0), -1)
        cv2.putText(final_img, "Tumor 1", (cx + 8, cy - 8), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 0), 1, cv2.LINE_AA)

        zoom_img, (zx, zy) = self.make_zoom(mri_rgb, cx, cy, r, padding=90)
        zoom_overlay = zoom_img.copy()
        zoom_cx, zoom_cy = cx - zx, cy - zy
        active_zoom = active_pts.copy()
        active_zoom[:, 0] -= zx
        active_zoom[:, 1] -= zy
        self.draw_dashed_circle(zoom_overlay, (zoom_cx, zoom_cy), init_radius, (255, 0, 0), 2)
        self.draw_polyline(zoom_overlay, active_zoom, (0, 0, 255), 3)
        cv2.circle(zoom_overlay, (zoom_cx, zoom_cy), 4, (255, 255, 0), -1)

        self.show_image(self.lbl_final, final_img)
        self.show_image(self.lbl_zoom, zoom_overlay)

        area_cm2 = area_px * (self.PIXEL_TO_CM ** 2)
        diameter_px = 2 * r
        diameter_cm = diameter_px * self.PIXEL_TO_CM
        dist_left_px = max(cx - x_kep, 0)
        dist_top_px = max(cy - y_kep, 0)
        lokasi = self.get_location_label(cx, cy, skull_bbox)

        self.last_result_data = {
            "mode": self.mode,
            "status": "TERDETEKSI KANDIDAT TUMOR",
            "area_px": int(area_px),
            "area_cm2": f"{area_cm2:.2f}",
            "diameter_cm": f"{diameter_cm:.2f}",
            "center": f"X={cx}, Y={cy}",
            "lokasi": lokasi,
            "original_preview": mri_rgb.copy(),
            "result_preview": final_img.copy(),
        }

        active_method = "Contour Refinement (OpenCV)" if not SKIMAGE_AVAILABLE else "Active Contour (skimage)"
        info_text = (
            "📊 Data Klinis Tumor:\n\n"
            f"Mode analisis: {self.mode}\n"
            f"Metode contour: {active_method}\n\n"
            "🔹 Tumor 1\n"
            f"- Luas area: {int(area_px)} px\n"
            f"- Estimasi luas: {area_cm2:.2f} cm²\n"
            f"- Diameter estimasi: {diameter_px} px / {diameter_cm:.2f} cm\n"
            f"- Titik pusat: X={cx}px, Y={cy}px\n"
            f"- Lokasi relatif: {lokasi}\n"
            f"- Jarak dari kiri: {dist_left_px}px / {dist_left_px * self.PIXEL_TO_CM:.2f} cm\n"
            f"- Jarak dari atas: {dist_top_px}px / {dist_top_px * self.PIXEL_TO_CM:.2f} cm\n\n"
            "Keterangan:\n"
            "Garis merah putus-putus = init circle.\n"
            "Garis biru = contour hasil refinement."
        )
        self.lbl_info_klinis.setText(info_text)

        overlay_text = [
            "Data Klinis Tumor",
            f"Tumor 1 | Area: {int(area_px)} px ({area_cm2:.2f} cm2)",
            f"Lokasi: {lokasi} | Pusat: X={cx}, Y={cy}",
            f"Diameter: {diameter_px} px ({diameter_cm:.2f} cm)"
        ]
        y_text = 28
        annotated_final = final_img.copy()
        for text in overlay_text:
            cv2.putText(annotated_final, text, (14, y_text), cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(annotated_final, text, (14, y_text), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            y_text += 24

        self.final_result_img = self.make_report_image(annotated_final, zoom_overlay)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Poppins", 10))
    window = DeteksiTumorApp()
    window.show()
    sys.exit(app.exec_())
