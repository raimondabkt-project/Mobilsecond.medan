from app import create_app
from models import Mobil
from elasticsearch_utils import index_mobil, buat_index

app = create_app()

with app.app_context():
    print("=== Re-Index Semua Mobil ===")
    buat_index()
    
    mobils = Mobil.query.all()
    print(f"Total mobil: {len(mobils)}")
    
    success = 0
    for mobil in mobils:
        try:
            index_mobil(mobil)
            success += 1
            print(f"✅ {mobil.kode_mobil} - {mobil.merek} {mobil.model}")
        except Exception as e:
            print(f"❌ Gagal: {mobil.kode_mobil} → {e}")
    
    print(f"\nBerhasil di-index: {success} mobil")