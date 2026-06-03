import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QPushButton, QFileDialog, 
                             QMessageBox, QFrame, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea)
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
            detail = "Hasil uji kedua menunjukkan tidak ada tumor terdeteksi, sehingga dapat dipakai sebagai contoh perbaikan kondisi pasien setelah follow-up. Ini cocok untuk skenario pasien sebelumnya masih terdeteksi tumor, kemudian setelah operasi hasilnya bersih."
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
# KELAS UTAMA (Patokan)
# =========================================================
class DeteksiTumorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MRI Tumor Tracker - Desktop UI")
        self.setGeometry(50, 50, 1300, 750) 
        self.setStyleSheet("background-color: #f0f4f8;") 
        
        self.img_bgr = None
        self.final_result_img = None
        
        self.mode = "Meningioma" 
        self.menu_buttons = {} 
        
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
        # SIDEBAR KIRI (MENU)
        # ---------------------------------------------------------
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame { background-color: #e4ebf3; border-radius: 20px; }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 30, 15, 30)
        sidebar_layout.setSpacing(15)

        lbl_judul = QLabel("🧠 MRI Tumor Otak\nTracker")
        lbl_judul.setAlignment(Qt.AlignCenter)
        lbl_judul.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; border: none;")
        sidebar_layout.addWidget(lbl_judul)
        sidebar_layout.addSpacing(20)

        # BAGIAN YANG DIUBAH: Menghapus "Glioma", "Notumor", dan "Pituitary"
        menus = ["Meningioma"]
        
        for menu in menus:
            btn = QPushButton(menu)
            btn.setCursor(Qt.PointingHandCursor)
            
            if menu == self.mode:
                btn.setStyleSheet("QPushButton { background-color: #3b6af3; color: white; font-weight: bold; border-radius: 12px; padding: 12px; text-align: left; padding-left: 20px; border: none; }")
            else:
                btn.setStyleSheet("QPushButton { background-color: transparent; color: #555; font-weight: bold; border-radius: 12px; padding: 12px; text-align: left; padding-left: 20px; border: none; } QPushButton:hover { background-color: #d1dced; }")
            
            btn.clicked.connect(lambda checked, m=menu: self.ubah_mode(m))
            self.menu_buttons[menu] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        layout_utama.addWidget(sidebar)

        # ---------------------------------------------------------
        # KONTEN UTAMA (KANAN)
        # ---------------------------------------------------------
        konten_kanan = QVBoxLayout()
        konten_kanan.addStretch(1) 

        baris_atas = QHBoxLayout()
        baris_atas.setSpacing(20)
        
        self.panel_asli, self.lbl_asli = self.buat_panel_gambar("Gambar Asli", 260)
        self.panel_clahe, self.lbl_clahe = self.buat_panel_gambar("Masking", 260)
        self.panel_kandidat, self.lbl_kandidat = self.buat_panel_gambar("Threshold Execution", 260)
        
        baris_atas.addWidget(self.panel_asli)
        baris_atas.addWidget(self.panel_clahe)
        baris_atas.addWidget(self.panel_kandidat)
        konten_kanan.addLayout(baris_atas)
        konten_kanan.addSpacing(30) 

        # AREA BAWAH: Dibagi 3 bagian
        baris_bawah = QHBoxLayout()
        baris_bawah.setSpacing(20)

        # 1. BAGIAN KIRI: SLIDER
        panel_slider = QVBoxLayout()
        panel_slider.setSpacing(15)
        panel_slider.setAlignment(Qt.AlignVCenter)
        
        self.slider_thresh, self.lbl_val_th = self.buat_slider_ui("Batas Kecerahan : ", 0, 300, 0)
        self.slider_circ, self.lbl_val_circ = self.buat_slider_ui("Toleransi Lingkaran : ", 1, 90, 20)
        self.slider_area, self.lbl_val_area = self.buat_slider_ui("Size Minimum Tumor : ", 50, 5000, 150)
        
        panel_slider.addLayout(self.slider_thresh)
        panel_slider.addLayout(self.slider_circ)
        panel_slider.addLayout(self.slider_area)
        
        # 2. BAGIAN TENGAH: GAMBAR FINAL & PEMBANDING
        panel_tengah = QHBoxLayout()
        panel_tengah.setSpacing(15)
        
        self.panel_final, self.lbl_final = self.buat_panel_gambar("FINAL", 260)
        self.panel_pembanding, self.lbl_pembanding = self.buat_panel_gambar("Pembanding", 260)
        
        panel_tengah.addWidget(self.panel_final)
        panel_tengah.addWidget(self.panel_pembanding)
        
        # 3. BAGIAN KANAN: DATA KLINIS & TOMBOL
        panel_kanan = QVBoxLayout()
        panel_kanan.setAlignment(Qt.AlignVCenter)
        panel_kanan.setSpacing(10)

        # Teks Box Info Klinis
        self.lbl_info_klinis = QLabel("Data Klinis:\nMenunggu gambar...")
        self.lbl_info_klinis.setStyleSheet("background-color: white; border: 2px solid #ccc; border-radius: 15px; padding: 15px; font-size: 13px; color: #333; font-weight: bold;")
        self.lbl_info_klinis.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl_info_klinis.setMinimumHeight(140)
        
        # Tombol Upload Utama
        btn_upload = QPushButton("Upload MRI")
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.setFixedSize(160, 35)
        btn_upload.setStyleSheet("QPushButton { background-color: #3b6af3; color: white; font-weight: bold; border-radius: 17px; border: none; } QPushButton:hover { background-color: #2a52cf; }")
        btn_upload.clicked.connect(self.upload_gambar)

        # Tombol Download
        self.btn_download = QPushButton("Download Hasil")
        self.btn_download.setCursor(Qt.PointingHandCursor)
        self.btn_download.setFixedSize(160, 35)
        self.btn_download.setEnabled(False)
        self.btn_download.setStyleSheet("QPushButton { background-color: #f33b3b; color: white; font-weight: bold; border-radius: 17px; border: none; } QPushButton:hover { background-color: #cf2a2a; } QPushButton:disabled { background-color: #f79999; }")
        self.btn_download.clicked.connect(self.download_gambar)

        # Tombol Upload Pembanding
        btn_upload_pembanding = QPushButton("Upload Pembanding")
        btn_upload_pembanding.setCursor(Qt.PointingHandCursor)
        btn_upload_pembanding.setFixedSize(160, 35)
        btn_upload_pembanding.setStyleSheet("QPushButton { background-color: #7f8c8d; color: white; font-weight: bold; border-radius: 17px; border: none; } QPushButton:hover { background-color: #636e72; }")
        btn_upload_pembanding.clicked.connect(self.upload_pembanding)

        # --- TOMBOL PERBANDINGAN POPUP ---
        self.btn_save_compare = QPushButton("Simpan Uji")
        self.btn_save_compare.setCursor(Qt.PointingHandCursor)
        self.btn_save_compare.setFixedSize(160, 35)
        self.btn_save_compare.setEnabled(False)
        self.btn_save_compare.setStyleSheet("QPushButton { background-color: #16a085; color: white; font-weight: bold; border-radius: 17px; border: none; } QPushButton:hover { background-color: #138d75; } QPushButton:disabled { background-color: #a9dfbf; }")
        self.btn_save_compare.clicked.connect(self.simpan_hasil_uji)

        self.btn_show_compare = QPushButton("Lihat Perbandingan")
        self.btn_show_compare.setCursor(Qt.PointingHandCursor)
        self.btn_show_compare.setFixedSize(160, 35)
        self.btn_show_compare.setEnabled(False)
        self.btn_show_compare.setStyleSheet("QPushButton { background-color: #8e44ad; color: white; font-weight: bold; border-radius: 17px; border: none; } QPushButton:hover { background-color: #732d91; } QPushButton:disabled { background-color: #d2b4de; }")
        self.btn_show_compare.clicked.connect(self.tampilkan_perbandingan)

        self.btn_reset_compare = QPushButton("Reset Perbandingan")
        self.btn_reset_compare.setCursor(Qt.PointingHandCursor)
        self.btn_reset_compare.setFixedSize(160, 35)
        self.btn_reset_compare.setEnabled(False)
        self.btn_reset_compare.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; font-weight: bold; border-radius: 17px; border: none; } QPushButton:hover { background-color: #7f8c8d; } QPushButton:disabled { background-color: #d5dbdb; }")
        self.btn_reset_compare.clicked.connect(self.reset_perbandingan)

        # Tata Letak Panel Kanan
        panel_kanan.addWidget(self.lbl_info_klinis)
        panel_kanan.addWidget(btn_upload, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_download, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(btn_upload_pembanding, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_save_compare, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_show_compare, alignment=Qt.AlignHCenter)
        panel_kanan.addWidget(self.btn_reset_compare, alignment=Qt.AlignHCenter)

        # Gabungkan semua ke baris bawah
        baris_bawah.addLayout(panel_slider, stretch=1)
        baris_bawah.addLayout(panel_tengah, stretch=2) 
        baris_bawah.addLayout(panel_kanan, stretch=1)

        konten_kanan.addLayout(baris_bawah)
        konten_kanan.addStretch(1) 
        layout_utama.addLayout(konten_kanan)

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
        results = self.comparison_results[:2] # Fokus 2 teratas
        dialog = ComparisonDialog(results, self)
        dialog.exec_()


    # ---------------------------------------------------------
    # METHOD UTAMA (Patokan)
    # ---------------------------------------------------------
    def ubah_mode(self, mode_baru):
        self.mode = mode_baru
        for menu, btn in self.menu_buttons.items():
            if menu == self.mode:
                btn.setStyleSheet("QPushButton { background-color: #3b6af3; color: white; font-weight: bold; border-radius: 12px; padding: 12px; text-align: left; padding-left: 20px; border: none; }")
            else:
                btn.setStyleSheet("QPushButton { background-color: transparent; color: #555; font-weight: bold; border-radius: 12px; padding: 12px; text-align: left; padding-left: 20px; border: none; } QPushButton:hover { background-color: #d1dced; }")
        
        if self.img_bgr is not None:
            self.proses_gambar()

    def buat_panel_gambar(self, title, size):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setFixedHeight(35)
        
        if title == "Pembanding":
            lbl_title.setStyleSheet("background-color: #7f8c8d; color: white; font-weight: bold; border-radius: 17px;")
        else:
            lbl_title.setStyleSheet("background-color: #3b6af3; color: white; font-weight: bold; border-radius: 17px;")
        
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setFixedSize(size, size)
        lbl_img.setStyleSheet("background-color: white; border: 2px solid #ccc; border-radius: 15px;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_img)
        return panel, lbl_img

    def buat_slider_ui(self, nama, min_val, max_val, default_val):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        lbl = QLabel(f"{nama}{default_val}")
        lbl.setStyleSheet("color: #444; font-weight: bold; font-size: 13px; border: none;")
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("QSlider::groove:horizontal { border: none; height: 6px; background: #ccc; border-radius: 3px; } QSlider::handle:horizontal { background: #3b6af3; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px; }")
        
        slider.sliderReleased.connect(self.proses_gambar)
        slider.valueChanged.connect(lambda val, l=lbl, n=nama: l.setText(f"{n}{val}"))
        
        layout.addWidget(lbl)
        layout.addWidget(slider)
        return layout, slider

    def upload_gambar(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Buka Citra MRI", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            self.img_bgr = cv2.imread(file_name)
            if self.img_bgr is not None:
                self.btn_download.setEnabled(True)
                self.btn_save_compare.setEnabled(True) 
                self.proses_gambar() 
            else:
                QMessageBox.warning(self, "Error", "Gagal memuat gambar!")

    def upload_pembanding(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Buka Citra Pembanding", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            img_pemb = cv2.imread(file_name)
            if img_pemb is not None:
                img_rgb = cv2.cvtColor(img_pemb, cv2.COLOR_BGR2RGB)
                self.lbl_pembanding.setPixmap(self.cv2_ke_qpixmap(img_rgb, self.lbl_pembanding))
            else:
                QMessageBox.warning(self, "Error", "Gagal memuat gambar pembanding!")

    def download_gambar(self):
        if self.final_result_img is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Simpan Hasil Deteksi", "hasil_tumor_final.jpg", "JPEG (*.jpg);;PNG (*.png)")
        if path:
            cv2.imwrite(path, self.final_result_img)
            QMessageBox.information(self, "Sukses", f"Gambar berhasil disimpan di:\n{path}")

    def cv2_ke_qpixmap(self, cv_img, target_label):
        if len(cv_img.shape) == 2:
            h, w = cv_img.shape
            bytes_per_line = w
            qt_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        else:
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w
            qt_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        return QPixmap.fromImage(qt_img).scaled(target_label.width(), target_label.height(), Qt.KeepAspectRatio)

    # ---------------------------------------------------------
    # ALGORITMA OPENCV (Patokan Utama)
    # ---------------------------------------------------------
    def proses_gambar(self):
        if self.img_bgr is None:
            return

        val_thresh = self.lbl_val_th.value()
        val_circ   = self.lbl_val_circ.value() / 100.0
        val_area   = self.lbl_val_area.value()

        # 1. PRE-PROCESSING
        img_rgb  = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB)
        img_gray = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2GRAY)
        self.lbl_asli.setPixmap(self.cv2_ke_qpixmap(img_rgb, self.lbl_asli))

        not_white = img_gray < 254
        rows = np.any(not_white, axis=1)
        cols = np.any(not_white, axis=0)
        if rows.any() and cols.any():
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            mri_rgb  = img_rgb[rmin:rmax, cmin:cmax]
            mri_gray = img_gray[rmin:rmax, cmin:cmax].copy()
            mri_gray[mri_gray > 253] = 0   
        else:
            mri_rgb  = img_rgb
            mri_gray = img_gray.copy()
        h, w = mri_gray.shape

        # 2. SKULL STRIPPING
        _, head_mask = cv2.threshold(mri_gray, 15, 255, cv2.THRESH_BINARY)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))
        closed_head  = cv2.morphologyEx(head_mask, cv2.MORPH_CLOSE, kernel_close)
        
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        cleaned_head = cv2.morphologyEx(closed_head, cv2.MORPH_OPEN, kernel_clean)
        
        kernel_agg   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25,25))
        mask_pedoman = cv2.erode(cleaned_head, kernel_agg, iterations=1)
        
        brain_only = cv2.bitwise_and(mri_gray, mask_pedoman)

        # 3. ENHANCEMENT
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        brain_enhanced = clahe.apply(brain_only)
        blurred_brain  = cv2.bilateralFilter(brain_enhanced, 7, 50, 50)
        self.lbl_clahe.setPixmap(self.cv2_ke_qpixmap(blurred_brain, self.lbl_clahe))
        self.lbl_kandidat.setStyleSheet("background-color: white; border: 2px solid #ccc; border-radius: 15px;")

        # 4. SEGMENTASI
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
        
        contours, _ = cv2.findContours(thresh_closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        # 5. FEATURE EXTRACTION
        valid = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < val_area or area > 50000:
                continue
            
            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            circ = 4 * np.pi * area / (peri ** 2)
            if circ < val_circ:
                continue
            
            (cx, cy), r = cv2.minEnclosingCircle(cnt)
            if cx < 10 or cx > w - 10 or cy < 10 or cy > h - 10:
                continue
            
            valid.append((cnt, area, circ, int(cx), int(cy), int(r)))

        # 6. PENGGAMBARAN & EKSTRAKSI DATA KLINIS
        thresh_rgb = cv2.cvtColor(thresh_closed, cv2.COLOR_GRAY2RGB)
        final_img = mri_rgb.copy()

        # JIKA AREA BERSIH
        if not valid:
            self.lbl_kandidat.clear()
            self.lbl_kandidat.setText("Area Bersih\n(Tidak ada anomali)")
            self.lbl_final.clear()
            
            img_normal = mri_rgb.copy()
            cv2.putText(img_normal, "STATUS: NORMAL (NO TUMOR)", (15, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            
            self.lbl_final.setPixmap(self.cv2_ke_qpixmap(img_normal, self.lbl_final))
            
            dl_img = cv2.cvtColor(img_normal, cv2.COLOR_RGB2BGR)
            cv2.putText(dl_img, "Data Klinis: STATUS NORMAL (Tidak terdeteksi anomali)", (15, 35), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(dl_img, "Data Klinis: STATUS NORMAL (Tidak terdeteksi anomali)", (15, 35), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
            self.final_result_img = dl_img
            
            self.lbl_info_klinis.setText("Data Klinis:\n\n✅ STATUS: NORMAL\nTidak terdeteksi anomali.")

            # Record untuk perbandingan
            self.last_result_data = {
                "mode": self.mode,
                "status": "NORMAL",
                "area_px": 0,
                "area_cm2": "0.00",
                "diameter_cm": "0.00",
                "center": "-",
                "lokasi": "-",
                "original_preview": mri_rgb.copy(),
                "result_preview": img_normal.copy()
            }
            return

        # MENCARI BATAS TERLUAR KEPALA (SKULL BOUNDING BOX)
        contours_kepala, _ = cv2.findContours(cleaned_head, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours_kepala:
            kontur_terbesar = max(contours_kepala, key=cv2.contourArea)
            x_kep, y_kep, w_kep, h_kep = cv2.boundingRect(kontur_terbesar)
            
            cv2.rectangle(final_img, (x_kep, y_kep), (x_kep + w_kep, y_kep + h_kep), (150, 150, 150), 1)
            cv2.putText(final_img, "Skull Bounds", (x_kep, y_kep - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1, cv2.LINE_AA)
        else:
            x_kep, y_kep = 0, 0 

        info_text = "Data Klinis Tumor:\n"

        for idx, item in enumerate(valid, 1):
            cnt, area_asli, circ, cx, cy, r = item
            
            cv2.drawContours(thresh_rgb, [cnt], -1, (255, 0, 0), 2)
            cv2.circle(thresh_rgb, (cx, cy), r, (0, 255, 0), 2)
            cv2.drawContours(final_img, [cnt], -1, (0, 0, 255), 3) 
            
            cv2.putText(final_img, str(idx), (cx + r + 5, cy), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2, cv2.LINE_AA)
            
            jarak_x_dari_kiri = cx - x_kep
            jarak_y_dari_atas = cy - y_kep
            
            info_text += f"\n- Tumor {idx}\n"
            info_text += f"  - Luas Area : {int(area_asli)} px\n"
            info_text += f"  - Kedalaman (X) : {jarak_x_dari_kiri} px dr tepi\n"
            info_text += f"  - Kedalaman (Y) : {jarak_y_dari_atas} px dr atas\n"

        ui_text = info_text.replace("Data Klinis Tumor:", "📊 Data Klinis Tumor:").replace("- Tumor", "🔹 Tumor")
        self.lbl_info_klinis.setText(ui_text)

        self.lbl_kandidat.setPixmap(self.cv2_ke_qpixmap(thresh_rgb, self.lbl_kandidat))
        self.lbl_final.setPixmap(self.cv2_ke_qpixmap(final_img, self.lbl_final))
        
        dl_img = cv2.cvtColor(final_img, cv2.COLOR_RGB2BGR)
        teks_bersih = info_text.split("\n")
        
        y_pos = 35 
        for baris in teks_bersih:
            if baris.strip():
                cv2.putText(dl_img, baris.rstrip(), (15, y_pos), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(dl_img, baris.rstrip(), (15, y_pos), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
                y_pos += 25 
                
        self.final_result_img = dl_img

        # Record untuk perbandingan (mengambil data tumor pertama/terbesar)
        cnt_f, area_f, circ_f, cx_f, cy_f, r_f = valid[0]
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Poppins", 10))
    window = DeteksiTumorApp()
    window.show()
    sys.exit(app.exec_())