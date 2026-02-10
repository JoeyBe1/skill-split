# Skill-Split Demo Scenarios

This directory contains comprehensive demo scripts that demonstrate the real-world value of skill-split's progressive disclosure system.

## Available Demos

### 1. Token Savings Demo (`token_savings_demo.sh`)

**Demonstrates:** Token efficiency through progressive disclosure

**Value Proposition:**
- 99% context savings: Load only what you need
- Cost savings at API prices
- Performance improvement with large files

**Run:**
```bash
cd /Users/joey/working/skill-split
./demo/token_savings_demo.sh
```

**What You'll See:**
- File size analysis (full file vs single section)
- Token comparison (traditional vs progressive)
- Cost calculation at current API prices
- Scaled savings for 1000 operations
- Progressive disclosure workflow demonstration

---

### 2. Search Relevance Demo (`search_relevance_demo.sh`)

**Demonstrates:** Three search modes comparison

**Value Proposition:**
- BM25 (Keywords): Fast, local, exact matching
- Vector (Semantic): Concept discovery, semantic understanding
- Hybrid (Combined): Best of both with tunable weights

**Run:**
```bash
cd /Users/joey/working/skill-split
./demo/search_relevance_demo.sh
```

**What You'll See:**
- Search result comparison across modes
- Boolean operators (AND, OR, NEAR)
- File-specific search
- Performance metrics
- Ranking scores

**For Semantic Search:**
```bash
ENABLE_EMBEDDINGS=true ./demo/search_relevance_demo.sh
```

---

### 3. Component Deployment Demo (`component_deployment_demo.sh`)

**Demonstrates:** Multi-file checkout for complex components

**Value Proposition:**
- Atomic deployment of multi-file components
- Runtime-ready after checkout
- Directory structure preservation
- Rollback on failure

**Requirements:**
- `SUPABASE_URL` environment variable
- `SUPABASE_KEY` environment variable

**Run:**
```bash
cd /Users/joey/working/skill-split
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
./demo/component_deployment_demo.sh
```

**What You'll See:**
- Plugin component creation (plugin.json + .mcp.json + hooks)
- Hooks component deployment (hooks.json + shell scripts)
- Multi-file atomic checkout
- Runtime readiness verification
- Checkin workflow

---

### 4. Disaster Recovery Demo (`disaster_recovery_demo.sh`)

**Demonstrates:** Backup and restore capabilities

**Value Proposition:**
- Automated timestamped backups with gzip compression
- Integrity validation during restoration
- Safe recovery from data corruption
- Multiple backup generations

**Run:**
```bash
cd /Users/joey/working/skill-split
./demo/disaster_recovery_demo.sh
```

**What You'll See:**
- Database backup creation
- Simulated database corruption
- Restore from backup with validation
- Integrity checks (FTS5, foreign keys)
- Incremental backups

---

### 5. Batch Processing Demo (`batch_processing_demo.sh`)

**Demonstrates:** Scalability with large datasets

**Value Proposition:**
- Efficient batch ingestion of 1000+ files
- Performance metrics and monitoring
- Production-ready workflows
- Linear scalability

**Run:**
```bash
cd /Users/joey/working/skill-split
./demo/batch_processing_demo.sh
```

**What You'll See:**
- Generation of 100 test files
- Batch ingestion performance
- Search performance on large datasets
- Progressive disclosure at scale
- Scalability projections

**Custom File Count:**
```bash
NUM_FILES=1000 ./demo/batch_processing_demo.sh
```

---

## Master Demo Runner

Run all demos or select specific ones:

```bash
cd /Users/joey/working/skill-split

# Interactive menu
./demo/run_all_demos.sh

# Run specific demo
./demo/run_all_demos.sh token
./demo/run_all_demos.sh search
./demo/run_all_demos.sh component
./demo/run_all_demos.sh recovery
./demo/run_all_demos.sh batch
```

## Quick Start

1. **Prerequisites:**
   - Python 3 with sqlite3
   - skill-split installed in `/Users/joey/working/skill-split`

2. **Run Token Savings Demo (quickest):**
   ```bash
   ./demo/token_savings_demo.sh
   ```

3. **Run All Demos:**
   ```bash
   ./demo/run_all_demos.sh
   ```

## Environment Variables

- `ENABLE_EMBEDDINGS=true` - Enable semantic search (requires OPENAI_API_KEY)
- `NUM_FILES=N` - Set number of files for batch demo (default: 100)
- `SUPABASE_URL` - Supabase project URL (for component demo)
- `SUPABASE_KEY` - Supabase API key (for component demo)
- `OPENAI_API_KEY` - OpenAI API key (for semantic search)

## Demo Outputs

Each demo generates output in `demo/work/`:
- Test databases
- Generated files
- Backup files
- Deployed components

Clean up after running:
```bash
rm -rf /Users/joey/working/skill-split/demo/work
```

## Value Summary

| Demo | Primary Value | ROI |
|------|---------------|-----|
| Token Savings | 99% cost reduction per operation | \$X per 1000 operations |
| Search Relevance | Best result quality for any query | Time savings in discovery |
| Component Deployment | Atomic multi-file operations | Reduced deployment errors |
| Disaster Recovery | Data safety and recovery | Peace of mind, data protection |
| Batch Processing | Production-scale performance | Handle any library size |

## Troubleshooting

**Python not found:**
```bash
# Ensure Python 3 is available
python3 --version
```

**Permission denied:**
```bash
# Make scripts executable
chmod +x /Users/joey/working/skill-split/demo/*.sh
```

**Supabase credentials:**
```bash
# Set environment variables
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-anon-or-service-key"
```

**Semantic search not working:**
```bash
# Check API key
export OPENAI_API_KEY="sk-..."
ENABLE_EMBEDDINGS=true ./demo/search_relevance_demo.sh
```

## Integration with CI/CD

These demos can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Token Savings Demo
  run: ./demo/token_savings_demo.sh

- name: Run Disaster Recovery Demo
  run: ./demo/disaster_recovery_demo.sh

- name: Verify Batch Processing
  run: NUM_FILES=100 ./demo/batch_processing_demo.sh
```

---

*Last Updated: 2025-02-10*
