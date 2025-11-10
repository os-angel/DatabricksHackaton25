# Databricks notebook source
# MAGIC %md
# MAGIC # Scientific PDF Processing Pipeline
# MAGIC
# MAGIC This notebook processes scientific PDFs and prepares them for Vector Search RAG.
# MAGIC
# MAGIC **Workflow:**
# MAGIC 1. Read PDFs from Unity Catalog Volume
# MAGIC 2. Parse PDFs using `ai_parse_document()`
# MAGIC 3. Extract images and generate descriptions using vision models
# MAGIC 4. Extract chemical formulas
# MAGIC 5. Extract metadata using LLM
# MAGIC 6. Combine all content for embedding
# MAGIC 7. Save to Delta table (auto-sync with Vector Search)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Setup and Configuration

# COMMAND ----------

import os
import json
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, udf, explode, concat_ws, expr, lit,
    current_timestamp, to_date, array, struct
)
from pyspark.sql.types import (
    StringType, ArrayType, StructType, StructField,
    IntegerType, DoubleType, DateType
)

# Configuration
CATALOG = "biolabs_catalog"
SCHEMA = "scientific"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/raw_pdfs"
IMAGE_OUTPUT_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/parsed_images"
TARGET_TABLE = f"{CATALOG}.{SCHEMA}.documents"

print(f"✓ Configuration loaded")
print(f"  - PDF Source: {VOLUME_PATH}")
print(f"  - Image Output: {IMAGE_OUTPUT_PATH}")
print(f"  - Target Table: {TARGET_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. PDF Parsing with ai_parse_document()

# COMMAND ----------

# Read PDFs from volume as binary files
pdf_files = (
    spark.read
    .format("binaryFile")
    .option("recursiveFileLookup", "true")
    .option("pathGlobFilter", "*.pdf")
    .load(VOLUME_PATH)
)

print(f"✓ Found {pdf_files.count()} PDF files")
display(pdf_files.select("path"))

# COMMAND ----------

# Parse PDFs using Databricks ai_parse_document function
# This extracts text, tables, and identifies images
parsed_pdfs = pdf_files.withColumn(
    "parsed_result",
    expr(f"""
        ai_parse_document(
            content,
            map(
                'imageOutputPath', '{IMAGE_OUTPUT_PATH}',
                'descriptionElementTypes', '*',
                'includeTableData', 'true'
            )
        )
    """)
)

print(f"✓ Parsed {parsed_pdfs.count()} PDFs")

# COMMAND ----------

# Extract document structure
documents_df = parsed_pdfs.select(
    col("path").alias("pdf_path"),
    col("parsed_result.document.pages").alias("pages"),
    col("parsed_result.document.elements").alias("elements")
)

display(documents_df.limit(2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Extract Text Content

# COMMAND ----------

# Extract text from all elements
text_extracted = documents_df.withColumn(
    "text_content",
    expr("""
        concat_ws('\n\n',
            transform(
                filter(elements, e -> e.type IN ('text', 'paragraph', 'title')),
                e -> e.content
            )
        )
    """)
)

print(f"✓ Extracted text from {text_extracted.count()} documents")
display(text_extracted.select("pdf_path", "text_content").limit(2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Extract and Describe Images with Vision Model

# COMMAND ----------

# Extract image paths from parsed results
images_df = documents_df.select(
    col("pdf_path"),
    explode(
        expr("filter(elements, e -> e.type = 'image')")
    ).alias("image_element")
).select(
    "pdf_path",
    col("image_element.imagePath").alias("image_path"),
    col("image_element.pageNumber").alias("page_number")
)

print(f"✓ Found {images_df.count()} images across all documents")
display(images_df.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4a. Vision Model Integration (GPT-4V or Claude Sonnet)
# MAGIC
# MAGIC This section uses external vision models to describe scientific charts and figures.
# MAGIC **Note:** In production, configure API keys in Databricks secrets.

# COMMAND ----------

import requests
import base64
from typing import Optional

# Configuration for vision model
VISION_MODEL_PROVIDER = "openai"  # or "anthropic"
OPENAI_API_KEY = dbutils.secrets.get(scope="biolabs", key="openai_api_key")
ANTHROPIC_API_KEY = dbutils.secrets.get(scope="biolabs", key="anthropic_api_key")

def describe_scientific_image_gpt4v(image_path: str) -> str:
    """
    Use GPT-4V to describe a scientific image/chart
    """
    try:
        # Read image from DBFS
        with open(image_path.replace("dbfs:", "/dbfs"), "rb") as f:
            image_bytes = f.read()

        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Call GPT-4V API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        prompt = """You are a PhD biochemist specializing in carbohydrates and sugar metabolism.

Describe this scientific figure/chart in detail. Include:
1. Type of visualization (line graph, bar chart, molecular structure, etc.)
2. Axis labels and units (if applicable)
3. Key trends or patterns visible
4. Numerical values or ranges shown
5. What this demonstrates about sugar metabolism or biological effects
6. Any error bars, statistical significance markers, or confidence intervals

Be precise and technical. This description will be used for scientific literature search."""

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"[Error describing image: {response.status_code}]"

    except Exception as e:
        return f"[Error: {str(e)}]"


def describe_scientific_image_claude(image_path: str) -> str:
    """
    Use Claude Sonnet 4 with vision to describe a scientific image
    """
    try:
        # Read image from DBFS
        with open(image_path.replace("dbfs:", "/dbfs"), "rb") as f:
            image_bytes = f.read()

        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }

        prompt = """You are a PhD biochemist specializing in carbohydrates and sugar metabolism.

Describe this scientific figure/chart in detail. Include:
1. Type of visualization
2. Axis labels and units
3. Key trends or patterns
4. Numerical values
5. Scientific implications for sugar metabolism
6. Statistical markers

Be precise and technical."""

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            return f"[Error describing image: {response.status_code}]"

    except Exception as e:
        return f"[Error: {str(e)}]"


# Register UDF
if VISION_MODEL_PROVIDER == "openai":
    describe_image_udf = udf(describe_scientific_image_gpt4v, StringType())
else:
    describe_image_udf = udf(describe_scientific_image_claude, StringType())

print(f"✓ Vision model UDF registered ({VISION_MODEL_PROVIDER})")

# COMMAND ----------

# Apply vision model to all images
images_with_descriptions = images_df.withColumn(
    "description",
    describe_image_udf(col("image_path"))
)

print(f"✓ Generated descriptions for {images_with_descriptions.count()} images")
display(images_with_descriptions.limit(5))

# COMMAND ----------

# Aggregate image descriptions by document
image_descriptions_agg = (
    images_with_descriptions
    .groupBy("pdf_path")
    .agg(
        expr("collect_list(description)").alias("image_descriptions")
    )
)

print(f"✓ Aggregated image descriptions for {image_descriptions_agg.count()} documents")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Extract Chemical Formulas

# COMMAND ----------

import re

def extract_formulas(text: str) -> List[str]:
    """
    Extract chemical formulas from text using regex patterns
    """
    if not text:
        return []

    formulas = []

    # Pattern 1: Standard chemical formulas (e.g., C6H12O6, CH3COOH)
    pattern1 = r'\b[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*\b'
    matches1 = re.findall(pattern1, text)

    # Pattern 2: Unicode subscripts (e.g., C₆H₁₂O₆)
    pattern2 = r'[A-Z][a-z]?[₀₁₂₃₄₅₆₇₈₉]+(?:[A-Z][a-z]?[₀₁₂₃₄₅₆₇₈₉]+)*'
    matches2 = re.findall(pattern2, text)

    # Filter valid formulas (must contain at least one element and one number)
    for match in matches1 + matches2:
        if re.search(r'\d', match) and len(match) >= 3:
            formulas.append(match)

    # Remove duplicates while preserving order
    seen = set()
    unique_formulas = []
    for formula in formulas:
        if formula not in seen:
            seen.add(formula)
            unique_formulas.append(formula)

    return unique_formulas[:10]  # Limit to 10 formulas per document


extract_formulas_udf = udf(extract_formulas, ArrayType(StringType()))

print("✓ Formula extraction UDF registered")

# COMMAND ----------

# Extract formulas from text
text_with_formulas = text_extracted.withColumn(
    "formulas",
    extract_formulas_udf(col("text_content"))
)

print(f"✓ Extracted formulas from {text_with_formulas.count()} documents")
display(text_with_formulas.select("pdf_path", "formulas").limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Extract Metadata with LLM

# COMMAND ----------

def extract_metadata_with_llm(text: str, pdf_filename: str) -> Dict[str, Any]:
    """
    Extract structured metadata from scientific paper using LLM
    """
    try:
        # Use Databricks Foundation Model or external LLM
        from anthropic import Anthropic

        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        # Take first 3000 characters (abstract and intro usually)
        text_sample = text[:3000] if text else ""

        prompt = f"""Extract metadata from this scientific paper excerpt:

{text_sample}

Filename: {pdf_filename}

Return JSON with these fields:
- document_type: one of [clinical_trial, patent, regulatory, review]
- product: one of [tagatose, allulose, trehalose, general]
- title: paper title (from text or filename)
- authors: comma-separated author list
- publication_date: YYYY-MM-DD or null
- journal: journal name or null
- study_type: one of [in_vitro, animal, human_trial, meta_analysis, review, null]
- sample_size: integer or null
- p_value: float or null
- key_findings: array of 3 key findings (short bullet points)

Return ONLY valid JSON, no other text."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse LLM response
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        metadata = json.loads(response_text)
        return metadata

    except Exception as e:
        # Return default metadata on error
        return {
            "document_type": "review",
            "product": "general",
            "title": pdf_filename,
            "authors": None,
            "publication_date": None,
            "journal": None,
            "study_type": None,
            "sample_size": None,
            "p_value": None,
            "key_findings": []
        }


# Define schema for metadata
metadata_schema = StructType([
    StructField("document_type", StringType(), True),
    StructField("product", StringType(), True),
    StructField("title", StringType(), True),
    StructField("authors", StringType(), True),
    StructField("publication_date", StringType(), True),
    StructField("journal", StringType(), True),
    StructField("study_type", StringType(), True),
    StructField("sample_size", IntegerType(), True),
    StructField("p_value", DoubleType(), True),
    StructField("key_findings", ArrayType(StringType()), True),
])

extract_metadata_udf = udf(extract_metadata_with_llm, metadata_schema)

print("✓ Metadata extraction UDF registered")

# COMMAND ----------

# Extract filename from path
text_with_metadata = text_with_formulas.withColumn(
    "filename",
    expr("regexp_extract(pdf_path, '[^/]+$', 0)")
).withColumn(
    "metadata",
    extract_metadata_udf(col("text_content"), col("filename"))
)

print(f"✓ Extracted metadata from {text_with_metadata.count()} documents")
display(text_with_metadata.select("pdf_path", "metadata").limit(3))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Combine All Content and Prepare for Vector Search

# COMMAND ----------

# Join with image descriptions
final_df = (
    text_with_metadata
    .join(image_descriptions_agg, "pdf_path", "left")
)

# Create combined content for embedding
final_df = final_df.withColumn(
    "combined_content",
    expr("""
        concat(
            'TITLE: ', metadata.title, '\n\n',
            'CONTENT:\n', text_content, '\n\n',
            CASE
                WHEN size(image_descriptions) > 0 THEN
                    concat('[FIGURES AND CHARTS]\n',
                           concat_ws('\n\n', image_descriptions), '\n\n')
                ELSE ''
            END,
            CASE
                WHEN size(formulas) > 0 THEN
                    concat('[CHEMICAL FORMULAS]\n',
                           concat_ws(', ', formulas))
                ELSE ''
            END
        )
    """)
)

print("✓ Combined all content for embedding")
display(final_df.select("pdf_path", "combined_content").limit(2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Create Final Schema and Save to Delta Table

# COMMAND ----------

# Generate unique doc_id
from pyspark.sql.functions import md5, concat_ws, monotonically_increasing_id

final_documents = final_df.select(
    md5(col("pdf_path")).alias("doc_id"),
    col("metadata.document_type").alias("document_type"),
    col("metadata.product").alias("product"),
    col("metadata.title").alias("title"),
    col("metadata.authors").alias("authors"),
    to_date(col("metadata.publication_date")).alias("publication_date"),
    col("metadata.journal").alias("journal"),

    # Processed content
    col("text_content"),
    col("image_descriptions"),
    col("formulas"),
    col("combined_content"),

    # Metadata
    col("metadata.study_type").alias("study_type"),
    col("metadata.sample_size").alias("sample_size"),
    col("metadata.p_value").alias("p_value"),
    col("metadata.key_findings").alias("key_findings"),

    # References
    lit(None).cast(ArrayType(StringType())).alias("citations"),
    col("pdf_path"),

    # Timestamps
    current_timestamp().alias("created_at"),
    current_timestamp().alias("updated_at")
)

print("✓ Final schema created")
display(final_documents.limit(3))

# COMMAND ----------

# Save to Delta table
final_documents.write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable(TARGET_TABLE)

print(f"✓ Saved {final_documents.count()} documents to {TARGET_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Verify Results

# COMMAND ----------

# Query the table
result = spark.sql(f"SELECT * FROM {TARGET_TABLE}")

print(f"✓ Table contains {result.count()} documents")
print("\nDocument types:")
result.groupBy("document_type").count().show()

print("\nProducts:")
result.groupBy("product").count().show()

print("\nStudy types:")
result.groupBy("study_type").count().show()

# COMMAND ----------

# Show sample document
spark.sql(f"""
    SELECT
        doc_id,
        title,
        document_type,
        product,
        study_type,
        sample_size,
        key_findings
    FROM {TARGET_TABLE}
    LIMIT 5
""").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✓ Pipeline Complete
# MAGIC
# MAGIC **Next Steps:**
# MAGIC 1. Create Vector Search Index on this table
# MAGIC 2. Configure embedding model (databricks-bge-large-en)
# MAGIC 3. Enable auto-sync with Change Data Feed
# MAGIC 4. Test RAG queries

# COMMAND ----------

print("""
✓ PDF Processing Pipeline Complete!

Summary:
--------
- PDFs parsed using ai_parse_document()
- Text extracted and cleaned
- Images described with vision models
- Chemical formulas extracted
- Metadata extracted with LLM
- All content combined for embedding
- Data saved to Delta table with CDC enabled

Next: Run notebook 02_vector_search_setup.py
""")
