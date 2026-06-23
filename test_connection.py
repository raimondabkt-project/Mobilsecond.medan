from elasticsearch_utils import buat_index, es
from config import Config

print("=== Test Koneksi Elasticsearch ===")
try:
    info = es.info()
    print("✅ Berhasil konek ke Elasticsearch")
    print("Cluster:", info['cluster_name'])
    print("Version:", info['version']['number'])
except Exception as e:
    print("❌ Error:", e)

print("\n=== Membuat Index ===")
buat_index()