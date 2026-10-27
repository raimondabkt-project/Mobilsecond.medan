from elasticsearch import Elasticsearch
from config import Config

es = Elasticsearch([Config.ELASTICSEARCH_HOST])


def buat_index():
    """Buat index Elasticsearch jika belum ada"""
    if not es.indices.exists(index=Config.INDEX_NAME):
        mapping = {
            "mappings": {
                "properties": {
                    "kode_mobil": {"type": "keyword"},
                    "merek": {"type": "text"},
                    "model": {"type": "text"},
                    "nama_lengkap": {"type": "text"},
                    "tahun": {"type": "integer"},
                    "harga": {"type": "long"},
                    "kilometer": {"type": "integer"},
                    "transmisi": {"type": "keyword"},
                    "deskripsi": {"type": "text"},
                    "status": {"type": "keyword"}
                }
            }
        }
        es.indices.create(index=Config.INDEX_NAME, body=mapping)
        print(f"✅ Index '{Config.INDEX_NAME}' berhasil dibuat.")
    else:
        print(f"✅ Index '{Config.INDEX_NAME}' sudah ada.")


def index_mobil(mobil):
    """Simpan data mobil ke Elasticsearch"""
    merek = (mobil.merek or "").strip()
    model = (mobil.model or "").strip()
    nama_lengkap = f"{merek} {model}".strip()

    doc = {
        "kode_mobil": mobil.kode_mobil,
        "merek": merek,
        "model": model,
        "nama_lengkap": nama_lengkap,
        "tahun": mobil.tahun,
        "harga": mobil.harga,
        "kilometer": mobil.kilometer,
        "transmisi": mobil.transmisi,
        "deskripsi": mobil.deskripsi,
        "status": mobil.status
    }
    es.index(index=Config.INDEX_NAME, id=mobil.id, document=doc)


def cari_mobil(query="", limit=50):
    """
    Mode adaptif:
    - Query pendek (1-2 kata): partial + fuzzy
    - Query panjang (nama lengkap): ketat, prioritas mobil yang paling cocok
    """
    if not query or not query.strip():
        body = {"query": {"match_all": {}}}
        response = es.search(index=Config.INDEX_NAME, body=body, size=limit)
        return response["hits"]["hits"]

    query = query.strip()
    jumlah_kata = len(query.split())

    # ==================== MODE NAMA LENGKAP (3 kata atau lebih) ====================
    if jumlah_kata >= 3:
        body = {
            "query": {
                "bool": {
                    "should": [
                        # Sangat kuat: phrase hampir sama
                        {
                            "match_phrase": {
                                "nama_lengkap": {
                                    "query": query,
                                    "slop": 2,
                                    "boost": 50
                                }
                            }
                        },
                        # Semua kata harus ada di nama lengkap
                        {
                            "match": {
                                "nama_lengkap": {
                                    "query": query,
                                    "operator": "and",
                                    "boost": 25
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            # Ketat: buang mobil yang cuma cocok sebagian kecil
            "min_score": 8.0
        }

    # ==================== MODE PENDEK (1-2 kata): partial + fuzzy ====================
    else:
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase": {
                                "nama_lengkap": {
                                    "query": query,
                                    "boost": 15
                                }
                            }
                        },
                        {
                            "match": {
                                "nama_lengkap": {
                                    "query": query,
                                    "operator": "and",
                                    "boost": 10
                                }
                            }
                        },
                        {
                            "match": {
                                "nama_lengkap": {
                                    "query": query,
                                    "operator": "or",
                                    "minimum_should_match": "50%",
                                    "boost": 4
                                }
                            }
                        },
                        {
                            "match": {
                                "nama_lengkap": {
                                    "query": query,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 1,
                                    "boost": 3
                                }
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["merek^4", "model^4"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "prefix_length": 1,
                                "boost": 2
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "min_score": 1.0
        }

    response = es.search(index=Config.INDEX_NAME, body=body, size=limit)
    return response["hits"]["hits"]


def cari_mobil_dengan_penjelasan(query="", limit=5):
    if not query:
        return []

    try:
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["nama_lengkap^8", "merek^6", "model^5", "deskripsi^2"],
                    "type": "best_fields"
                }
            }
        }
        response = es.search(
            index=Config.INDEX_NAME,
            body=body,
            size=limit,
            explain=True
        )
        hasil = []
        for hit in response["hits"]["hits"]:
            hasil.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "source": hit["_source"],
                "explanation": hit.get("_explanation", {})
            })
        return hasil
    except Exception as e:
        print(f"⚠️ Error koneksi Elasticsearch: {e}")
        return []