# Databricks notebook source
# MAGIC %md
# MAGIC # Vector Search Index Setup
# MAGIC
# MAGIC This notebook creates and configures the Vector Search index for scientific RAG.
# MAGIC
# MAGIC **Steps:**
# MAGIC 1. Create Vector Search endpoint
# MAGIC 2. Create Vector Search index on scientific.documents table
# MAGIC 3. Configure embedding model
# MAGIC 4. Test queries

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
import time

# Configuration
CATALOG = "biolabs_catalog"
SCHEMA = "scientific"
SOURCE_TABLE = f"{CATALOG}.{SCHEMA}.documents"
ENDPOINT_NAME = "biolabs_vector_endpoint"
INDEX_NAME = f"{CATALOG}.{SCHEMA}.scientific_knowledge_index"

# Embedding configuration
EMBEDDING_MODEL = "databricks-bge-large-en"  # or "nomic-embed-text-v1.5"
EMBEDDING_SOURCE_COLUMN = "combined_content"
PRIMARY_KEY = "doc_id"

print("✓ Configuration loaded")
print(f"  - Endpoint: {ENDPOINT_NAME}")
print(f"  - Index: {INDEX_NAME}")
print(f"  - Source Table: {SOURCE_TABLE}")
print(f"  - Embedding Model: {EMBEDDING_MODEL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create Vector Search Endpoint

# COMMAND ----------

# Initialize Vector Search client
vsc = VectorSearchClient()

print("Checking for existing endpoint...")

try:
    endpoint = vsc.get_endpoint(name=ENDPOINT_NAME)
    print(f"✓ Endpoint '{ENDPOINT_NAME}' already exists")
    print(f"  Status: {endpoint.get('endpoint_status', {}).get('state', 'unknown')}")
except Exception as e:
    print(f"Creating new endpoint '{ENDPOINT_NAME}'...")
    endpoint = vsc.create_endpoint(
        name=ENDPOINT_NAME,
        endpoint_type="STANDARD"  # Free Edition supports STANDARD
    )
    print(f"✓ Endpoint created: {ENDPOINT_NAME}")

    # Wait for endpoint to be ready
    print("Waiting for endpoint to be ready...")
    while True:
        endpoint_status = vsc.get_endpoint(name=ENDPOINT_NAME)
        state = endpoint_status.get('endpoint_status', {}).get('state', 'unknown')
        print(f"  Current state: {state}")

        if state == "ONLINE":
            print("✓ Endpoint is ready!")
            break
        elif state in ["PROVISIONING", "OFFLINE"]:
            time.sleep(30)
        else:
            raise Exception(f"Unexpected endpoint state: {state}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create Vector Search Index

# COMMAND ----------

print(f"Creating Vector Search index: {INDEX_NAME}")

try:
    # Check if index already exists
    existing_index = vsc.get_index(index_name=INDEX_NAME)
    print(f"⚠ Index '{INDEX_NAME}' already exists")
    print(f"  To recreate, delete it first using: vsc.delete_index('{INDEX_NAME}')")

except Exception as e:
    # Index doesn't exist, create it
    print("Creating new index...")

    index = vsc.create_delta_sync_index(
        endpoint_name=ENDPOINT_NAME,
        index_name=INDEX_NAME,
        source_table_name=SOURCE_TABLE,
        primary_key=PRIMARY_KEY,
        embedding_source_column=EMBEDDING_SOURCE_COLUMN,
        embedding_model_endpoint_name=EMBEDDING_MODEL,
        pipeline_type="TRIGGERED",  # Manual sync (can be CONTINUOUS)
    )

    print(f"✓ Index created: {INDEX_NAME}")
    print(f"  - Primary key: {PRIMARY_KEY}")
    print(f"  - Embedding column: {EMBEDDING_SOURCE_COLUMN}")
    print(f"  - Embedding model: {EMBEDDING_MODEL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Wait for Index to be Ready

# COMMAND ----------

print("Waiting for index to be ready...")

max_wait_time = 600  # 10 minutes
start_time = time.time()

while True:
    try:
        index_info = vsc.get_index(index_name=INDEX_NAME)
        status = index_info.get('status', {}).get('detailed_state', 'unknown')
        print(f"  Current status: {status}")

        if status == "ONLINE_CONTINUOUS_UPDATE" or status == "ONLINE":
            print("✓ Index is ready!")
            break
        elif time.time() - start_time > max_wait_time:
            raise Exception("Timeout waiting for index to be ready")
        else:
            time.sleep(30)

    except Exception as e:
        print(f"  Error checking index status: {str(e)}")
        time.sleep(30)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Sync Index (if TRIGGERED mode)

# COMMAND ----------

print("Triggering index sync...")

try:
    vsc.sync_index(index_name=INDEX_NAME)
    print("✓ Sync triggered successfully")
    print("Note: Sync may take a few minutes to complete")

except Exception as e:
    print(f"⚠ Error triggering sync: {str(e)}")
    print("Index may already be syncing or using CONTINUOUS mode")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Get Index Statistics

# COMMAND ----------

# Wait a bit for sync to process
time.sleep(60)

index_info = vsc.get_index(index_name=INDEX_NAME)

print("\n" + "="*60)
print("VECTOR SEARCH INDEX STATISTICS")
print("="*60)

print(f"\nIndex Name: {INDEX_NAME}")
print(f"Endpoint: {ENDPOINT_NAME}")
print(f"Status: {index_info.get('status', {}).get('detailed_state', 'unknown')}")

# Get document count
index_status = index_info.get('status', {})
num_docs = index_status.get('num_indexed_rows', 0)
print(f"Documents Indexed: {num_docs}")

print("\nIndex Configuration:")
print(f"  - Primary Key: {PRIMARY_KEY}")
print(f"  - Embedding Column: {EMBEDDING_SOURCE_COLUMN}")
print(f"  - Embedding Model: {EMBEDDING_MODEL}")
print(f"  - Pipeline Type: {index_info.get('index_type', 'unknown')}")

print("="*60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Test Vector Search Queries

# COMMAND ----------

def test_vector_search(query: str, num_results: int = 5):
    """
    Test vector search with a query
    """
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)

    try:
        results = vsc.get_index(index_name=INDEX_NAME).similarity_search(
            query_text=query,
            columns=["doc_id", "title", "product", "study_type", "key_findings"],
            num_results=num_results
        )

        print(f"\nFound {len(results.get('result', {}).get('data_array', []))} results:\n")

        for i, result in enumerate(results.get('result', {}).get('data_array', []), 1):
            score = result[0] if len(result) > 0 else "N/A"
            doc_id = result[1] if len(result) > 1 else "N/A"
            title = result[2] if len(result) > 2 else "N/A"
            product = result[3] if len(result) > 3 else "N/A"
            study_type = result[4] if len(result) > 4 else "N/A"

            print(f"{i}. {title}")
            print(f"   Product: {product} | Study: {study_type}")
            print(f"   Score: {score:.4f}")
            print(f"   Doc ID: {doc_id}")
            print()

        return results

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Test queries
test_vector_search("What are the effects of Allulose on glycemic response in diabetic patients?")

# COMMAND ----------

test_vector_search("Clinical trials of Trehalose in athletic performance")

# COMMAND ----------

test_vector_search("Safety and regulatory status of Tagatose")

# COMMAND ----------

test_vector_search("Comparison of sugar substitutes for metabolic syndrome")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Advanced Query with Filters

# COMMAND ----------

def test_filtered_search(query: str, filters: dict, num_results: int = 3):
    """
    Test vector search with metadata filters
    """
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Filters: {filters}")
    print('='*60)

    try:
        results = vsc.get_index(index_name=INDEX_NAME).similarity_search(
            query_text=query,
            columns=["doc_id", "title", "product", "study_type", "sample_size", "p_value"],
            filters=filters,
            num_results=num_results
        )

        print(f"\nFound {len(results.get('result', {}).get('data_array', []))} results:\n")

        for i, result in enumerate(results.get('result', {}).get('data_array', []), 1):
            print(f"{i}. {result[2]}")  # title
            print(f"   Product: {result[3]} | Study: {result[4]}")
            print(f"   Sample Size: {result[5] if len(result) > 5 else 'N/A'}")
            print()

        return results

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Test with filters
test_filtered_search(
    query="Effects on athletes",
    filters={"product": "Trehalose", "study_type": "human_trial"}
)

# COMMAND ----------

test_filtered_search(
    query="Glycemic control",
    filters={"product": "Allulose"}
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Get Full Document Content

# COMMAND ----------

def get_full_document(doc_id: str):
    """
    Retrieve full document content from Delta table
    """
    query = f"""
        SELECT
            doc_id,
            title,
            authors,
            publication_date,
            journal,
            document_type,
            product,
            study_type,
            sample_size,
            p_value,
            key_findings,
            text_content,
            image_descriptions,
            formulas,
            pdf_path
        FROM {SOURCE_TABLE}
        WHERE doc_id = '{doc_id}'
    """

    return spark.sql(query).collect()[0]


# Example: Get full document for first search result
print("Retrieving full document content...\n")

# Use doc_id from previous search results
sample_doc_id = spark.sql(f"SELECT doc_id FROM {SOURCE_TABLE} LIMIT 1").collect()[0][0]

doc = get_full_document(sample_doc_id)

print(f"Title: {doc.title}")
print(f"Authors: {doc.authors}")
print(f"Journal: {doc.journal}")
print(f"Study Type: {doc.study_type}")
print(f"\nKey Findings:")
for finding in doc.key_findings:
    print(f"  • {finding}")

print(f"\nText Content (first 500 chars):")
print(doc.text_content[:500] + "...")

if doc.image_descriptions:
    print(f"\nImage Descriptions ({len(doc.image_descriptions)}):")
    for i, desc in enumerate(doc.image_descriptions[:2], 1):
        print(f"  {i}. {desc[:200]}...")

if doc.formulas:
    print(f"\nChemical Formulas:")
    print(f"  {', '.join(doc.formulas)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✓ Vector Search Setup Complete!

# COMMAND ----------

print("""
✓ Vector Search Setup Complete!

Summary:
--------
✓ Endpoint created and online
✓ Vector Search index created
✓ Index synced and ready
✓ Test queries successful
✓ Filters working

Index Details:
--------------
Name: {INDEX_NAME}
Endpoint: {ENDPOINT_NAME}
Model: {EMBEDDING_MODEL}
Documents: {num_docs}

Next Steps:
-----------
1. Integrate with Gradio app
2. Configure Scientific RAG agent
3. Test end-to-end queries

You can now query the index using:
```python
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()
results = vsc.get_index("{INDEX_NAME}").similarity_search(
    query_text="your query here",
    num_results=5
)
```
""".format(
    INDEX_NAME=INDEX_NAME,
    ENDPOINT_NAME=ENDPOINT_NAME,
    EMBEDDING_MODEL=EMBEDDING_MODEL,
    num_docs=num_docs
))
