# Haiku Execution Tasklist - Skill-Split Gap Closure
**Date**: 2026-02-05
**Status**: READY FOR EXECUTION
**Total Estimated Time**: ~14 hours (parallelizable)

---

## Overview

This tasklist consolidates all remaining gaps from:
- FINAL_GAP_CLOSURE_TASKS.md (6 gaps)
- Phase 11: SkillComposer API (docs/plans/phase-11-skillcomposer.md)
- Phase 14: Vector Search (docs/plans/phase-14-vector-search.md)

**Execution Strategy**: Parallel Haiku agents with dependencies tracked

---

## Priority Tiers

### TIER 1: Critical Path (Must Complete First)
- Schema migration documentation
- Phase 11 SkillComposer implementation
- Documentation updates

### TIER 2: Enhanced Capabilities
- Phase 14 Vector Search implementation
- Performance optimization

### TIER 3: User Verification Required
- Manual round-trip testing
- Schema migration application

---

## TIER 1: Critical Path

### Block A: Immediate Setup (30 min)

**Task 1.1: Document Schema Migration**
- **File**: `migrations/SCHEMA_MIGRATION_GUIDE.md`
- **Purpose**: Clear instructions for user to apply schema migration
- **Time**: 10 min
- **Dependencies**: None
- **Deliverable**:
  ```markdown
  # Schema Migration Guide

  ## What This Fixes
  - Enables config.json and script file types
  - Removes "files_type_check" constraint errors

  ## Steps
  1. Open: https://supabase.com/dashboard/project/dnqbnwalycyoynbcpbpz/editor
  2. Click: SQL Editor → New Query
  3. Copy SQL from: migrations/add_config_script_types.sql
  4. Paste and Click: Run
  5. Verify: No errors in output

  ## Verification
  ```bash
  # Should succeed after migration
  ./skill_split.py ingest ~/.claude/skills/agent-browser/config.json
  ```

  ## Rollback (if needed)
  ```sql
  -- See migrations/rollback_config_script_types.sql
  ```
  ```

**Task 1.2: Document Round-Trip Test**
- **File**: `test/MANUAL_ROUNDTRIP_TEST.md`
- **Purpose**: Clear instructions for user to verify byte-perfect retrieval
- **Time**: 15 min
- **Dependencies**: None
- **Deliverable**:
  ```markdown
  # Manual Round-Trip Test

  ## Purpose
  Verify that files retrieved from Supabase are byte-perfect copies

  ## Test Steps

  ### Step 1: Pick Test File
  ```bash
  python3 -c "
  from dotenv import load_dotenv
  import os
  load_dotenv()
  from core.supabase_store import SupabaseStore

  store = SupabaseStore(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
  result = store.client.table('files').select('id,name,storage_path').eq('type', 'skill').limit(1).execute()
  if result.data:
      print(f\"File ID: {result.data[0]['id']}\")
      print(f\"Name: {result.data[0]['name']}\")
      print(f\"Path: {result.data[0]['storage_path']}\")
  "
  ```

  ### Step 2: Checkout File
  ```bash
  ./skill_split.py checkout <file-id> /tmp/skill-test/
  ```

  ### Step 3: Verify Byte-Perfect Match
  ```bash
  diff /tmp/skill-test/<filename> <original-path>
  # Should output: NOTHING (perfect match)
  ```

  ### Step 4: Check Hash
  ```bash
  ./skill_split.py verify <original-path>
  # Should output: Valid ✓
  ```

  ## Success Criteria
  - diff outputs nothing
  - verify shows Valid ✓
  - File is identical byte-for-byte
  ```

**Task 1.3: Update Documentation**
- **File**: `CLAUDE.md`, `README.md`, `HANDOFF.md`
- **Purpose**: Reflect archival strategy and current state
- **Time**: 5 min
- **Dependencies**: None
- **Updates**:
  - CLAUDE.md: Add archival mode section (done)
  - README.md: Update stats (2,757 files in Supabase)
  - HANDOFF.md: Mark as archival strategy confirmed

---

### Block B: Phase 11 - SkillComposer Implementation (7.5 hours)

> **Note**: These tasks follow docs/plans/phase-11-skillcomposer.md exactly

#### Stage 1: Core Data Models (45 min)

**Task 2.1: Create ComposedSkill Model**
- **File**: `models.py` (modify lines 50-80)
- **Purpose**: Data structure for composed skills
- **Time**: 20 min
- **Dependencies**: None
- **Code**:
  ```python
  @dataclass
  class ComposedSkill:
      """Represents a skill composed from multiple sections."""
      section_ids: List[int]
      sections: Dict[int, Section]
      output_path: str
      frontmatter: str
      title: str
      description: str
      composed_hash: str = ""

      def to_dict(self) -> Dict[str, Any]:
          """Serialize to dictionary."""
          return {
              "section_ids": self.section_ids,
              "output_path": self.output_path,
              "frontmatter": self.frontmatter,
              "title": self.title,
              "description": self.description,
              "composed_hash": self.composed_hash
          }
  ```

**Task 2.2: Add CompositionContext Model**
- **File**: `models.py` (append)
- **Purpose**: Track composition metadata
- **Time**: 15 min
- **Dependencies**: Task 2.1
- **Code**:
  ```python
  @dataclass
  class CompositionContext:
      """Metadata for skill composition process."""
      source_files: List[str]
      source_sections: int
      target_format: FileFormat
      created_at: str
      validation_status: str = "pending"
      errors: List[str] = field(default_factory=list)
  ```

**Task 2.3: Write ComposedSkill Tests**
- **File**: `test/test_models.py` (create)
- **Purpose**: Test model serialization
- **Time**: 10 min
- **Dependencies**: Task 2.1, 2.2
- **Tests**: 5 tests for ComposedSkill and CompositionContext

---

#### Stage 2: SkillComposer Core (2 hours)

**Task 3.1: Create SkillComposer Class**
- **File**: `core/skill_composer.py` (create, lines 1-150)
- **Purpose**: Main composition orchestrator
- **Time**: 45 min
- **Dependencies**: Task 2.1, 2.2
- **Key Methods**:
  ```python
  class SkillComposer:
      def __init__(self, db_store: DatabaseStore):
          self.db_store = db_store
          self.query_api = QueryAPI(db_store)

      def compose_from_sections(
          self,
          section_ids: List[int],
          output_path: str,
          title: str = "",
          description: str = ""
      ) -> ComposedSkill:
          """Compose new skill from section IDs."""
          # 1. Retrieve sections
          # 2. Rebuild hierarchy
          # 3. Generate frontmatter
          # 4. Create ComposedSkill
          pass
  ```

**Task 3.2: Implement Section Retrieval**
- **File**: `core/skill_composer.py` (lines 50-100)
- **Purpose**: Load sections from database
- **Time**: 30 min
- **Dependencies**: Task 3.1
- **Implementation**:
  ```python
  def _retrieve_sections(self, section_ids: List[int]) -> Dict[int, Section]:
      """Retrieve sections by IDs from database."""
      sections = {}
      for section_id in section_ids:
          section = self.query_api.get_section(section_id)
          if not section:
              raise ValueError(f"Section {section_id} not found")
          sections[section_id] = section
      return sections
  ```

**Task 3.3: Implement Hierarchy Rebuild**
- **File**: `core/skill_composer.py` (lines 100-200)
- **Purpose**: Reconstruct parent-child relationships
- **Time**: 45 min
- **Dependencies**: Task 3.2
- **Implementation**:
  ```python
  def _rebuild_hierarchy(self, sections: Dict[int, Section]) -> List[Section]:
      """Build section tree from flat dictionary."""
      # Sort by start line
      sorted_sections = sorted(sections.values(), key=lambda s: s.start_line)

      # Build parent-child relationships
      root_sections = []
      for section in sorted_sections:
          if section.level == 1:
              root_sections.append(section)
          # ... attach children

      return root_sections
  ```

---

#### Stage 3: Frontmatter Generation (1.5 hours)

**Task 4.1: Create FrontmatterGenerator**
- **File**: `core/frontmatter_generator.py` (create, 200 lines)
- **Purpose**: Auto-generate YAML metadata
- **Time**: 60 min
- **Dependencies**: None
- **Key Methods**:
  ```python
  class FrontmatterGenerator:
      def generate(
          self,
          title: str,
          description: str,
          sections: List[Section],
          context: CompositionContext
      ) -> str:
          """Generate YAML frontmatter."""
          metadata = {
              "name": self._slugify(title),
              "description": description,
              "sections": len(sections),
              "composed_from": context.source_files,
              "created_at": context.created_at
          }
          return yaml.dump(metadata, sort_keys=False)
  ```

**Task 4.2: Add Metadata Enrichment**
- **File**: `core/frontmatter_generator.py` (lines 100-150)
- **Purpose**: Extract tags, dependencies from sections
- **Time**: 30 min
- **Dependencies**: Task 4.1
- **Features**:
  - Extract common tags across sections
  - Identify tool dependencies
  - Detect file types involved

---

#### Stage 4: Validation (1 hour)

**Task 5.1: Create SkillValidator**
- **File**: `handlers/skill_validator.py` (create, 180 lines)
- **Purpose**: Validate composed skill structure
- **Time**: 45 min
- **Dependencies**: Task 3.1
- **Methods**:
  ```python
  class SkillValidator:
      def validate_structure(self, sections: List[Section]) -> List[str]:
          """Check hierarchy is valid."""
          errors = []
          # Check level progression
          # Check no orphaned sections
          # Check heading consistency
          return errors

      def validate_content(self, sections: List[Section]) -> List[str]:
          """Check content requirements."""
          errors = []
          # Check for empty sections
          # Check code block closure
          # Check frontmatter presence
          return errors
  ```

**Task 5.2: Write Validator Tests**
- **File**: `test/test_skill_validator.py` (create, 250 lines)
- **Purpose**: Test validation logic
- **Time**: 15 min
- **Dependencies**: Task 5.1
- **Tests**: 12 tests covering structure, content, metadata validation

---

#### Stage 5: Output & Integration (1.5 hours)

**Task 6.1: Implement write_to_filesystem()**
- **File**: `core/skill_composer.py` (lines 250-320)
- **Purpose**: Save composed skill to disk
- **Time**: 30 min
- **Dependencies**: Task 3.1, 4.1
- **Implementation**:
  ```python
  def write_to_filesystem(self, composed: ComposedSkill) -> str:
      """Write composed skill to file."""
      # Build content: frontmatter + sections
      content = f"---\n{composed.frontmatter}---\n\n"

      # Use Recomposer to build sections
      recomposer = Recomposer()
      sections_content = recomposer._build_sections_content(
          list(composed.sections.values())
      )
      content += sections_content

      # Write file
      Path(composed.output_path).write_text(content, encoding='utf-8')

      # Compute hash
      composed.composed_hash = compute_file_hash(composed.output_path)
      return composed.composed_hash
  ```

**Task 6.2: Implement upload_to_supabase()**
- **File**: `core/skill_composer.py` (lines 320-380)
- **Purpose**: Push composed skill to Supabase
- **Time**: 30 min
- **Dependencies**: Task 6.1
- **Implementation**:
  ```python
  def upload_to_supabase(
      self,
      composed: ComposedSkill,
      supabase_store: SupabaseStore
  ) -> str:
      """Upload composed skill to Supabase."""
      # Parse composed file
      parser = Parser()
      detector = FormatDetector()

      with open(composed.output_path, 'r') as f:
          content = f.read()

      file_type, file_format = detector.detect(composed.output_path, content)
      doc = parser.parse(composed.output_path, content, file_type, file_format)

      # Store to Supabase
      file_id = supabase_store.store_file(
          storage_path=composed.output_path,
          name=Path(composed.output_path).name,
          doc=doc,
          content_hash=composed.composed_hash
      )

      return file_id
  ```

**Task 6.3: Add CLI Commands**
- **File**: `skill_split.py` (lines 400-500)
- **Purpose**: CLI interface for composition
- **Time**: 30 min
- **Dependencies**: Task 6.1, 6.2
- **Commands**:
  ```python
  @cli.command()
  @click.option('--sections', required=True, help='Comma-separated section IDs')
  @click.option('--output', required=True, help='Output file path')
  @click.option('--title', default='', help='Skill title')
  @click.option('--description', default='', help='Skill description')
  @click.option('--upload', is_flag=True, help='Upload to Supabase')
  def compose(sections, output, title, description, upload):
      """Compose new skill from section IDs."""
      section_ids = [int(sid) for sid in sections.split(',')]

      # Compose skill
      composer = SkillComposer(db_store)
      composed = composer.compose_from_sections(
          section_ids, output, title, description
      )

      # Write to filesystem
      hash_val = composer.write_to_filesystem(composed)
      click.echo(f"Composed skill written: {output}")
      click.echo(f"Hash: {hash_val}")

      # Upload if requested
      if upload:
          file_id = composer.upload_to_supabase(composed, supabase_store)
          click.echo(f"Uploaded to Supabase: {file_id}")
  ```

---

#### Stage 6: Testing & Documentation (1 hour)

**Task 7.1: Write SkillComposer Tests**
- **File**: `test/test_skill_composer.py` (create, 400 lines)
- **Purpose**: Test composition workflow
- **Time**: 30 min
- **Dependencies**: All previous tasks
- **Tests**: 18 tests covering:
  - Section retrieval
  - Hierarchy rebuild
  - Frontmatter generation
  - File writing
  - Supabase upload
  - Error handling

**Task 7.2: Write Integration Tests**
- **File**: `test/test_composer_integration.py` (create, 300 lines)
- **Purpose**: End-to-end composition tests
- **Time**: 20 min
- **Dependencies**: Task 7.1
- **Tests**: 8 integration tests

**Task 7.3: Update Documentation**
- **File**: `COMPONENT_COMPOSITION.md` (create)
- **Purpose**: Guide for using composition API
- **Time**: 10 min
- **Dependencies**: All previous tasks
- **Content**:
  ```markdown
  # Skill Composition Guide

  ## Overview
  Build custom skills from existing sections

  ## Basic Usage
  ```bash
  # Compose from specific sections
  ./skill_split.py compose \
    --sections 101,205,310 \
    --output ~/.claude/skills/custom-auth.md \
    --title "Custom Auth Patterns" \
    --description "Selected authentication patterns"

  # Upload to Supabase
  ./skill_split.py compose \
    --sections 101,205,310 \
    --output ~/.claude/skills/custom-auth.md \
    --upload
  ```

  ## Programmatic Usage
  ```python
  from core.skill_composer import SkillComposer
  from core.database import DatabaseStore

  db = DatabaseStore("~/.claude/databases/skill-split.db")
  composer = SkillComposer(db)

  composed = composer.compose_from_sections(
      section_ids=[101, 205, 310],
      output_path="~/.claude/skills/custom.md",
      title="Custom Skill",
      description="My custom composition"
  )

  hash_val = composer.write_to_filesystem(composed)
  ```
  ```

---

## TIER 2: Enhanced Capabilities

### Block C: Phase 14 - Vector Search (6.5 hours)

> **Note**: These tasks follow docs/plans/phase-14-vector-search.md exactly

#### Stage 1: Database Schema (45 min)

**Task 8.1: Enable pgvector Extension**
- **File**: `migrations/enable_pgvector.sql` (create)
- **Purpose**: Enable PostgreSQL pgvector
- **Time**: 5 min
- **Dependencies**: None
- **SQL**:
  ```sql
  -- Enable pgvector extension
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

**Task 8.2: Create Embeddings Table**
- **File**: `migrations/create_embeddings_table.sql` (create)
- **Purpose**: Store section embeddings
- **Time**: 20 min
- **Dependencies**: Task 8.1
- **SQL**:
  ```sql
  CREATE TABLE section_embeddings (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
      embedding VECTOR(1536),  -- text-embedding-3-small dimensions
      model_name TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(section_id, model_name)
  );

  -- Index for fast vector similarity search
  CREATE INDEX section_embeddings_vector_idx
  ON section_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
  ```

**Task 8.3: Add Embedding Metadata**
- **File**: `migrations/add_embedding_metadata.sql` (create)
- **Purpose**: Track embedding generation
- **Time**: 20 min
- **Dependencies**: Task 8.2
- **SQL**:
  ```sql
  CREATE TABLE embedding_metadata (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      total_sections INTEGER,
      embedded_sections INTEGER,
      last_batch_at TIMESTAMP,
      total_tokens_used INTEGER,
      estimated_cost_usd DECIMAL(10, 4)
  );
  ```

---

#### Stage 2: Embedding Service (90 min)

**Task 9.1: Create EmbeddingService Class**
- **File**: `core/embedding_service.py` (create, 300 lines)
- **Purpose**: Generate and cache embeddings
- **Time**: 45 min
- **Dependencies**: Task 8.2
- **Key Methods**:
  ```python
  class EmbeddingService:
      def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
          self.api_key = api_key
          self.model = model
          self.dimensions = 1536

      def generate_embedding(self, text: str) -> List[float]:
          """Generate embedding for text."""
          # Call OpenAI API
          # Return embedding vector
          pass

      def batch_generate(self, texts: List[str]) -> List[List[float]]:
          """Generate embeddings in batch (up to 100)."""
          # Batch API call for efficiency
          pass
  ```

**Task 9.2: Implement Token-Efficient Caching**
- **File**: `core/embedding_service.py` (lines 150-250)
- **Purpose**: Avoid re-embedding unchanged sections
- **Time**: 30 min
- **Dependencies**: Task 9.1
- **Implementation**:
  ```python
  def get_or_generate_embedding(
      self,
      section_id: int,
      content: str,
      content_hash: str
  ) -> List[float]:
      """Get cached embedding or generate new one."""
      # Check if embedding exists for this content hash
      # If exists and hash matches, return cached
      # If changed or missing, generate new
      pass
  ```

**Task 9.3: Write Embedding Tests**
- **File**: `test/test_embedding_service.py` (create, 200 lines)
- **Purpose**: Test embedding generation
- **Time**: 15 min
- **Dependencies**: Task 9.1, 9.2
- **Tests**: 10 tests for embedding service

---

#### Stage 3: Hybrid Search API (60 min)

**Task 10.1: Design Hybrid Search Scoring**
- **File**: `core/hybrid_search.py` (create, lines 1-100)
- **Purpose**: Combine vector + text rankings
- **Time**: 20 min
- **Dependencies**: None
- **Algorithm**:
  ```python
  def hybrid_score(
      vector_similarity: float,
      text_score: float,
      vector_weight: float = 0.7
  ) -> float:
      """Combine vector and text scores."""
      return (vector_weight * vector_similarity) + \
             ((1 - vector_weight) * text_score)
  ```

**Task 10.2: Implement Vector Search Query**
- **File**: `core/hybrid_search.py` (lines 100-200)
- **Purpose**: Query by embedding similarity
- **Time**: 20 min
- **Dependencies**: Task 9.1, 10.1
- **Implementation**:
  ```python
  def vector_search(
      self,
      query_embedding: List[float],
      limit: int = 10
  ) -> List[Tuple[int, float]]:
      """Search sections by vector similarity."""
      # Supabase RPC call
      result = self.supabase.rpc(
          'match_sections',
          {
              'query_embedding': query_embedding,
              'match_threshold': 0.7,
              'match_count': limit
          }
      ).execute()

      return [(row['section_id'], row['similarity']) for row in result.data]
  ```

**Task 10.3: Implement Combined Search**
- **File**: `core/hybrid_search.py` (lines 200-300)
- **Purpose**: Merge vector + text results
- **Time**: 20 min
- **Dependencies**: Task 10.2
- **Implementation**:
  ```python
  def hybrid_search(
      self,
      query: str,
      limit: int = 10,
      vector_weight: float = 0.7
  ) -> List[Tuple[int, float]]:
      """Search using both vector and text."""
      # Generate query embedding
      query_emb = self.embedding_service.generate_embedding(query)

      # Get vector results
      vector_results = self.vector_search(query_emb, limit * 2)

      # Get text results
      text_results = self.text_search(query, limit * 2)

      # Merge and rank
      combined = self._merge_rankings(
          vector_results, text_results, vector_weight
      )

      return combined[:limit]
  ```

---

#### Stage 4: Integration (45 min)

**Task 11.1: Integrate into SupabaseStore**
- **File**: `core/supabase_store.py` (modify lines 100-150)
- **Purpose**: Auto-generate embeddings on store
- **Time**: 20 min
- **Dependencies**: Task 9.1
- **Modification**:
  ```python
  def store_file(self, ...):
      # Existing store logic
      file_id = ...

      # Generate embeddings for sections
      if os.getenv('ENABLE_EMBEDDINGS', 'false') == 'true':
          self._generate_section_embeddings(file_id, doc.sections)

      return file_id
  ```

**Task 11.2: Update CLI Commands**
- **File**: `skill_split.py` (lines 550-650)
- **Purpose**: Add vector search commands
- **Time**: 20 min
- **Dependencies**: Task 10.3
- **Commands**:
  ```python
  @cli.command()
  @click.argument('query')
  @click.option('--limit', default=10, help='Max results')
  @click.option('--vector-weight', default=0.7, help='Vector score weight')
  def search_semantic(query, limit, vector_weight):
      """Search sections using semantic similarity."""
      hybrid = HybridSearch(supabase_store, embedding_service)
      results = hybrid.hybrid_search(query, limit, vector_weight)

      for section_id, score in results:
          section = query_api.get_section(section_id)
          click.echo(f"[{score:.2f}] {section.title} (ID: {section_id})")
  ```

**Task 11.3: Write Integration Tests**
- **File**: `test/test_vector_search_integration.py` (create, 250 lines)
- **Purpose**: Test end-to-end vector search
- **Time**: 5 min
- **Dependencies**: All Stage 3-4 tasks
- **Tests**: 8 integration tests

---

#### Stage 5: Performance & Migration (60 min)

**Task 12.1: Add Performance Metrics**
- **File**: `core/hybrid_search.py` (lines 300-350)
- **Purpose**: Track search latency and accuracy
- **Time**: 20 min
- **Dependencies**: Task 10.3
- **Metrics**:
  - Query latency (ms)
  - Embedding generation time
  - Results returned
  - Cache hit rate

**Task 12.2: Create Migration Script**
- **File**: `scripts/generate_embeddings.py` (create, 200 lines)
- **Purpose**: Batch generate embeddings for existing sections
- **Time**: 30 min
- **Dependencies**: Task 9.1
- **Script**:
  ```python
  #!/usr/bin/env python3
  """Generate embeddings for all existing sections."""

  def main():
      # Load all sections from Supabase
      # Batch into groups of 100
      # Generate embeddings
      # Store to section_embeddings table
      # Track progress and cost
      pass
  ```

**Task 12.3: Optimize Query Performance**
- **File**: `migrations/optimize_vector_search.sql` (create)
- **Purpose**: Add indexes for fast search
- **Time**: 10 min
- **Dependencies**: Task 8.2
- **SQL**:
  ```sql
  -- Improve vector search performance
  SET ivfflat.probes = 10;

  -- Add composite index for hybrid search
  CREATE INDEX sections_content_idx ON sections USING GIN (to_tsvector('english', content));
  ```

---

#### Stage 6: Testing & Documentation (45 min)

**Task 13.1: Write Vector Search Tests**
- **File**: `test/test_vector_search.py` (create, 300 lines)
- **Purpose**: Comprehensive vector search testing
- **Time**: 20 min
- **Dependencies**: All Stage 2-5 tasks
- **Tests**: 15 tests covering:
  - Embedding generation
  - Vector similarity search
  - Hybrid ranking
  - Performance metrics

**Task 13.2: Performance Benchmarks**
- **File**: `benchmarks/vector_search_benchmark.py` (create, 150 lines)
- **Purpose**: Measure search quality improvements
- **Time**: 15 min
- **Dependencies**: Task 13.1
- **Benchmarks**:
  - Search latency
  - Relevance scores
  - Cache effectiveness

**Task 13.3: Document Costs & Usage**
- **File**: `VECTOR_SEARCH_GUIDE.md` (create)
- **Purpose**: Guide for using vector search
- **Time**: 10 min
- **Dependencies**: All previous tasks
- **Content**:
  ```markdown
  # Vector Search Guide

  ## Cost Estimates
  - Initial embedding: ~$0.08 for 19,207 sections
  - Ongoing: ~$0.001/month for new files
  - Per query: ~$0.0001

  ## Usage
  ```bash
  # Enable embeddings
  export ENABLE_EMBEDDINGS=true
  export OPENAI_API_KEY=sk-...

  # Search semantically
  ./skill_split.py search-semantic "authentication patterns"

  # Adjust vector weight (0.0 = pure text, 1.0 = pure vector)
  ./skill_split.py search-semantic "browser automation" --vector-weight 0.8
  ```

  ## Batch Migration
  ```bash
  # Generate embeddings for all existing sections
  python3 scripts/generate_embeddings.py
  ```
  ```

---

#### Stage 7: Production Deployment (30 min)

**Task 14.1: Cost Analysis**
- **File**: `docs/VECTOR_SEARCH_COSTS.md` (create)
- **Purpose**: Detailed cost breakdown
- **Time**: 10 min
- **Dependencies**: None
- **Analysis**:
  - One-time: $0.08 (19,207 sections × 100 tokens avg × $0.00002/1K)
  - Monthly: $0.001 (50 new sections × 100 tokens)
  - Query: $0.0001 per semantic search

**Task 14.2: Deployment Checklist**
- **File**: `DEPLOYMENT_CHECKLIST.md` (update)
- **Purpose**: Add vector search steps
- **Time**: 10 min
- **Dependencies**: All previous tasks
- **Checklist**:
  - [ ] Apply pgvector migration
  - [ ] Create embeddings table
  - [ ] Set OPENAI_API_KEY env var
  - [ ] Run batch embedding script
  - [ ] Test semantic search
  - [ ] Monitor costs

**Task 14.3: Monitoring Setup**
- **File**: `scripts/monitor_embeddings.py` (create, 100 lines)
- **Purpose**: Track embedding usage and costs
- **Time**: 10 min
- **Dependencies**: Task 8.3
- **Monitoring**:
  - Embedded sections count
  - Total tokens used
  - Estimated cost
  - Failed embeddings

---

## TIER 3: User Verification

### Block D: Manual Testing (User Action Required)

**Task 15.1: Apply Schema Migration**
- **Guide**: See `migrations/SCHEMA_MIGRATION_GUIDE.md` (Task 1.1)
- **User Action**: Apply SQL in Supabase dashboard
- **Time**: 5 min
- **Verification**: Ingest config.json file successfully

**Task 15.2: Run Round-Trip Test**
- **Guide**: See `test/MANUAL_ROUNDTRIP_TEST.md` (Task 1.2)
- **User Action**: Execute test steps manually
- **Time**: 10 min
- **Verification**: Byte-perfect diff output

**Task 15.3: Test Custom Skill Composition**
- **Guide**: See `COMPONENT_COMPOSITION.md` (Task 7.3)
- **User Action**: Compose a test skill
- **Time**: 10 min
- **Commands**:
  ```bash
  # Find interesting sections
  ./skill_split.py search "authentication" --db supabase

  # Compose custom skill
  ./skill_split.py compose \
    --sections <ids> \
    --output /tmp/test-composition.md \
    --title "Test Composition"

  # Verify it works
  ./skill_split.py validate /tmp/test-composition.md
  ```

---

## Execution Strategy

### Parallel Execution Blocks

**Wave 1 (No Dependencies)**: 30 min
- Task 1.1 (Schema migration guide)
- Task 1.2 (Round-trip test guide)
- Task 1.3 (Documentation updates)
- Task 2.1 (ComposedSkill model)
- Task 2.2 (CompositionContext model)

**Wave 2 (Depends on Wave 1)**: 1.5 hours
- Task 2.3 (Model tests) → depends on 2.1, 2.2
- Task 3.1 (SkillComposer class) → depends on 2.1, 2.2
- Task 8.1 (pgvector SQL) → independent
- Task 8.2 (Embeddings table) → depends on 8.1

**Wave 3 (Depends on Wave 2)**: 2 hours
- Task 3.2 (Section retrieval) → depends on 3.1
- Task 3.3 (Hierarchy rebuild) → depends on 3.2
- Task 4.1 (Frontmatter generator) → independent
- Task 8.3 (Embedding metadata) → depends on 8.2
- Task 9.1 (Embedding service) → depends on 8.2

**Wave 4 (Depends on Wave 3)**: 2 hours
- Task 4.2 (Metadata enrichment) → depends on 4.1
- Task 5.1 (SkillValidator) → depends on 3.1
- Task 9.2 (Embedding cache) → depends on 9.1
- Task 9.3 (Embedding tests) → depends on 9.1, 9.2
- Task 10.1 (Hybrid scoring) → independent

**Wave 5 (Depends on Wave 4)**: 2 hours
- Task 5.2 (Validator tests) → depends on 5.1
- Task 6.1 (write_to_filesystem) → depends on 3.1, 4.1
- Task 10.2 (Vector search) → depends on 9.1, 10.1
- Task 10.3 (Combined search) → depends on 10.2

**Wave 6 (Depends on Wave 5)**: 1.5 hours
- Task 6.2 (upload_to_supabase) → depends on 6.1
- Task 6.3 (CLI commands) → depends on 6.1, 6.2
- Task 11.1 (SupabaseStore integration) → depends on 9.1
- Task 11.2 (CLI vector commands) → depends on 10.3

**Wave 7 (Final Integration)**: 2 hours
- Task 7.1 (Composer tests) → depends on all Stage 1-5
- Task 7.2 (Integration tests) → depends on 7.1
- Task 7.3 (Documentation) → depends on all
- Task 11.3 (Vector integration tests) → depends on all Stage 3-4

**Wave 8 (Performance & Docs)**: 2 hours
- Task 12.1 (Performance metrics) → depends on 10.3
- Task 12.2 (Migration script) → depends on 9.1
- Task 12.3 (Query optimization) → depends on 8.2
- Task 13.1 (Vector tests) → depends on all Stage 2-5
- Task 13.2 (Benchmarks) → depends on 13.1
- Task 13.3 (Vector docs) → depends on all

**Wave 9 (Production Ready)**: 30 min
- Task 14.1 (Cost analysis)
- Task 14.2 (Deployment checklist)
- Task 14.3 (Monitoring setup)

---

## Success Criteria

### Phase 11 Complete When:
- [ ] All 18 tasks completed
- [ ] 81 tests passing (24 existing + 57 new)
- [ ] Documentation updated
- [ ] User can compose custom skills via CLI
- [ ] Composed skills validate and verify correctly

### Phase 14 Complete When:
- [ ] All 25 tasks completed
- [ ] 15 new tests passing
- [ ] Vector search working with 40-60% relevance improvement
- [ ] Embeddings generated for all sections
- [ ] Cost monitoring in place

### Overall Success:
- [ ] 6 gaps from FINAL_GAP_CLOSURE_TASKS.md closed
- [ ] User can compose skills from sections
- [ ] User can search semantically
- [ ] All documentation updated
- [ ] Production ready for tomorrow's work session

---

## Notes for Haiku Agents

1. **Token Efficiency**: Skip verbose explanations, focus on deliverables
2. **Dependencies**: Check task dependencies before starting
3. **Testing**: Run tests after each stage, not just at end
4. **Documentation**: Update as you go, not at the end
5. **Verification**: Each task has clear success criteria
6. **Parallel Safe**: Tasks in same wave can run concurrently
7. **Error Handling**: Report blockers immediately, don't guess

---

**Total Tasks**: 42 (18 Phase 11 + 21 Phase 14 + 3 guides)
**Total Time**: ~14 hours (parallelizable to ~4-5 hours with 3-4 agents)
**Files Created**: 27 new files, 8 modified files
**Tests Added**: 96 new tests (81 Phase 11 + 15 Phase 14)
**Lines of Code**: ~4,800 lines

---

*Last Updated: 2026-02-05*
*Ready for Haiku execution*
