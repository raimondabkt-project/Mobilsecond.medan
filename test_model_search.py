from app import create_app
from elasticsearch_utils import es, buat_index, index_mobil, cari_mobil, Config
from models import Mobil

app = create_app()

with app.app_context():
    # re-index
    if es.indices.exists(index=Config.INDEX_NAME):
        es.indices.delete(index=Config.INDEX_NAME)
    buat_index()
    for m in Mobil.query.all():
        index_mobil(m)
    es.indices.refresh(index=Config.INDEX_NAME)
    print("Re-index selesai\n")

    tests = [
        "CX-5",
        "cx-5",
        "pajero",
        "brio",
        "civic",
        "xforce",
        "innova",
        "mazda",
        "honda",
        "pajro",   # typo - fuzzy
    ]

    for q in tests:
        hits = cari_mobil(q, limit=10)
        print("=" * 60)
        print(f"Query: '{q}' -> {len(hits)} hasil")
        for h in hits:
            s = h["_source"]
            print(f"  {s.get('kode_mobil')} | {s.get('merek')} {s.get('model')} | skor={h.get('_score'):.4f}")
        if not hits:
            print("  (tidak ada hasil)")