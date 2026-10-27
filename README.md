
# Mobilsecond.medan

Platform web marketplace jual-beli mobil bekas berbasis pencarian cerdas menggunakan **Flask**, **MySQL**, dan **Elasticsearch**.


## Tech Stack

* **Backend:** Python, Flask, SQLAlchemy
* **Database:** MySQL
* **Search Engine:** Elasticsearch
* **Frontend:** HTML5, CSS3, Tailwind CSS, JavaScript


## Main Fiture
* **Manajemen Akun & Seller:** Autentikasi pengguna dan pendaftaran akun *seller*.
* **Pencarian Cerdas (Elasticsearch):** Memungkinkan pencarian kendaraan secara cepat dan relevan menggunakan fitur *indexing*.
* **Manajemen Data Kendaraan:** Unggah foto mobil, detail spesifikasi, dan harga.
* **Fitur Favorit:** Menyimpan daftar kendaraan impian pengguna.
## Run Locally

Ikuti langkah-langkah di bawah ini untuk menjalankan project ini di komputer/laptop lokal kamu:

Clone the project

```bash
  git clone https://github.com/raimondabkt-project/Mobilsecond.medan
```

Buat dan Aktifkan Virtual Environment

```bash
  python -m venv venv
.\venv\Scripts\Activate
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Konfigurasi Environment (.env)

```bash
  DATABASE_URL=mysql+mysqlconnector://root:password_kamu@localhost/mobilsecond_db
ES_HOST=http://localhost:9200
```

Siapkan Database MySQL

```bash
  Buat database baru di MySQL Workbench / phpMyAdmin dengan nama: mobilsecond_db
```

Jalankan Aplikasi Flask

```bash
  python app.py
```