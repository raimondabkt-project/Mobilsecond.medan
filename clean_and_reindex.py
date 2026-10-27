"""
clean_and_reindex.py
Script untuk menghapus index Elasticsearch + re-index semua data mobil dari database.
Tujuan: Membersihkan data duplikat di Elasticsearch.
"""

from elasticsearch_utils import es, buat_index, index_mobil
from models import Mobil
from app import create_app

app = create_app()

def clean_and_reindex():
    print("=" * 60)
    print("MEMBERSIHKAN DATA DUPLIKAT DI ELASTICSEARCH")
    print("=" * 60)

    with app.app_context():
        try:
            # 1. Hapus index lama jika ada
            if es.indices.exists(index="katalog_mobil_bekas"):
                es.indices.delete(index="katalog_mobil_bekas")
                print("✅ Index lama berhasil dihapus.")

            # 2. Buat index baru
            buat_index()

            # 3. Ambil semua mobil dari database
            mobils = Mobil.query.all()
            print(f"\nTotal mobil di database: {len(mobils)}")

            # 4. Index ulang semua mobil
            for mobil in mobils:
                index_mobil(mobil)
                print(f"   → Indexed: {mobil.kode_mobil} - {mobil.merek} {mobil.model}")

            print("\n✅ Proses re-index selesai. Data sudah bersih.")
            print("=" * 60)

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_and_reindex()