import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

class DeteksiTumorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deteksi Meningioma - Semi Otomatis (Numbered Multi-Tumor)")
        self.setGeometry(50, 100, 1500, 600) 
        
        self.img_bgr = None
        self.final_result_img = None
        
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout_utama = QVBoxLayout()
        
        # --- PANEL TOMBOL ATAS ---
        layout_tombol = QHBoxLayout()
        
        btn_upload = QPushButton("📁 Upload Gambar MRI")
        btn_upload.setMinimumHeight(40)
        btn_upload.clicked.connect(self.upload_gambar)
        
        self.btn_download = QPushButton("💾 Simpan Hasil (Panel 4)")
        self.btn_download.setMinimumHeight(40)
        self.btn_download.clicked.connect(self.download_gambar)
        self.btn_download.setEnabled(False) 
        
        layout_tombol.addWidget(btn_upload)
        layout_tombol.addWidget(self.btn_download)
        layout_utama.addLayout(layout_tombol)

        # --- LAYOUT GAMBAR NYAMPING (1x4) ---
        layout_gambar = QHBoxLayout()
        self.lbl_asli = self.buat_label_gambar("1. Gambar Asli\n(Pilih Upload)")
        self.lbl_clahe = self.buat_label_gambar("2. Otak Bersih\n(Masking + CLAHE)")
        self.lbl_kandidat = self.buat_label_gambar("3. Kandidat\nThreshold")
        self.lbl_final = self.buat_label_gambar("4. Hasil Final\n(Contour Matching)")
        
        layout_gambar.addWidget(self.lbl_asli)
        layout_gambar.addWidget(self.lbl_clahe)
        layout_gambar.addWidget(self.lbl_kandidat)
        layout_gambar.addWidget(self.lbl_final)
        layout_utama.addLayout(layout_gambar)

        # --- PANEL KONTROL (SLIDERS) ---
        layout_kontrol = QHBoxLayout()
        
        self.slider_thresh, layout_th = self.buat_slider("Batas Kecerahan (0=Otsu Auto)", 0, 255, 0)
        self.slider_circ, layout_circ = self.buat_slider("Toleransi Kebulatan", 1, 90, 20)
        self.slider_area, layout_area = self.buat_slider("Ukuran Minimum Tumor", 50, 2000, 150)

        layout_kontrol.addLayout(layout_th)
        layout_kontrol.addLayout(layout_circ)
        layout_kontrol.addLayout(layout_area)
        layout_utama.addLayout(layout_kontrol)

        main_widget.setLayout(layout_utama)

    def buat_label_gambar(self, teks):
        lbl = QLabel(teks)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("border: 1px solid #aaa; background-color: #e0e0e0;")
        # FIX: Ukuran dikunci mati 340x340 biar ga ada drama gambar nge-zoom lagi
        lbl.setFixedSize(340, 340) 
        return lbl

    def buat_slider(self, nama, min_val, max_val, default_val):
        layout = QVBoxLayout()
        lbl = QLabel(f"{nama}: {default_val}")
        lbl.setAlignment(Qt.AlignCenter)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default_val)
        
        slider.sliderReleased.connect(self.proses_gambar)
        slider.valueChanged.connect(lambda val, l=lbl, n=nama: l.setText(f"{n}: {val}"))
        
        layout.addWidget(lbl)
        layout.addWidget(slider)
        return slider, layout

    def upload_gambar(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Buka Citra MRI", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            self.img_bgr = cv2.imread(file_name)
            if self.img_bgr is not None:
                self.btn_download.setEnabled(True)
                self.proses_gambar()
            else:
                QMessageBox.warning(self, "Error", "Gagal memuat gambar!")

    def download_gambar(self):
        if self.final_result_img is None:
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Simpan Hasil Deteksi", "hasil_tumor.jpg", "JPEG (*.jpg);;PNG (*.png)")
        if path:
            cv2.imwrite(path, self.final_result_img)
            QMessageBox.information(self, "Sukses", f"Gambar berhasil disimpan di:\n{path}")

    def cv2_ke_qpixmap(self, cv_img):
        if len(cv_img.shape) == 2:
            h, w = cv_img.shape
            bytes_per_line = w
            qt_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        else:
            h, w, ch = cv_img.shape
            bytes_per_line = ch * w
            qt_img = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        return QPixmap.fromImage(qt_img).scaled(self.lbl_asli.width(), self.lbl_asli.height(), Qt.KeepAspectRatio)

    def proses_gambar(self):
        if self.img_bgr is None:
            return

        val_thresh = self.slider_thresh.value()
        val_circ   = self.slider_circ.value() / 100.0
        val_area   = self.slider_area.value()

        # ==========================================
        # 1. PRE-PROCESSING DASAR
        # ==========================================
        img_rgb  = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2RGB)
        img_gray = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2GRAY)
        self.lbl_asli.setPixmap(self.cv2_ke_qpixmap(img_rgb))

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

        # ==========================================
        # 2. SKULL STRIPPING AGRESIF
        # ==========================================
        _, head_mask = cv2.threshold(mri_gray, 15, 255, cv2.THRESH_BINARY)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))
        closed_head  = cv2.morphologyEx(head_mask, cv2.MORPH_CLOSE, kernel_close)
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        cleaned_head = cv2.morphologyEx(closed_head, cv2.MORPH_OPEN, kernel_clean)
        kernel_agg   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25,25))
        mask_pedoman = cv2.erode(cleaned_head, kernel_agg, iterations=1)

        brain_only = cv2.bitwise_and(mri_gray, mask_pedoman)

        # ==========================================
        # 3. ENHANCEMENT
        # ==========================================
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        brain_enhanced = clahe.apply(brain_only)
        blurred_brain  = cv2.bilateralFilter(brain_enhanced, 7, 50, 50)
        self.lbl_clahe.setPixmap(self.cv2_ke_qpixmap(blurred_brain))

        # ==========================================
        # 4. SEGMENTASI (Otsu Auto vs Manual)
        # ==========================================
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

        # ==========================================
        # 5. FILTER FITUR GEOMETRI
        # ==========================================
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

        # ==========================================
        # 6. MENGGAMBAR MULTI-TUMOR + PENOMORAN
        # ==========================================
        if not valid:
            self.lbl_kandidat.setText("Tumor Tidak Ditemukan\n(Turunkan Area / Kebulatan)")
            self.lbl_final.setText("Gagal")
            self.final_result_img = mri_rgb 
            return

        thresh_rgb = cv2.cvtColor(thresh_closed, cv2.COLOR_GRAY2RGB)
        final_img = mri_rgb.copy()

        # Looping ke SEMUA tumor yang lolos saringan (idx dimulai dari 1)
        for idx, item in enumerate(valid, 1):
            cnt, area, circ, cx, cy, r = item
            
            # Gambar di Panel 3 (Sketsa Merah & Ijo)
            cv2.drawContours(thresh_rgb, [cnt], -1, (255, 0, 0), 2)
            cv2.circle(thresh_rgb, (cx, cy), r, (0, 255, 0), 2)
            
            # Gambar di Panel 4 (Garis Biru Tebal)
            cv2.drawContours(final_img, [cnt], -1, (0, 0, 255), 3) 
            
            # REVISI: Tambah tulisan angka (Kuning Terang) di dekat titik pusat tumor (cx, cy)
            # Koordinat sedikit digeser (cx-10, cy+10) biar angkanya pas di tengah/samping kontur
            cv2.putText(final_img, str(idx), (cx - 10, cy - r - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2, cv2.LINE_AA)

        # Update gambar di layar aplikasi
        self.lbl_kandidat.setPixmap(self.cv2_ke_qpixmap(thresh_rgb))
        self.lbl_final.setPixmap(self.cv2_ke_qpixmap(final_img))
        
        # Simpan format BGR buat di-download (biar hasil download ada nomornya juga)
        self.final_result_img = cv2.cvtColor(final_img, cv2.COLOR_RGB2BGR)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    font = QFont("Poppins")
    app.setFont(font)
    
    window = DeteksiTumorApp()
    window.show()
    sys.exit(app.exec_())