from app import create_app
from elasticsearch_utils import es, Config
from models import Mobil

app = create_app()

with app.app_context():
    print("=" * 80)
    print("PENGUJIAN SKOR BM25 - KATALOG MOBIL")
    print("=" * 80)

    # Ambil data mobil dari database (otomatis)
    mobil_list = Mobil.query.filter_by(status='Ready').all()

    if not mobil_list:
        print("Tidak ada data mobil di katalog.")
    else:
        # Buat query otomatis dari merek & model
        queries = set()
        for mobil in mobil_list:
            if mobil.merek:
                queries.add(mobil.merek.lower().strip())
            if mobil.model:
                kata_model = mobil.model.lower().strip().split()[0]
                queries.add(kata_model)

        queries = sorted(list(queries))

        print(f"Total mobil di katalog : {len(mobil_list)}")
        print(f"Total query diuji      : {len(queries)}")
        print("=" * 80)

        for q in queries:
            res = es.search(
                index=Config.INDEX_NAME,
                body={
                    "query": {
                        "multi_match": {
                            "query": q,
                            "fields": ["merek^6", "model^5", "deskripsi^2"],
                            "fuzziness": 1
                        }
                    }
                },
                size=3
            )

            hits = res["hits"]["hits"]
            print(f"\nQuery: \"{q}\" → {len(hits)} hasil")
            print("-" * 60)

            if not hits:
                print("  Tidak ada hasil ditemukan.")
                continue

            for i, hit in enumerate(hits, 1):
                s = hit["_source"]
                score = hit.get("_score", 0)

                # Tentukan tingkat relevansi
                if score >= 12:
                    tingkat = "Sangat Relevan"
                elif score >= 8:
                    tingkat = "Relevan"
                elif score >= 4:
                    tingkat = "Cukup Relevan"
                else:
                    tingkat = "Kurang Relevan"

                print(f"  {i}. {s.get('kode_mobil')} | {s.get('merek')} {s.get('model')}")
                print(f"     Skor BM25       : {score:.4f}")
                print(f"     Tingkat         : {tingkat}")

    print("\n" + "=" * 80)
    print("SELESAI - Pengujian Skor BM25")
    print("=" * 80)