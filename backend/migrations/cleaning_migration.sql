-- SQLite Migration Script: Database Cleaning Enhancement
-- Creates new tables and indexes for improved data management

-- ============================================
-- 1. Historical KPI Table (national benchmarks)
-- ============================================

CREATE TABLE IF NOT EXISTS historical_kpis (
    year INTEGER PRIMARY KEY,
    metrics JSON NOT NULL,
    source TEXT DEFAULT 'AICTE/UGC',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. Document Hash Cache (for deduplication)
-- ============================================

CREATE TABLE IF NOT EXISTS document_hash_cache (
    id TEXT PRIMARY KEY,
    batch_id TEXT,
    file_hash TEXT,
    filename TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document hash cache
CREATE INDEX IF NOT EXISTS idx_doc_hash_batch ON document_hash_cache(batch_id);
CREATE INDEX IF NOT EXISTS idx_doc_hash_hash ON document_hash_cache(file_hash);

-- ============================================
-- 3. Performance Indexes
-- ============================================

-- Batch status index for filtering
CREATE INDEX IF NOT EXISTS idx_batch_status ON batches(status);

-- Block composite index for batch + type queries
CREATE INDEX IF NOT EXISTS idx_blocks_batch_type ON blocks(batch_id, block_type);

-- Compliance flags index
CREATE INDEX IF NOT EXISTS idx_compliance_flags_batch ON compliance_flags(batch_id);

-- Approval required documents index
CREATE INDEX IF NOT EXISTS idx_required_docs_batch_cat ON approval_required_documents(batch_id, category);

-- File batch index
CREATE INDEX IF NOT EXISTS idx_files_batch ON files(batch_id);

-- ============================================
-- 4. Cleanup Views (for monitoring)
-- ============================================

-- View: Invalid batches (candidates for deletion)
CREATE VIEW IF NOT EXISTS v_invalid_batches AS
SELECT 
    b.id,
    b.status,
    b.created_at,
    json_extract(b.sufficiency_result, '$.percentage') as sufficiency_pct,
    json_extract(b.kpi_results, '$.overall_score.value') as overall_score,
    (SELECT COUNT(*) FROM blocks WHERE batch_id = b.id) as block_count
FROM batches b
WHERE 
    json_extract(b.sufficiency_result, '$.percentage') < 30
    OR json_extract(b.kpi_results, '$.overall_score.value') = 0
    OR json_extract(b.kpi_results, '$.overall_score.value') IS NULL
    OR (SELECT COUNT(*) FROM blocks WHERE batch_id = b.id) = 0;

-- View: Database statistics
CREATE VIEW IF NOT EXISTS v_db_stats AS
SELECT 
    'batches' as table_name, COUNT(*) as row_count FROM batches
UNION ALL
SELECT 'blocks', COUNT(*) FROM blocks
UNION ALL
SELECT 'files', COUNT(*) FROM files
UNION ALL
SELECT 'compliance_flags', COUNT(*) FROM compliance_flags
UNION ALL
SELECT 'historical_kpis', COUNT(*) FROM historical_kpis;

-- ============================================
-- 5. Triggers for automatic cleanup
-- ============================================

-- Trigger: Cascade delete blocks when batch is deleted
CREATE TRIGGER IF NOT EXISTS trg_delete_batch_blocks
AFTER DELETE ON batches
BEGIN
    DELETE FROM blocks WHERE batch_id = OLD.id;
    DELETE FROM files WHERE batch_id = OLD.id;
    DELETE FROM compliance_flags WHERE batch_id = OLD.id;
    DELETE FROM approval_classifications WHERE batch_id = OLD.id;
    DELETE FROM approval_required_documents WHERE batch_id = OLD.id;
    DELETE FROM document_hash_cache WHERE batch_id = OLD.id;
END;

-- ============================================
-- Done
-- ============================================
