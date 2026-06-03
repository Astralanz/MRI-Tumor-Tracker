import sys
import cv2
import math
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QSlider, QPushButton, QFileDialog, QMessageBox, QFrame, QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

# =========================================================
# KELAS DIALOG PERBANDINGAN
# =========================================================
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
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1f2937; border:none;")
        main_layout.addWidget(title)

        subtitle = QLabel("Popup ini menampilkan 2 gambar hasil uji yang sudah disimpan, lalu dibandingkan bersama data area, titik pusat, dan lokasi tumor.")
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

        table_title = QLabel("Tabel Perbandingan (Berdasarkan Tumor Terbesar/Pertama)")
        table_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #203040; border:none;")
        table_layout.addWidget(table_title)

        table = QTableWidget(len(self.results), 8)
        table.setHorizontalHeaderLabels([
            "No", "Kelas", "Status", "Luas px", "Luas cm²",
            "Diameter cm", "Titik Pusat", "Lokasi Relatif"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            "QTableWidget { background-color:white; font-size:12px; gridline-color:#dfe7f1; }"
            "QHeaderView::section { background-color:#3b6af3; color:white; font-weight:bold; padding:7px; border:none; }"
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
        conclusion.setStyleSheet("background-color: white; border: 2px solid #d5dde8; border-radius: 16px; padding: 12px; font-size: 12px; color:#2c3e50; font-weight: bold;")
        main_layout.addWidget(conclusion)

        close_btn = QPushButton("Tutup")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(140, 40)
        close_btn.setStyleSheet("QPushButton { background-color:#3b6af3; color:white; font-weight:bold; border:none; border-radius:20px; } QPushButton:hover { background-color:#2a52cf; }")
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
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #203040; border:none;")
        layout.addWidget(title)

        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setFixedSize(500, 260)
        lbl_img.setStyleSheet("background-color:#f8fafc; border: 2px solid #dbe4f0; border-radius: 14px; color:#64748b;")

        preview = item.get("result_preview")
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
        info.setStyleSheet("font-size: 12px; color:#334155; font-weight:bold; border:none;")
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
            detail = "Hasil uji kedua menunjukkan tidak ada tumor terdeteksi, sehingga dapat dipakai sebagai contoh perbaikan kondisi pasien setelah operasi."
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


# =========================================================
# KELAS UTAMA (GRID PIPELINE 6 GAMBAR)
# =========================================================
class DeteksiTumorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Lengkap: Deteksi Tumor MRI")
        self.setGeometry(30, 30, 1380, 850) 
        self.setStyleSheet("background-color: #f0f4f8;") 
        
        self.img_bgr = None
        self.mode = "Meningioma" 
        
        # Untuk menyimpan gambar tiap step biar bisa di-download
        self.step_images = {
            "asli": None, "grayscale": None, "masking": None,
            "segmentasi": None, "contour": None, "final": None
        }
        
        # Variabel untuk menampung data perbandingan
        self.last_result_data = None
        self.comparison_results = []
        
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout_utama = QHBoxLayout(main_widget)
        layout_utama.setContentsMargins(20, 20, 20, 20)
        layout_utama.setSpacing(20)

        # ---------------------------------------------------------
        # KONTEN UTAMA (KIRI: GRID 6 GAMBAR)
        # ---------------------------------------------------------
        konten_kiri = QVBoxLayout()
        
        grid_pipeline = QGridLayout()
        grid_pipeline.setSpacing(15)
        
        ukuran_gambar = 260
        
        self.panel_asli, self.lbl_asli = self.buat_panel_gambar("1. Asli (RGB)", "asli", ukuran_gambar)
        self.panel_gray, self.lbl_gray = self.buat_panel_gambar("2. Grayscale", "grayscale", ukuran_gambar)
        self.panel_mask, self.lbl_mask = self.buat_panel_gambar("3. Masking & Enhancement", "masking", ukuran_gambar)
        self.panel_seg, self.lbl_seg = self.buat_panel_gambar("4. Segmentasi Biner", "segmentasi", ukuran_gambar)
        self.panel_cnt, self.lbl_cnt = self.buat_panel_gambar("5. Ekstraksi Kontur", "contour", ukuran_gambar)
        self.panel_fin, self.lbl_fin = self.buat_panel_gambar("6. Hasil Final", "final", ukuran_gambar)
        
        grid_pipeline.addWidget(self.panel_asli, 0, 0)
        grid_pipeline.addWidget(self.panel_gray, 0, 1)
        grid_pipeline.addWidget(self.panel_mask, 0, 2)
        grid_pipeline.addWidget(self.panel_seg, 1, 0)
        grid_pipeline.addWidget(self.panel_cnt, 1, 1)
        grid_pipeline.addWidget(self.panel_fin, 1, 2)
        
        konten_kiri.addLayout(grid_pipeline)
        layout_utama.addLayout(konten_kiri, stretch=3)

        # ---------------------------------------------------------
        # PANEL KANAN (SLIDER & INFO)
        # ---------------------------------------------------------
        panel_kanan = QFrame()
        panel_kanan.setFixedWidth(320)
        panel_kanan.setStyleSheet("QFrame { background-color: #e4ebf3; border-radius: 20px; }")
        layout_kanan = QVBoxLayout(panel_kanan)
        layout_kanan.setContentsMargins(20, 30, 20, 30)
        layout_kanan.setSpacing(20)

        btn_upload = QPushButton("Upload MRI")
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.setFixedHeight(45)
        btn_upload.setStyleSheet("QPushButton { background-color: #3b6af3; color: white; font-weight: bold; border-radius: 15px; border: none; } QPushButton:hover { background-color: #2a52cf; }")
        btn_upload.clicked.connect(self.upload_gambar)
        layout_kanan.addWidget(btn_upload)

        layout_kanan.addWidget(QLabel("<b>⚙️ Parameter Deteksi:</b>"))

        self.layout_thresh, self.slider_thresh = self.buat_slider_ui("Batas Kecerahan (0=Otsu): ", 0, 255, 0)
        self.layout_circ, self.slider_circ = self.buat_slider_ui("Toleransi Bulat (1-90): ", 1, 90, 20)
        self.layout_area, self.slider_area = self.buat_slider_ui("Minimum Luas (Area): ", 50, 5000, 150)
        
        layout_kanan.addLayout(self.layout_thresh)
        layout_kanan.addLayout(self.layout_circ)
        layout_kanan.addLayout(self.layout_area)

        layout_kanan.addStretch()

        self.lbl_info_klinis = QLabel("Data Klinis:\nMenunggu gambar...")
        self.lbl_info_klinis.setStyleSheet("background-color: white; border: 2px solid #ccc; border-radius: 15px; padding: 15px; font-size: 13px; color: #333; font-weight: bold;")
        self.lbl_info_klinis.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl_info_klinis.setMinimumHeight(180)
        layout_kanan.addWidget(self.lbl_info_klinis)
        
        # Tombol Perbandingan
        self.btn_save_compare = QPushButton("Simpan Uji")
        self.btn_save_compare.setCursor(Qt.PointingHandCursor)
        self.btn_save_compare.setFixedHeight(35)
        self.btn_save_compare.setEnabled(False)
        self.btn_save_compare.setStyleSheet("QPushButton { background-color: #16a085; color: white; font-weight: bold; border-radius: 15px; border: none; } QPushButton:hover { background-color: #138d75; } QPushButton:disabled { background-color: #a9dfbf; }")
        self.btn_save_compare.clicked.connect(self.simpan_hasil_uji)
        layout_kanan.addWidget(self.btn_save_compare)

        self.btn_show_compare = QPushButton("Lihat Perbandingan")
        self.btn_show_compare.setCursor(Qt.PointingHandCursor)
        self.btn_show_compare.setFixedHeight(35)
        self.btn_show_compare.setEnabled(False)
        self.btn_show_compare.setStyleSheet("QPushButton { background-color: #8e44ad; color: white; font-weight: bold; border-radius: 15px; border: none; } QPushButton:hover { background-color: #732d91; } QPushButton:disabled { background-color: #d2b4de; }")
        self.btn_show_compare.clicked.connect(self.tampilkan_perbandingan)
        layout_kanan.addWidget(self.btn_show_compare)

        self.btn_reset_compare = QPushButton("Reset Perbandingan")
        self.btn_reset_compare.setCursor(Qt.PointingHandCursor)
        self.btn_reset_compare.setFixedHeight(35)
        self.btn_reset_compare.setEnabled(False)
        self.btn_reset_compare.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; font-weight: bold; border-radius: 15px; border: none; } QPushButton:hover { background-color: #7f8c8d; } QPushButton:disabled { background-color: #d5dbdb; }")
        self.btn_reset_compare.clicked.connect(self.reset_perbandingan)
        layout_kanan.addWidget(self.btn_reset_compare)

        layout_utama.addWidget(panel_kanan, stretch=1)

    # ---------------------------------------------------------
    # FUNGSI UI BANTUAN
    # ---------------------------------------------------------
    def buat_panel_gambar(self, title, step_key, size):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFixedHeight(30)
        lbl_title.setStyleSheet("background-color: #3b6af3; color: white; font-weight: bold; border-radius: 15px; font-size: 12px;")
        
        lbl_img = QLabel("Belum ada gambar")
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setFixedSize(size, size)
        lbl_img.setStyleSheet("background-color: white; border: 2px solid #ccc; border-radius: 15px; color: #999;")
        
        btn_dl = QPushButton(f"Donlod {title.split('.')[1][:8]}")
        btn_dl.setCursor(Qt.PointingHandCursor)
        btn_dl.setFixedHeight(28)
        btn_dl.setStyleSheet("QPushButton { background-color: #e67e22; color: white; font-weight: bold; border-radius: 10px; font-size: 11px; } QPushButton:hover { background-color: #d35400; }")
        btn_dl.clicked.connect(lambda _, k=step_key, t=title: self.download_step_gambar(k, t))

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_img)
        layout.addWidget(btn_dl, alignment=Qt.AlignHCenter)
        return panel, lbl_img

    def buat_slider_ui(self, nama, min_val, max_val, default_val):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        lbl = QLabel(f"{nama}{default_val}")
        lbl.setStyleSheet("color: #444; font-size: 12px; font-weight: bold;")
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("QSlider::groove:horizontal { border: none; height: 6px; background: #ccc; border-radius: 3px; } QSlider::handle:horizontal { background: #3b6af3; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }")
        
        slider.sliderReleased.connect(self.proses_gambar)
        slider.valueChanged.connect(lambda val, l=lbl, n=nama: l.setText(f"{n}{val}"))
        
        layout.addWidget(lbl)
        layout.addWidget(slider)
        return layout, slider

    def download_step_gambar(self, step_key, title):
        img_to_save = self.step_images.get(step_key)
        if img_to_save is None:
            QMessageBox.warning(self, "Kosong", f"Gambar '{title}' belum ada!")
            return
            
        file_suggest = f"output_{step_key}.jpg"
        path, _ = QFileDialog.getSaveFileName(self, f"Simpan {title}", file_suggest, "JPEG (*.jpg);;PNG (*.png)")
        if path:
            cv2.imwrite(path, img_to_save)
            QMessageBox.information(self, "Sukses", f"Tersimpan di:\n{path}")

    # ---------------------------------------------------------
    # METHOD PERBANDINGAN
    # ---------------------------------------------------------
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

        QMessageBox.information(self, "Hasil Disimpan", f"Hasil uji berhasil disimpan.\nTotal data perbandingan: {len(self.comparison_results)}")

    def reset_perbandingan(self):
        self.comparison_results.clear()
        self.btn_show_compare.setEnabled(False)
        self.btn_reset_compare.setEnabled(False)
        QMessageBox.information(self, "Reset", "Data perbandingan sudah dikosongkan.")

    def tampilkan_perbandingan(self):
        if len(self.comparison_results) < 2:
            return
        results = self.comparison_results[:2] 
        dialog = ComparisonDialog(results, self)
        dialog.exec_()


    # ---------------------------------------------------------
    # PIPELINE OPENCV UTAMA
    # ---------------------------------------------------------
    def upload_gambar(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Buka Citra MRI", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            self.img_bgr = cv2.imread(file_name)
            if self.img_bgr is not None:
                self.btn_save_compare.setEnabled(True)
                self.proses_gambar() 
            else:
                QMessageBox.warning(self, "Error", "Gagal memuat gambar!")

    def proses_gambar(self):
        if self.img_bgr is None:
            return

        val_thresh = self.slider_thresh.value()
        val_circ   = self.slider_circ.value() / 100.0
        val_area   = self.slider_area.value()

        # 1 & 2. ASLI & GRAYSCALE
        img_rgb = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB)
        img_gray = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2GRAY)
        
        self.step_images["asli"] = self.img_bgr.copy()
        self.lbl_asli.setPixmap(self.cv2_ke_qpixmap(img_rgb, self.lbl_asli))
        
        gray_bgr = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        self.step_images["grayscale"] = gray_bgr
        self.lbl_gray.setPixmap(self.cv2_ke_qpixmap(gray_bgr, self.lbl_gray))

        # Prep-Crop Otomatis
        not_white = img_gray < 254
        rows = np.any(not_white, axis=1)
        cols = np.any(not_white, axis=0)
        if rows.any() and cols.any():
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            mri_rgb = img_rgb[rmin:rmax, cmin:cmax]
            mri_gray = img_gray[rmin:rmax, cmin:cmax].copy()
            mri_gray[mri_gray > 253] = 0   
        else:
            mri_rgb = img_rgb.copy()
            mri_gray = img_gray.copy()
        h, w = mri_gray.shape

        # 3. MASKING & ENHANCEMENT
        _, head_mask = cv2.threshold(mri_gray, 15, 255, cv2.THRESH_BINARY)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))
        closed_head  = cv2.morphologyEx(head_mask, cv2.MORPH_CLOSE, kernel_close)
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        cleaned_head = cv2.morphologyEx(closed_head, cv2.MORPH_OPEN, kernel_clean)
        kernel_agg   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25,25))
        mask_pedoman = cv2.erode(cleaned_head, kernel_agg, iterations=1)
        
        brain_only = cv2.bitwise_and(mri_gray, mask_pedoman)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        brain_enhanced = clahe.apply(brain_only)
        blurred_brain  = cv2.bilateralFilter(brain_enhanced, 7, 50, 50)
        
        mask_bgr = cv2.cvtColor(blurred_brain, cv2.COLOR_GRAY2BGR)
        self.step_images["masking"] = mask_bgr
        self.lbl_mask.setPixmap(self.cv2_ke_qpixmap(mask_bgr, self.lbl_mask))

        # 4. SEGMENTASI BINER
        brain_pixels = blurred_brain[blurred_brain > 15]
        if len(brain_pixels) > 0:
            if val_thresh == 0:
                thresh_val, _ = cv2.threshold(brain_pixels, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                _, thresh = cv2.threshold(blurred_brain, thresh_val, 255, cv2.THRESH_BINARY)
            else:
                _, thresh = cv2.threshold(blurred_brain, val_thresh, 255, cv2.THRESH_BINARY)
        else:
            thresh = np.zeros_like(blurred_brain)

        kernel_morph = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
        thresh_closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_morph)
        thresh_closed = cv2.morphologyEx(thresh_closed, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3)))
        
        seg_bgr = cv2.cvtColor(thresh_closed, cv2.COLOR_GRAY2BGR)
        self.step_images["segmentasi"] = seg_bgr
        self.lbl_seg.setPixmap(self.cv2_ke_qpixmap(seg_bgr, self.lbl_seg))

        # 5. EKSTRAKSI KONTUR
        contours, _ = cv2.findContours(thresh_closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        valid = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < val_area or area > 50000:
                continue
            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            circ = 4 * math.pi * area / (peri ** 2)
            if circ < val_circ:
                continue
            (cx, cy), r = cv2.minEnclosingCircle(cnt)
            if cx < 10 or cx > w - 10 or cy < 10 or cy > h - 10:
                continue
            valid.append((cnt, area, int(cx), int(cy), int(r)))

        thresh_rgb = cv2.cvtColor(thresh_closed, cv2.COLOR_GRAY2RGB)
        final_img = mri_rgb.copy()

        # 6. HASIL FINAL
        if not valid:
            self.step_images["contour"] = seg_bgr.copy()
            self.lbl_cnt.setPixmap(self.cv2_ke_qpixmap(seg_bgr, self.lbl_cnt))
            
            img_normal = mri_rgb.copy()
            cv2.putText(img_normal, "STATUS: NORMAL", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            
            self.lbl_fin.setPixmap(self.cv2_ke_qpixmap(img_normal, self.lbl_fin))
            
            dl_img = cv2.cvtColor(img_normal, cv2.COLOR_RGB2BGR)
            cv2.putText(dl_img, "Data Klinis: STATUS NORMAL", (15, 35), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(dl_img, "Data Klinis: STATUS NORMAL", (15, 35), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
            self.step_images["final"] = dl_img
            self.lbl_info_klinis.setText("✅ STATUS: NORMAL\nTidak terdeteksi anomali.")
            
            self.last_result_data = {
                "mode": self.mode, "status": "NORMAL", "area_px": 0, "area_cm2": "0.00",
                "diameter_cm": "0.00", "center": "-", "lokasi": "-",
                "original_preview": mri_rgb.copy(), "result_preview": img_normal.copy()
            }
            return

        # Ambil kontur kepala untuk perhitungan lokasi relatif
        contours_kepala, _ = cv2.findContours(cleaned_head, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours_kepala:
            kontur_terbesar = max(contours_kepala, key=cv2.contourArea)
            x_kep, y_kep, w_kep, h_kep = cv2.boundingRect(kontur_terbesar)
        else:
            x_kep, y_kep = 0, 0 

        info_text = "📊 Data Klinis Tumor:\n"
        for idx, item in enumerate(valid, 1):
            cnt, area_asli, cx, cy, r = item
            
            # Gambar Kontur (Biru) & Lingkaran (Hijau)
            cv2.drawContours(thresh_rgb, [cnt], -1, (255, 0, 0), 2)
            cv2.circle(thresh_rgb, (cx, cy), r, (0, 255, 0), 2)
            
            # Gambar Garis Merah di Citra Asli
            cv2.drawContours(final_img, [cnt], -1, (0, 0, 255), 3) 
            cv2.putText(final_img, str(idx), (cx + r + 5, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2, cv2.LINE_AA)
            
            info_text += f"\n🔹 Tumor {idx}\n  - Luas: {int(area_asli)} px\n  - Posisi: X={cx}, Y={cy}\n"

        self.lbl_info_klinis.setText(info_text)

        cnt_bgr = cv2.cvtColor(thresh_rgb, cv2.COLOR_RGB2BGR)
        self.step_images["contour"] = cnt_bgr
        self.lbl_cnt.setPixmap(self.cv2_ke_qpixmap(thresh_rgb, self.lbl_cnt))
        
        self.lbl_fin.setPixmap(self.cv2_ke_qpixmap(final_img, self.lbl_fin))
        
        dl_img = cv2.cvtColor(final_img, cv2.COLOR_RGB2BGR)
        teks_bersih = info_text.split("\n")
        y_pos = 35 
        for baris in teks_bersih:
            if baris.strip():
                cv2.putText(dl_img, baris.rstrip(), (15, y_pos), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(dl_img, baris.rstrip(), (15, y_pos), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
                y_pos += 25 
        self.step_images["final"] = dl_img
        
        # Ekstraksi data tumor utama/terbesar untuk perbandingan
        cnt_f, area_f, cx_f, cy_f, r_f = valid[0]
        pixel_to_cm = 0.026
        self.last_result_data = {
            "mode": self.mode,
            "status": f"TERDETEKSI ({len(valid)} Tumor)",
            "area_px": int(area_f),
            "area_cm2": f"{area_f * (pixel_to_cm**2):.2f}",
            "diameter_cm": f"{2 * r_f * pixel_to_cm:.2f}",
            "center": f"X={cx_f}, Y={cy_f}",
            "lokasi": f"X:{cx_f - x_kep}px, Y:{cy_f - y_kep}px",
            "original_preview": mri_rgb.copy(),
            "result_preview": final_img.copy()
        }

    def cv2_ke_qpixmap(self, cv_img, target_label):
        if len(cv_img.shape) == 2:
            h, w = cv_img.shape
            qt_img = QImage(cv_img.data, w, h, w, QImage.Format_Grayscale8)
        else:
            h, w, ch = cv_img.shape
            qt_img = QImage(cv_img.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_img).scaled(target_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Poppins", 10))
    window = DeteksiTumorApp()
    window.show()
    sys.exit(app.exec_())