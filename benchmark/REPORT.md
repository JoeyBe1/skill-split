# Skill-Split Performance Benchmark Report

**Template Version**: 1.0.0
**Generated**: {{TIMESTAMP}}
**Commit**: {{COMMIT_HASH}}
**Machine**: {{MACHINE_INFO}}
**Python Version**: {{PYTHON_VERSION}}
**Test Command**: `{{BENCHMARK_COMMAND}}`

---

## Executive Summary

**Overall Assessment**: {{OVERALL_STATUS}}

| Metric | Baseline | Current | Delta | Status |
|--------|----------|---------|-------|--------|
| Parse Small (1KB) | {{BASELINE_PARSE_SMALL}} | {{CURRENT_PARSE_SMALL}} | {{DELTA_PARSE_SMALL}} | {{STATUS_PARSE_SMALL}} |
| Parse Medium (50KB) | {{BASELINE_PARSE_MEDIUM}} | {{CURRENT_PARSE_MEDIUM}} | {{DELTA_PARSE_MEDIUM}} | {{STATUS_PARSE_MEDIUM}} |
| Parse Large (500KB) | {{BASELINE_PARSE_LARGE}} | {{CURRENT_PARSE_LARGE}} | {{DELTA_PARSE_LARGE}} | {{STATUS_PARSE_LARGE}} |
| Query Latency | {{BASELINE_QUERY}} | {{CURRENT_QUERY}} | {{DELTA_QUERY}} | {{STATUS_QUERY}} |
| BM25 Search | {{BASELINE_BM25}} | {{CURRENT_BM25}} | {{DELTA_BM25}} | {{STATUS_BM25}} |

---

## 1. Parsing Performance

### 1.1 Small Files (~1KB, 5 sections)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Mean | {{PARSE_SMALL_MEAN}} ms | < 5 ms | {{PARSE_SMALL_STATUS}} |
| Median (p50) | {{PARSE_SMALL_P50}} ms | - | - |
| p95 | {{PARSE_SMALL_P95}} ms | < 10 ms | - |
| p99 | {{PARSE_SMALL_P99}} ms | < 15 ms | - |
| Min | {{PARSE_SMALL_MIN}} ms | - | - |
| Max | {{PARSE_SMALL_MAX}} ms | < 20 ms | - |
| Std Dev | {{PARSE_SMALL_STDDEV}} ms | - | - |
| Ops/sec | {{PARSE_SMALL_OPS}} | > 200 | - |

### 1.2 Medium Files (~50KB, 50 sections)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Mean | {{PARSE_MEDIUM_MEAN}} ms | < 50 ms | {{PARSE_MEDIUM_STATUS}} |
| Median (p50) | {{PARSE_MEDIUM_P50}} ms | - | - |
| p95 | {{PARSE_MEDIUM_P95}} ms | < 100 ms | - |
| p99 | {{PARSE_MEDIUM_P99}} ms | < 150 ms | - |
| Min | {{PARSE_MEDIUM_MIN}} ms | - | - |
| Max | {{PARSE_MEDIUM_MAX}} ms | < 200 ms | - |
| Std Dev | {{PARSE_MEDIUM_STDDEV}} ms | - | - |
| Ops/sec | {{PARSE_MEDIUM_OPS}} | > 20 | - |

### 1.3 Large Files (~500KB, 500 sections)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Mean | {{PARSE_LARGE_MEAN}} ms | < 500 ms | {{PARSE_LARGE_STATUS}} |
| Median (p50) | {{PARSE_LARGE_P50}} ms | - | - |
| p95 | {{PARSE_LARGE_P95}} ms | < 1000 ms | - |
| p99 | {{PARSE_LARGE_P99}} ms | < 1500 ms | - |
| Min | {{PARSE_LARGE_MIN}} ms | - | - |
| Max | {{PARSE_LARGE_MAX}} ms | < 2000 ms | - |
| Std Dev | {{PARSE_LARGE_STDDEV}} ms | - | - |
| Ops/sec | {{PARSE_LARGE_OPS}} | > 2 | - |

### 1.4 Scaling Analysis

| Sections | Time (ms) | Time/Section | Complexity |
|----------|-----------|--------------|------------|
| 10 | {{SCALE_10_TIME}} | {{SCALE_10_PER_SECTION}} ms | O(n) |
| 50 | {{SCALE_50_TIME}} | {{SCALE_50_PER_SECTION}} ms | O(n) |
| 100 | {{SCALE_100_TIME}} | {{SCALE_100_PER_SECTION}} ms | O(n) |
| 500 | {{SCALE_500_TIME}} | {{SCALE_500_PER_SECTION}} ms | O(n) |

**Algorithmic Complexity**: {{PARSING_COMPLEXITY_ASSESSMENT}}

---

## 2. Database Operations

### 2.1 Store Operations

| File Size | Mean | p95 | p99 | Ops/sec | Status |
|-----------|------|-----|-----|---------|--------|
| Small | {{DB_STORE_SMALL_MEAN}} ms | {{DB_STORE_SMALL_P95}} ms | {{DB_STORE_SMALL_P99}} ms | {{DB_STORE_SMALL_OPS}} | {{DB_STORE_SMALL_STATUS}} |
| Medium | {{DB_STORE_MEDIUM_MEAN}} ms | {{DB_STORE_MEDIUM_P95}} ms | {{DB_STORE_MEDIUM_P99}} ms | {{DB_STORE_MEDIUM_OPS}} | {{DB_STORE_MEDIUM_STATUS}} |
| Large | {{DB_STORE_LARGE_MEAN}} ms | {{DB_STORE_LARGE_P95}} ms | {{DB_STORE_LARGE_P99}} ms | {{DB_STORE_LARGE_OPS}} | {{DB_STORE_LARGE_STATUS}} |

### 2.2 Query Operations

| Operation | Mean | p95 | p99 | Ops/sec | Status |
|-----------|------|-----|-----|---------|--------|
| get_section | {{DB_GET_SECTION_MEAN}} ms | {{DB_GET_SECTION_P95}} ms | {{DB_GET_SECTION_P99}} ms | {{DB_GET_SECTION_OPS}} | {{DB_GET_SECTION_STATUS}} |
| get_section_tree | {{DB_GET_TREE_MEAN}} ms | {{DB_GET_TREE_P95}} ms | {{DB_GET_TREE_P99}} ms | {{DB_GET_TREE_OPS}} | {{DB_GET_TREE_STATUS}} |
| get_next_section | {{DB_GET_NEXT_MEAN}} ms | {{DB_GET_NEXT_P95}} ms | {{DB_GET_NEXT_P99}} ms | {{DB_GET_NEXT_OPS}} | {{DB_GET_NEXT_STATUS}} |
| list_sections | {{DB_LIST_MEAN}} ms | {{DB_LIST_P95}} ms | {{DB_LIST_P99}} ms | {{DB_LIST_OPS}} | {{DB_LIST_STATUS}} |

### 2.3 Batch Operations

| Metric | Value |
|--------|-------|
| Batch Store (3 files) | {{BATCH_STORE_TIME}} ms |
| Throughput | {{BATCH_THROUGHPUT}} files/sec |
| Efficiency | {{BATCH_EFFICIENCY}} % |

---

## 3. Search Performance

### 3.1 BM25 Full-Text Search

| Query Type | Mean | p95 | p99 | Ops/sec | Status |
|------------|------|-----|-----|---------|--------|
| Single term | {{BM25_SINGLE_MEAN}} ms | {{BM25_SINGLE_P95}} ms | {{BM25_SINGLE_P99}} ms | {{BM25_SINGLE_OPS}} | {{BM25_SINGLE_STATUS}} |
| Multi term | {{BM25_MULTI_MEAN}} ms | {{BM25_MULTI_P95}} ms | {{BM25_MULTI_P99}} ms | {{BM25_MULTI_OPS}} | {{BM25_MULTI_STATUS}} |
| With limit | {{BM25_LIMIT_MEAN}} ms | {{BM25_LIMIT_P95}} ms | {{BM25_LIMIT_P99}} ms | {{BM25_LIMIT_OPS}} | {{BM25_LIMIT_STATUS}} |
| No results | {{BM25_EMPTY_MEAN}} ms | {{BM25_EMPTY_P95}} ms | {{BM25_EMPTY_P99}} ms | {{BM25_EMPTY_OPS}} | {{BM25_EMPTY_STATUS}} |

### 3.2 Vector Search (if available)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Single embedding | {{VECTOR_SINGLE_MEAN}} ms | < 200 ms | {{VECTOR_SINGLE_STATUS}} |
| Batch embeddings | {{VECTOR_BATCH_MEAN}} ms | < 1000 ms | {{VECTOR_BATCH_STATUS}} |
| Semantic search | {{VECTOR_SEARCH_MEAN}} ms | < 500 ms | {{VECTOR_SEARCH_STATUS}} |
| Cache hit rate | {{VECTOR_CACHE_HIT}} % | > 80% | {{VECTOR_CACHE_STATUS}} |

### 3.3 Hybrid Search (if available)

| Vector Weight | Mean | p95 | p99 | Status |
|---------------|------|-----|-----|--------|
| 0.3 (keyword) | {{HYBRID_03_MEAN}} ms | {{HYBRID_03_P95}} ms | {{HYBRID_03_P99}} ms | {{HYBRID_03_STATUS}} |
| 0.5 (balanced) | {{HYBRID_05_MEAN}} ms | {{HYBRID_05_P95}} ms | {{HYBRID_05_P99}} ms | {{HYBRID_05_STATUS}} |
| 0.7 (semantic) | {{HYBRID_07_MEAN}} ms | {{HYBRID_07_P95}} ms | {{HYBRID_07_P99}} ms | {{HYBRID_07_STATUS}} |
| 1.0 (pure vector) | {{HYBRID_10_MEAN}} ms | {{HYBRID_10_P95}} ms | {{HYBRID_10_P99}} ms | {{HYBRID_10_STATUS}} |

---

## 4. Memory Usage

### 4.1 Memory Patterns

| Operation | Current | Peak | Delta | Status |
|-----------|---------|------|-------|--------|
| Parse small | {{MEM_PARSE_SMALL_CURRENT}} MB | {{MEM_PARSE_SMALL_PEAK}} MB | {{MEM_PARSE_SMALL_DELTA}} MB | {{MEM_PARSE_SMALL_STATUS}} |
| Parse medium | {{MEM_PARSE_MEDIUM_CURRENT}} MB | {{MEM_PARSE_MEDIUM_PEAK}} MB | {{MEM_PARSE_MEDIUM_DELTA}} MB | {{MEM_PARSE_MEDIUM_STATUS}} |
| Parse large | {{MEM_PARSE_LARGE_CURRENT}} MB | {{MEM_PARSE_LARGE_PEAK}} MB | {{MEM_PARSE_LARGE_DELTA}} MB | {{MEM_PARSE_LARGE_STATUS}} |
| Store large | {{MEM_STORE_CURRENT}} MB | {{MEM_STORE_PEAK}} MB | {{MEM_STORE_DELTA}} MB | {{MEM_STORE_STATUS}} |

### 4.2 Memory Leak Detection

| Test | Iterations | Start | End | Delta | Status |
|------|------------|-------|-----|-------|--------|
| Parse loop | {{MEM_LEAK_PARSE_ITER}} | {{MEM_LEAK_PARSE_START}} MB | {{MEM_LEAK_PARSE_END}} MB | {{MEM_LEAK_PARSE_DELTA}} MB | {{MEM_LEAK_PARSE_STATUS}} |
| Query loop | {{MEM_LEAK_QUERY_ITER}} | {{MEM_LEAK_QUERY_START}} MB | {{MEM_LEAK_QUERY_END}} MB | {{MEM_LEAK_QUERY_DELTA}} MB | {{MEM_LEAK_QUERY_STATUS}} |
| Search loop | {{MEM_LEAK_SEARCH_ITER}} | {{MEM_LEAK_SEARCH_START}} MB | {{MEM_LEAK_SEARCH_END}} MB | {{MEM_LEAK_SEARCH_DELTA}} MB | {{MEM_LEAK_SEARCH_STATUS}} |

**Memory Leak Assessment**: {{MEMORY_LEAK_ASSESSMENT}}

---

## 5. Throughput Analysis

### 5.1 Parsing Throughput

| File Size | Throughput | Target | Status |
|-----------|------------|--------|--------|
| Small (10x) | {{THROUGHPUT_PARSE_SMALL}} ops/sec | > 1000 | {{THROUGHPUT_PARSE_SMALL_STATUS}} |
| Medium (5x) | {{THROUGHPUT_PARSE_MEDIUM}} ops/sec | > 50 | {{THROUGHPUT_PARSE_MEDIUM_STATUS}} |

### 5.2 Query Throughput

| Operation | Throughput | Target | Status |
|-----------|------------|--------|--------|
| Sequential queries | {{THROUGHPUT_QUERY}} queries/sec | > 1000 | {{THROUGHPUT_QUERY_STATUS}} |
| Search operations | {{THROUGHPUT_SEARCH}} searches/sec | > 100 | {{THROUGHPUT_SEARCH_STATUS}} |

---

## 6. Critical Path Performance

### 6.1 End-to-End Workflow

```
Parse -> Store -> Query
```

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total time | {{CRITICAL_PATH_TIME}} ms | < 100 ms | {{CRITICAL_PATH_STATUS}} |
| Parse % | {{CRITICAL_PATH_PARSE_PCT}} % | - | - |
| Store % | {{CRITICAL_PATH_STORE_PCT}} % | - | - |
| Query % | {{CRITICAL_PATH_QUERY_PCT}} % | - | - |

**Bottleneck Analysis**: {{BOTTLENECK_ANALYSIS}}

### 6.2 Regression Detection

| Benchmark | Baseline | Current | Regression | Status |
|-----------|----------|---------|------------|--------|
| Parse medium | {{REGRESSION_PARSE_BASE}} | {{REGRESSION_PARSE_CUR}} | {{REGRESSION_PARSE_DELTA}} % | {{REGRESSION_PARSE_STATUS}} |
| Query latency | {{REGRESSION_QUERY_BASE}} | {{REGRESSION_QUERY_CUR}} | {{REGRESSION_QUERY_DELTA}} % | {{REGRESSION_QUERY_STATUS}} |
| Search BM25 | {{REGRESSION_SEARCH_BASE}} | {{REGRESSION_SEARCH_CUR}} | {{REGRESSION_SEARCH_DELTA}} % | {{REGRESSION_SEARCH_STATUS}} |

**Regression Status**: {{REGRESSION_OVERALL_STATUS}}

---

## 7. Performance Optimization Opportunities

### 7.1 Identified Bottlenecks

1. **{{BOTTLENECK_1}}**
   - Impact: {{BOTTLENECK_1_IMPACT}}
   - Recommendation: {{BOTTLENECK_1_REC}}
   - Expected gain: {{BOTTLENECK_1_GAIN}}

2. **{{BOTTLENECK_2}}**
   - Impact: {{BOTTLENECK_2_IMPACT}}
   - Recommendation: {{BOTTLENECK_2_REC}}
   - Expected gain: {{BOTTLENECK_2_GAIN}}

3. **{{BOTTLENECK_3}}**
   - Impact: {{BOTTLENECK_3_IMPACT}}
   - Recommendation: {{BOTTLENECK_3_REC}}
   - Expected gain: {{BOTTLENECK_3_GAIN}}

### 7.2 Caching Opportunities

| Operation | Current | Cached Potential | Expected Gain |
|-----------|---------|------------------|---------------|
| {{CACHE_OPP_1}} | {{CACHE_OPP_1_CURRENT}} ms | {{CACHE_OPP_1_CACHED}} ms | {{CACHE_OPP_1_GAIN}} % |
| {{CACHE_OPP_2}} | {{CACHE_OPP_2_CURRENT}} ms | {{CACHE_OPP_2_CACHED}} ms | {{CACHE_OPP_2_GAIN}} % |
| {{CACHE_OPP_3}} | {{CACHE_OPP_3_CURRENT}} ms | {{CACHE_OPP_3_CACHED}} ms | {{CACHE_OPP_3_GAIN}} % |

---

## 8. Scalability Assessment

### 8.1 Data Volume Projections

| Sections | Current Time | Projected Time (10x) | Projected Time (100x) | Complexity |
|----------|--------------|----------------------|-----------------------|------------|
| 50 | {{SCALE_50_CURRENT}} ms | {{SCALE_50_10X}} ms | {{SCALE_50_100X}} ms | {{SCALE_50_COMPLEXITY}} |
| 500 | {{SCALE_500_CURRENT}} ms | {{SCALE_500_10X}} ms | {{SCALE_500_100X}} ms | {{SCALE_500_COMPLEXITY}} |
| 5000 | {{SCALE_5000_CURRENT}} ms | {{SCALE_5000_10X}} ms | {{SCALE_5000_100X}} ms | {{SCALE_5000_COMPLEXITY}} |

### 8.2 Concurrent User Analysis

| Users | Queries/sec | Avg Latency | p95 Latency | Status |
|-------|-------------|-------------|-------------|--------|
| 1 | {{CONCURRENT_1_QPS}} | {{CONCURRENT_1_AVG}} ms | {{CONCURRENT_1_P95}} ms | {{CONCURRENT_1_STATUS}} |
| 10 | {{CONCURRENT_10_QPS}} | {{CONCURRENT_10_AVG}} ms | {{CONCURRENT_10_P95}} ms | {{CONCURRENT_10_STATUS}} |
| 100 | {{CONCURRENT_100_QPS}} | {{CONCURRENT_100_AVG}} ms | {{CONCURRENT_100_P95}} ms | {{CONCURRENT_100_STATUS}} |

**Scalability Verdict**: {{SCALABILITY_VERDICT}}

---

## 9. Recommendations

### 9.1 Performance Targets

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| {{REC_TARGET_1_METRIC}} | {{REC_TARGET_1_CURRENT}} | {{REC_TARGET_1_TARGET}} | {{REC_TARGET_1_PRIORITY}} |
| {{REC_TARGET_2_METRIC}} | {{REC_TARGET_2_CURRENT}} | {{REC_TARGET_2_TARGET}} | {{REC_TARGET_2_PRIORITY}} |
| {{REC_TARGET_3_METRIC}} | {{REC_TARGET_3_CURRENT}} | {{REC_TARGET_3_TARGET}} | {{REC_TARGET_3_PRIORITY}} |

### 9.2 Action Items

1. **[Priority: HIGH]** {{ACTION_ITEM_1}}
   - Effort: {{ACTION_ITEM_1_EFFORT}}
   - Impact: {{ACTION_ITEM_1_IMPACT}}
   - Timeline: {{ACTION_ITEM_1_TIMELINE}}

2. **[Priority: MEDIUM]** {{ACTION_ITEM_2}}
   - Effort: {{ACTION_ITEM_2_EFFORT}}
   - Impact: {{ACTION_ITEM_2_IMPACT}}
   - Timeline: {{ACTION_ITEM_2_TIMELINE}}

3. **[Priority: LOW]** {{ACTION_ITEM_3}}
   - Effort: {{ACTION_ITEM_3_EFFORT}}
   - Impact: {{ACTION_ITEM_3_IMPACT}}
   - Timeline: {{ACTION_ITEM_3_TIMELINE}}

---

## 10. Historical Trends

### 10.1 Performance Over Time

| Date | Commit | Parse Small | Parse Medium | Query | Search | Status |
|------|--------|-------------|--------------|-------|--------|--------|
| {{TREND_DATE_1}} | {{TREND_COMMIT_1}} | {{TREND_PARSE_SMALL_1}} | {{TREND_PARSE_MEDIUM_1}} | {{TREND_QUERY_1}} | {{TREND_SEARCH_1}} | {{TREND_STATUS_1}} |
| {{TREND_DATE_2}} | {{TREND_COMMIT_2}} | {{TREND_PARSE_SMALL_2}} | {{TREND_PARSE_MEDIUM_2}} | {{TREND_QUERY_2}} | {{TREND_SEARCH_2}} | {{TREND_STATUS_2}} |
| {{TREND_DATE_3}} | {{TREND_COMMIT_3}} | {{TREND_PARSE_SMALL_3}} | {{TREND_PARSE_MEDIUM_3}} | {{TREND_QUERY_3}} | {{TREND_SEARCH_3}} | {{TREND_STATUS_3}} |

### 10.2 Regression History

| Date | Benchmark | Before | After | Delta | Resolved |
|------|-----------|--------|-------|-------|----------|
| {{REGRESS_DATE_1}} | {{REGRESS_BENCH_1}} | {{REGRESS_BEFORE_1}} | {{REGRESS_AFTER_1}} | {{REGRESS_DELTA_1}} | {{REGRESS_RESOLVED_1}} |
| {{REGRESS_DATE_2}} | {{REGRESS_BENCH_2}} | {{REGRESS_BEFORE_2}} | {{REGRESS_AFTER_2}} | {{REGRESS_DELTA_2}} | {{REGRESS_RESOLVED_2}} |

---

## Appendix A: Test Environment

| Parameter | Value |
|-----------|-------|
| OS | {{TEST_OS}} |
| CPU | {{TEST_CPU}} |
| RAM | {{TEST_RAM}} |
| Python | {{TEST_PYTHON}} |
| pytest-benchmark | {{TEST_BENCHMARK_VER}} |
| SQLite | {{TEST_SQLITE_VER}} |

---

## Appendix B: Benchmark Execution Details

**Command**: `{{BENCHMARK_COMMAND}}`
**Duration**: {{BENCHMARK_DURATION}}
**Iterations**: {{BENCHMARK_ITERATIONS}}
**Warmup rounds**: {{BENCHMARK_WARMUP}}

---

## Appendix C: Raw Data

Full benchmark results available in: `{{RAW_DATA_FILE}}`

---

*Report generated by [Skill-Split Benchmark Suite](https://github.com/joeymafella/skill-split)*
