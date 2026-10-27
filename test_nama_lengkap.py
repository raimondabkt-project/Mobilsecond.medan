from app import create_app
from elasticsearch_utils import es, buat_index, index_mobil, cari_mobil, Config
from models import Mobil

app = create_app()

with app.app_context():
    # WAJIB hapus index lama karena ada field baru: nama_lengkap
    if es.indices.exists(index=Config.INDEX_NAME):
        es.indices.delete(index=Config.INDEX_NAME)
        print("Index lama dihapus")

    buat_index()
    for m in Mobil.query.all():
        index_mobil(m)
        print(f"OK {m.kode_mobil} | {m.merek} {m.model}")
    es.indices.refresh(index=Config.INDEX_NAME)
    print("Re-index selesai\n")

    tests = [
        "Pajero Sport",
        "GLX 4x4",
        "E 250",
        "CX-5",
        "CX-5 Kuro",
        "Xforce Ultimate",
        "Civic Hatchback",
        "Brio E 1.2",
        "pajro",
        "xforse",
        "mazda",
        "honda",
    ]

    for q in tests:
        hits = cari_mobil(q, limit=10)
        print("=" * 60)
        print(f"Query: '{q}' -> {len(hits)} hasil")
        for h in hits:
            s = h["_source"]
            print(f"  {s.get('kode_mobil')} | {s.get('nama_lengkap')} | skor={h.get('_score'):.4f}")
        if not hits:
            print("  (tidak ada hasil)")