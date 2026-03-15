import pathlib, json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

QDRANT_PATH = "data/qdrant_db"
COLLECTION  = "eu_ai_act"
EMBED_DIM   = 384

# Charger les 96 articles depuis le JSON
articles_path = pathlib.Path("data/eu_ai_act_articles.json")
if articles_path.exists():
    ARTICLES = json.loads(articles_path.read_text(encoding="utf-8"))
    print(f"[OK] {len(ARTICLES)} articles charges depuis eu_ai_act_articles.json")
else:
    print("[WARN] eu_ai_act_articles.json non trouve - utilisation articles de base")
    ARTICLES = [
        {"id":"art5",  "num":"Article 5",  "title":"Prohibited AI Practices", "framework":"eu_ai_act", "text":"The following AI practices shall be prohibited: subliminal techniques beyond consciousness, exploiting vulnerabilities, social scoring by public authorities, real-time remote biometric identification in public spaces by law enforcement."},
        {"id":"art6",  "num":"Article 6",  "title":"Classification of High-Risk AI Systems", "framework":"eu_ai_act", "text":"AI system shall be considered high-risk where intended to be used as safety component of product covered by Union harmonisation legislation listed in Annex I, or listed in Annex III."},
        {"id":"art9",  "num":"Article 9",  "title":"Risk Management System", "framework":"eu_ai_act", "text":"A risk management system shall be established, implemented, documented and maintained in relation to high-risk AI systems throughout their entire lifecycle."},
        {"id":"art10", "num":"Article 10", "title":"Data and Data Governance", "framework":"eu_ai_act", "text":"High-risk AI systems shall be developed on basis of training, validation and testing data sets that meet quality criteria. Training data shall be subject to appropriate data governance practices."},
        {"id":"art11", "num":"Article 11", "title":"Technical Documentation", "framework":"eu_ai_act", "text":"Technical documentation of a high-risk AI system shall be drawn up before placed on the market and kept up-to-date, demonstrating compliance with all requirements."},
        {"id":"art13", "num":"Article 13", "title":"Transparency and Information", "framework":"eu_ai_act", "text":"High-risk AI systems shall be transparent, providing sufficient information to deployers including capabilities, limitations, performance metrics, and human oversight measures."},
        {"id":"art14", "num":"Article 14", "title":"Human Oversight", "framework":"eu_ai_act", "text":"High-risk AI systems shall allow effective oversight by natural persons during use, designed to allow override, intervention, and refusal of outputs."},
        {"id":"art52", "num":"Article 52", "title":"Transparency for GPAI", "framework":"eu_ai_act", "text":"Providers of general-purpose AI models shall draw up technical documentation and provide information to downstream providers integrating the GPAI model."},
        {"id":"gdpr22","num":"GDPR Article 22","title":"Automated Decision Making","framework":"gdpr","text":"Data subject has right not to be subject to decision based solely on automated processing including profiling which produces legal or significant effects."},
        {"id":"nist_govern","num":"NIST GOVERN","title":"AI Risk Governance","framework":"nist_ai_rmf","text":"GOVERN function ensures policies, processes and practices are in place so AI risk management is integrated into organizational processes."},
    ]

def main():
    pathlib.Path(QDRANT_PATH).mkdir(parents=True, exist_ok=True)
    
    print("[...] Chargement sentence-transformers all-MiniLM-L6-v2...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Verifier dimension
    test_dim = len(model.encode("test"))
    print(f"[OK] Dimension embeddings : {test_dim}")
    
    client = QdrantClient(path=QDRANT_PATH)
    
    # Supprimer toutes les collections existantes
    for col in client.get_collections().collections:
        client.delete_collection(col.name)
        print(f"[OK] Collection supprimee : {col.name}")
    
    # Creer la collection eu_ai_act avec dim=384
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=test_dim, distance=Distance.COSINE)
    )
    print(f"[OK] Collection {COLLECTION} creee dim={test_dim}")
    
    points = []
    for i, art in enumerate(ARTICLES):
        text = f"{art['num']} -- {art['title']}\n{art['text']}"
        vec = model.encode(text).tolist()
        points.append(PointStruct(
            id=i+1,
            vector=vec,
            payload={
                "article_num":   art["num"],
                "article_title": art["title"],
                "framework":     art["framework"],
                "text":          art["text"],
                "chunk_id":      art.get("id", str(i)),
            }
        ))
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(ARTICLES)} encodes...")
    
    client.upsert(collection_name=COLLECTION, points=points)
    count = client.get_collection(COLLECTION).points_count
    print(f"[OK] {count} articles indexes dans Qdrant dim={test_dim}")

main()
