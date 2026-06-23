from elasticsearch import Elasticsearch
from config import Config

# Koneksi ke Elasticsearch
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
    doc = {
        "kode_mobil": mobil.kode_mobil,
        "merek": mobil.merek,
        "model": mobil.model,
        "tahun": mobil.tahun,
        "harga": mobil.harga,
        "kilometer": mobil.kilometer,
        "transmisi": mobil.transmisi,
        "deskripsi": mobil.deskripsi,
        "status": mobil.status
    }
    # Gunakan mobil.id sebagai document ID (bukan kode_mobil)
    es.index(index=Config.INDEX_NAME, id=mobil.id, body=doc)


def cari_mobil(query="", limit=50):
    if not query:
        body = {"query": {"match_all": {}}}
    else:
        body = {
            "query": {
                "bool": {
                    "should": [
                        # Prioritas tinggi: cocok persis / sebagian
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["merek^6", "model^5", "deskripsi^2"],
                                "type": "best_fields"
                            }
                        },
                        # Prioritas sedang: toleransi salah ketik
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["merek", "model"],
                                "fuzziness": 2,
                                "prefix_length": 0,
                                "max_expansions": 50
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        }

    response = es.search(index=Config.INDEX_NAME, body=body, size=limit)
    return response['hits']['hits']