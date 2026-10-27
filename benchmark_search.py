import time
from app import create_app
from models import Mobil
from elasticsearch_utils import cari_mobil

app = create_app()

QUERIES = ["pajero", "hyundai", "stargazer", "mercedes"]

def waktu_mysql(query, ulang=5):
    total = 0
    with app.app_context():
        for _ in range(ulang):
            t0 = time.perf_counter()
            Mobil.query.filter(
                (Mobil.status == "Ready") &
                (
                    (Mobil.merek.ilike(f"%{query}%")) |
                    (Mobil.model.ilike(f"%{query}%"))
                )
            ).all()
            total += (time.perf_counter() - t0) * 1000
    return round(total / ulang, 1)

def waktu_es(query, ulang=5):
    total = 0
    with app.app_context():
        for _ in range(ulang):
            t0 = time.perf_counter()
            cari_mobil(query=query, limit=50)
            total += (time.perf_counter() - t0) * 1000
    return round(total / ulang, 1)

if __name__ == "__main__":
    print("=" * 60)
    print("BENCHMARK PENCARIAN - Mobilsecond.medan")
    print("=" * 60)
    print(f"{'Query':<15} {'MySQL(ms)':>12} {'ES(ms)':>12}")
    print("-" * 60)

    mysql_list, es_list = [], []
    for q in QUERIES:
        m = waktu_mysql(q)
        e = waktu_es(q)
        mysql_list.append(m)
        es_list.append(e)
        print(f"{q:<15} {m:>12} {e:>12}")

    print("-" * 60)
    avg_m = sum(mysql_list) / len(mysql_list)
    avg_e = sum(es_list) / len(es_list)
    print(f"{'RATA-RATA':<15} {avg_m:>12.1f} {avg_e:>12.1f}")
    print("=" * 60)