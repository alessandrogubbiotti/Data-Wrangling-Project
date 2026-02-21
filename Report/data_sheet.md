-- Documents table
CREATE TABLE documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id TEXT UNIQUE NOT NULL,
  file_path TEXT NOT NULL,
  one_sentence_summary TEXT NOT NULL,      -- AI-generated brief summary
  paragraph_summary TEXT NOT NULL,         -- AI-generated detailed summary
  date_range_earliest TEXT,                -- Earliest date mentioned in document
  date_range_latest TEXT,                  -- Latest date mentioned in document
  category TEXT NOT NULL,                  -- Document category
  content_tags TEXT NOT NULL,              -- JSON array of content tags
  analysis_timestamp TEXT NOT NULL,        -- When analysis was performed
  input_tokens INTEGER,                    -- Claude API usage metrics
  output_tokens INTEGER,
  cache_read_tokens INTEGER,
  cost_usd REAL,                          -- Estimated API cost
  error TEXT,                             -- Error message if analysis failed
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  full_text TEXT                          -- Complete document text for search
);
CREATE INDEX idx_documents_doc_id ON documents(doc_id);
CREATE INDEX idx_documents_category ON documents(category);

-- RDF triples (relationships)
CREATE TABLE rdf_triples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id TEXT NOT NULL,
  timestamp TEXT,                         -- When the event occurred
  actor TEXT NOT NULL,                    -- Subject of the relationship
  action TEXT NOT NULL,                   -- Action/verb
  target TEXT NOT NULL,                   -- Object of the relationship
  location TEXT,                          -- Where the event occurred
  actor_likely_type TEXT,                 -- Type of actor (person, organization, etc.)
  triple_tags TEXT,                       -- JSON array of tags
  explicit_topic TEXT,                    -- Explicit subject matter
  implicit_topic TEXT,                    -- Inferred subject matter
  sequence_order INTEGER NOT NULL,        -- Order within document
  top_cluster_ids TEXT,                   -- JSON array of top 3 cluster IDs (materialized)
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);
CREATE INDEX idx_rdf_triples_doc_id ON rdf_triples(doc_id);
CREATE INDEX idx_rdf_triples_actor ON rdf_triples(actor);
CREATE INDEX idx_rdf_triples_timestamp ON rdf_triples(timestamp);
CREATE INDEX idx_top_cluster_ids ON rdf_triples(top_cluster_ids);

-- Entity aliases (deduplication)
CREATE TABLE entity_aliases (
  original_name TEXT PRIMARY KEY,
  canonical_name TEXT NOT NULL,
  reasoning TEXT,                         -- LLM explanation for the merge
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT DEFAULT 'llm_dedupe'    -- Source of the alias
);
