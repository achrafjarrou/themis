import asyncio, uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import httpx, pathlib

QDRANT_PATH = "data/qdrant_db"
COLLECTION  = "themis_regulations"
EMBED_DIM   = 768
OLLAMA_URL  = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"

ARTICLES = [
    {"num":"Art.5",  "title":"Prohibited AI Practices","text":"Article 5 EU AI Act prohibits AI systems that deploy subliminal techniques, exploit vulnerabilities, social scoring by public authorities, real-time remote biometric identification in public spaces, and AI that manipulates persons against their will."},
    {"num":"Art.6",  "title":"High-Risk Classification","text":"Article 6 classifies AI systems as high-risk when listed in Annex III including: biometric identification, critical infrastructure, education, employment, essential services, law enforcement, migration, justice and democratic processes."},
    {"num":"Art.9",  "title":"Risk Management System","text":"Article 9 requires high-risk AI providers to establish a risk management system covering identification and analysis of known and foreseeable risks, adoption of risk management measures, testing procedures, and residual risk documentation."},
    {"num":"Art.10", "title":"Data Governance","text":"Article 10 requires training, validation and testing data to meet quality criteria, be relevant, representative, free of errors and complete. Providers must examine datasets for biases and document data governance practices."},
    {"num":"Art.11", "title":"Technical Documentation","text":"Article 11 requires providers of high-risk AI systems to draw up technical documentation before placing on the market, kept up to date, demonstrating compliance with requirements of Chapter 2 of Title III."},
    {"num":"Art.12", "title":"Record-Keeping and Logging","text":"Article 12 requires high-risk AI systems to have automatic logging capabilities enabling traceability throughout the system lifecycle. Logs must be kept for minimum periods defined per sector, enabling post-market monitoring."},
    {"num":"Art.13", "title":"Transparency and Information","text":"Article 13 requires high-risk AI systems to be transparent and provide sufficient information to deployers including: identity of provider, capabilities and limitations, performance metrics, human oversight measures, and instructions for use."},
    {"num":"Art.14", "title":"Human Oversight","text":"Article 14 requires high-risk AI systems to allow effective oversight by natural persons during use. Systems must be designed to allow override, intervention, and refusal of outputs. Deployers must assign competent persons for oversight."},
    {"num":"Art.17", "title":"Quality Management System","text":"Article 17 requires providers to put a quality management system in place covering: strategy for regulatory compliance, design and development procedures, examination and testing of systems, post-market monitoring plan."},
    {"num":"Art.22", "title":"GDPR Automated Decision Making","text":"GDPR Article 22 gives individuals rights regarding automated individual decision-making including profiling that produces legal or significant effects. Individuals have right to explanation, human review, and to contest decisions."},
    {"num":"AnnexIII","title":"High-Risk AI Systems List","text":"Annex III lists high-risk AI systems: biometric identification, critical infrastructure management, education admission, employment recruitment and performance evaluation, access to essential services including credit scoring, law enforcement, migration and asylum, administration of justice."},
    {"num":"Art.52", "title":"Transparency Obligations","text":"Article 52 requires transparency obligations for certain AI systems including chatbots which must inform users they are interacting with AI, emotion recognition systems, and deep fake generation systems requiring disclosure of artificial origin."},
    {"num":"Art.72", "title":"Post-Market Monitoring","text":"Article 72 requires providers to establish post-market monitoring systems collecting and reviewing data on performance of high-risk AI systems throughout lifetime, enabling corrective actions and reporting serious incidents to market surveillance authorities."},
    {"num":"NIST-GOVERN","title":"NIST AI RMF Govern","text":"NIST AI RMF Govern function establishes organizational practices for AI risk management including policies, processes, procedures, roles and responsibilities. Organizations should establish risk tolerance, accountability structures, and organizational culture supporting trustworthy AI."},
    {"num":"NIST-MAP","title":"NIST AI RMF Map","text":"NIST AI RMF Map function categorizes AI risks in context including: identifying AI system purpose, potential impacts, affected individuals and communities, legal requirements, and organizational risk priorities."},
    {"num":"NIST-MEASURE","title":"NIST AI RMF Measure","text":"NIST AI RMF Measure function analyzes and assesses AI risks using quantitative and qualitative methods including: testing, evaluation, validation and verification of AI systems for accuracy, robustness, reliability, safety, and bias metrics."},
    {"num":"NIST-MANAGE","title":"NIST AI RMF Manage","text":"NIST AI RMF Manage function allocates resources to address identified AI risks including: risk response plans, incident response procedures, risk treatment decisions, and documentation of residual risks and accepted risks."},
]

async def embed(text):
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{OLLAMA_URL}/api/embeddings", json={"model": EMBED_MODEL, "prompt": text})
        r.raise_for_status()
        return r.json()["embedding"]

async def main():
    pathlib.Path(QDRANT_PATH).mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=QDRANT_PATH)
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
    client.create_collection(collection_name=COLLECTION,
                             vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE))
    print(f"[OK] Collection created")
    points = []
    for i, art in enumerate(ARTICLES):
        print(f"  Embedding {art['num']} ({i+1}/{len(ARTICLES)})...")
        vec = await embed(art["title"] + " " + art["text"])
        points.append(PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, art["num"])),
            vector=vec,
            payload={"article_num": art["num"], "article_title": art["title"],
                     "text": art["text"], "framework": "eu_ai_act", "frameworks": ["eu_ai_act", "gdpr", "nist_ai_rmf"], "chunk_idx": i},
        ))
    client.upsert(collection_name=COLLECTION, points=points)
    print(f"[OK] Indexed {len(points)} articles into Qdrant")

asyncio.run(main())

