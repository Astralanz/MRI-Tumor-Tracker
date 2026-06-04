MRI Tumor Tracker
Merupakan aplikasi untuk mentracker mengawasi perkembangan tumor otak terkhususnya meningioma dan glioma, semasa perawatan atau pengobatan pasien

Alur Pemrosesan :

1. Gambar Asli akan diubah menjadi Grayscale dengan cv2.COLOR_BGR2GRAY proces ini membuat citra memadatkan warnanya agar lebih ringan dan mudah di eksekusi
2. Masking
  a). Sistem membuat "cetakan" biner (masking) area kepala (threshold).
  b). Membersihkan cetakan dari bintik-bintik noise (morphologyEx).
  c). Mengikis bagian terluar cetakan tersebut (erode) sehingga area tulang tengkorak tidak ikut tercetak.
  d). Terakhir, menempelkan cetakan yang sudah dikikis ini ke gambar otak asli (bitwise_and). Bagian di luar cetakan otomatis menjadi hitam pekat.
4. Eksekusi
   cv2.threshold() (menggunakan cv2.THRESH_OTSU atau nilai slider manual) dan cv2.morphologyEx()
   Proses mengubah gambar otak yang sudah di-enhance menjadi gambar biner (hanya ada hitam dan putih murni). Bagian yang lebih cerah dari nilai threshold (ambang batas) akan diubah jadi putih pekat
   (dianggap sebagai kandidat tumor), sisanya jadi hitam. Setelah itu, dilakukan operasi morfologi (Closing & Opening) lagi untuk merapikan hasil putih-putihnya agar tidak bolong-bolong.
6. Countur dan kordinat
  a). cv2.findContours(), Untuk mencari dan menandari tumor dengan garis outline
  B). cv2.contourArea(), Untuk menghitung luas area tumor
  c). cv2.arcLength(), dan cv2.minEnclosingCircle() menghitung seberapa panjang garis lingkaran

8. Hasil
  cv2.drawContours(), cv2.circle(), cv2.putText()
  Hasil dari proses sebelumnya di pindahkan ke hasil final, dengan tambahan cordinat

  Alur Pengguna :
  1. User upload Tumor MRI ke aplikasi
  2. Aplikasi akan memproses (Masking dan execution)
  3. User bisa langsung menggunakan parameterbatas kecerahan 0 jika ingin langsung hasil(tidak akurat)
  4. Atau user bisa mengatur batas kecerahan, batas besar tumor, dan kelenturan garis countur
  5. Hasil akan tampil di layar beserta data klinis yg berisi kordinat dan luas tumor
  6. User bisa mendownload gambar tumor yg sudah di proses aplikasi (sekaligus keterangannya tertera pada gambar)
  7. anggap 1 bulan kemudian user bisa mengecek kembali dengan 1-6 lalu mengupload pembandingan dengan gambar 1 bulan lalu untuk membandingkan

  #Note
  Telah dilakukan 10 pengujian meningioma dan giloma dengan parameter yang sama (PPT) dengan hasil memuaskan

  Parameter Default :
  Batas kecerahan 0 (artinya otomatis dan kurang akurat)
  Toleransi lingkaran 20
  Luas Lingkaran 150

  Merupakan Project dari Tim DeTumors
