# Production Logging Guide

## Overview

The Multi-Agent RAG system includes production-grade logging with multiple log files, structured logging, log rotation, and performance tracking.

---

## Log Files

All logs are stored in the `logs/` directory with automatic rotation.

### 1. application.log
**Purpose**: Main application logs (human-readable)

**Content**:
- All INFO, WARNING, ERROR, DEBUG messages
- Function calls and operations
- System events

**Format**:
```
2025-01-29 10:15:23 - src.agents.sales_agent - INFO - Analyzing opportunity: OPP-2024-001
2025-01-29 10:15:24 - src.rag.retrieval - INFO - Hybrid search returned 5 results
2025-01-29 10:15:25 - src.utils.llm_client - INFO - Generated recommendations in 1.2s
```

**Rotation**: 10MB max size, 5 backups retained

---

### 2. error.log
**Purpose**: Error tracking and debugging

**Content**:
- ERROR and CRITICAL level messages only
- Full stack traces
- Exception details
- Context information

**Format**:
```
2025-01-29 10:20:15 - src.rag.vector_store - ERROR - Failed to connect to Weaviate
Traceback (most recent call last):
  File "src/rag/vector_store_weaviate.py", line 45, in __init__
    self.client = weaviate.connect_to_weaviate_cloud(...)
  weaviate.exceptions.WeaviateConnectionError: Connection refused
```

**Rotation**: 10MB max size, 5 backups retained

**Use Cases**:
- Debugging production issues
- Monitoring system health
- Alert triggers

---

### 3. application.json
**Purpose**: Structured logging for machine parsing

**Content**:
- All log levels in JSON format
- Structured fields for parsing
- Machine-readable timestamps

**Format**:
```json
{
  "timestamp": "2025-01-29T10:15:23.456Z",
  "level": "INFO",
  "logger": "src.agents.sales_agent",
  "message": "Analyzing opportunity: OPP-2024-001",
  "module": "sales_agent",
  "function": "analyze_opportunity",
  "line": 123,
  "request_id": "req-12345",
  "duration_ms": 1200
}
```

**Rotation**: 10MB max size, 5 backups retained

**Use Cases**:
- Log aggregation tools (ELK, Splunk)
- Automated monitoring
- Performance analysis
- Data analytics

---

### 4. performance.log
**Purpose**: Performance metrics and timing

**Content**:
- Operation durations
- API response times
- Database query times
- LLM generation times

**Format**:
```
2025-01-29 10:15:23 - Hybrid search completed - Duration: 345ms
2025-01-29 10:15:24 - OpenAI embedding generation - Duration: 156ms
2025-01-29 10:15:25 - Weaviate vector search - Duration: 89ms
2025-01-29 10:15:26 - GPT-4 recommendation generation - Duration: 2341ms
```

**Rotation**: 10MB max size, 5 backups retained

**Use Cases**:
- Performance monitoring
- Optimization identification
- SLA tracking
- Capacity planning

---

### 5. user_activity.log
**Purpose**: User action tracking

**Content**:
- User interactions
- Feature usage
- Feedback submissions
- Business metrics

**Format**:
```
2025-01-29 10:15:23 - User user_123 performed search_opportunity - {'opportunity_id': 'OPP-2024-001'}
2025-01-29 10:15:30 - User user_123 performed accept_recommendation - {'action_id': 'action_1'}
2025-01-29 10:15:35 - User user_123 performed provide_feedback - {'rating': 'positive'}
```

**Rotation**: 10MB max size, 5 backups retained

**Use Cases**:
- User behavior analysis
- Feature adoption tracking
- A/B testing analysis
- Audit trail

---

## Setup Logging

### Method 1: Automatic Setup

```python
from src.utils.logging_config import setup_logging

# Initialize logging (typically in main.py or app startup)
setup_logging(
    log_level="INFO",
    log_dir="logs",
    enable_console=True,
    enable_file=True,
    enable_json=True
)
```

### Method 2: Using Init Script

```bash
python scripts/init_logging.py
```

This creates all log files and verifies the setup.

---

## Using Logging in Code

### Basic Logging

```python
import logging
from src.utils.logging_config import get_logger

# Get logger for your module
logger = get_logger(__name__)

# Log messages
logger.debug("Detailed debugging information")
logger.info("General information about operations")
logger.warning("Warning about potential issues")
logger.error("Error that needs attention")
logger.critical("Critical error requiring immediate action")
```

### Logging with Context

```python
from src.utils.logging_config import LogContext

logger = get_logger(__name__)

# Automatic timing and error handling
with LogContext(logger, "Process opportunity", opportunity_id="OPP-001"):
    # Your code here
    result = analyze_opportunity("OPP-001")
    # Automatically logs duration and success/failure
```

**Output**:
```
2025-01-29 10:15:23 - Starting: Process opportunity
2025-01-29 10:15:25 - Completed: Process opportunity - Duration: 1234ms
```

### Logging API Requests

```python
from src.utils.logging_config import log_api_request

logger = get_logger(__name__)

# Log API calls
log_api_request(
    logger,
    endpoint="/api/opportunities",
    method="POST",
    status_code=200,
    duration_ms=345
)
```

**Output**:
```
2025-01-29 10:15:23 - API POST /api/opportunities - Duration: 345ms
```

**JSON Output**:
```json
{
  "timestamp": "2025-01-29T10:15:23.456Z",
  "level": "INFO",
  "message": "API POST /api/opportunities",
  "endpoint": "/api/opportunities",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 345
}
```

### Logging User Actions

```python
from src.utils.logging_config import log_user_action

logger = get_logger(__name__)

# Track user behavior
log_user_action(
    logger,
    user_id="user_123",
    action="accept_recommendation",
    details={"opportunity_id": "OPP-001", "action": "multi-threading"}
)
```

**Output** (user_activity.log):
```
2025-01-29 10:15:23 - User user_123 performed accept_recommendation - {'opportunity_id': 'OPP-001', 'action': 'multi-threading'}
```

### Logging Performance Metrics

```python
from src.utils.logging_config import log_performance

logger = get_logger(__name__)

# Track operation performance
log_performance(
    logger,
    operation="vector_search",
    duration_ms=156,
    details={"query": "stalled deals", "results": 5}
)
```

**Output** (performance.log):
```
2025-01-29 10:15:23 - Performance: vector_search - Duration: 156ms
```

### Logging Errors with Context

```python
from src.utils.logging_config import log_error_with_context

logger = get_logger(__name__)

try:
    result = risky_operation()
except Exception as e:
    log_error_with_context(
        logger,
        error=e,
        context={
            "operation": "risky_operation",
            "parameters": {"param1": "value1"},
            "user_id": "user_123"
        }
    )
```

**Output** (error.log):
```
2025-01-29 10:15:23 - ERROR - Error: Division by zero
Context: {'operation': 'risky_operation', 'parameters': {'param1': 'value1'}, 'user_id': 'user_123'}
Traceback (most recent call last):
  ...
```

---

## Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| **DEBUG** | Detailed diagnostic info | Variable values, loop iterations, internal state |
| **INFO** | General informational messages | Operation started/completed, configuration loaded |
| **WARNING** | Warning about potential issues | Deprecated features, fallback used, high latency |
| **ERROR** | Error that needs attention | API failed, database error, validation failed |
| **CRITICAL** | Critical system failure | System crash, data corruption, security breach |

---

## Log Rotation

### Configuration

All log files automatically rotate when they reach **10MB**.

**Settings**:
- Max file size: 10MB
- Backups retained: 5
- Total disk space: ~60MB per log type

**Example**:
```
logs/
├── application.log       (current, up to 10MB)
├── application.log.1     (backup 1)
├── application.log.2     (backup 2)
├── application.log.3     (backup 3)
├── application.log.4     (backup 4)
├── application.log.5     (backup 5, oldest)
```

When `application.log` reaches 10MB:
1. `application.log.5` is deleted
2. Other backups shift: `.4` → `.5`, `.3` → `.4`, etc.
3. `application.log` → `application.log.1`
4. New `application.log` created

### Manual Rotation

```python
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'logs/application.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

# Force rotation
handler.doRollover()
```

---

## Monitoring Logs

### Tail Logs (Real-time)

**Windows**:
```cmd
# PowerShell
Get-Content logs\application.log -Wait -Tail 50

# Command Prompt (use external tool like tail.exe)
tail -f logs\application.log
```

**Linux/Mac**:
```bash
tail -f logs/application.log
```

### Search Logs

**Windows**:
```cmd
# Find errors
findstr /C:"ERROR" logs\application.log

# Find specific operation
findstr /C:"Analyzing opportunity" logs\application.log
```

**Linux/Mac**:
```bash
# Find errors
grep "ERROR" logs/application.log

# Find specific operation
grep "Analyzing opportunity" logs/application.log
```

### Parse JSON Logs

```python
import json

# Read and parse JSON logs
with open('logs/application.json', 'r') as f:
    for line in f:
        log_entry = json.loads(line)
        if log_entry['level'] == 'ERROR':
            print(f"Error at {log_entry['timestamp']}: {log_entry['message']}")
```

Or use `jq` tool:
```bash
# Find all errors
cat logs/application.json | jq 'select(.level == "ERROR")'

# Find slow operations (>1000ms)
cat logs/application.json | jq 'select(.duration_ms > 1000)'

# Count errors per hour
cat logs/application.json | jq -r 'select(.level == "ERROR") | .timestamp' | cut -d: -f1 | sort | uniq -c
```

---

## Best Practices

### 1. Use Appropriate Log Levels

```python
# ✅ Good
logger.debug(f"Processing {len(items)} items")
logger.info("Analysis completed successfully")
logger.warning("Using fallback embedding model")
logger.error("Failed to connect to database", exc_info=True)

# ❌ Bad
logger.info("x = 123")  # Too granular, use DEBUG
logger.error("User clicked button")  # Not an error, use INFO
```

### 2. Include Context

```python
# ✅ Good
logger.info(
    "Recommendation generated",
    extra={
        'opportunity_id': opp_id,
        'risk_score': 0.87,
        'playbooks_retrieved': 5,
        'duration_ms': 1234
    }
)

# ❌ Bad
logger.info("Done")  # No context
```

### 3. Log Exceptions Properly

```python
# ✅ Good
try:
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)  # Includes stack trace
    # Or
    log_error_with_context(logger, e, context={'param': value})

# ❌ Bad
except Exception as e:
    logger.error(str(e))  # No stack trace!
```

### 4. Avoid Logging Sensitive Data

```python
# ✅ Good
logger.info(f"User authenticated: user_id={user_id}")

# ❌ Bad
logger.info(f"User login: password={password}")  # Never log passwords!
logger.info(f"API call: key={api_key}")  # Never log API keys!
```

### 5. Use Structured Logging

```python
# ✅ Good (structured, parseable)
logger.info(
    "Search completed",
    extra={
        'query': query,
        'results_count': len(results),
        'duration_ms': duration
    }
)

# ❌ Less ideal (harder to parse)
logger.info(f"Search for '{query}' found {len(results)} results in {duration}ms")
```

---

## Troubleshooting

### Log Files Not Created

**Issue**: `logs/` directory doesn't exist

**Solution**:
```python
from pathlib import Path
Path("logs").mkdir(parents=True, exist_ok=True)
```

Or run:
```bash
python scripts/init_logging.py
```

### Too Many Log Files

**Issue**: Disk space filling up

**Solution**:
Reduce backup count or max file size:
```python
setup_logging(
    max_bytes=5*1024*1024,  # 5MB instead of 10MB
    backup_count=3  # 3 backups instead of 5
)
```

### Logs Not Rotating

**Issue**: Log file > 10MB but not rotating

**Solution**:
Check file permissions and manually trigger rotation:
```python
import logging
for handler in logging.getLogger().handlers:
    if hasattr(handler, 'doRollover'):
        handler.doRollover()
```

---

## Integration with Monitoring Tools

### ELK Stack (Elasticsearch, Logstash, Kibana)

Use `application.json` for structured ingestion:

**Logstash config**:
```
input {
  file {
    path => "/path/to/logs/application.json"
    codec => "json"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "multi-agent-rag-%{+YYYY.MM.dd}"
  }
}
```

### Splunk

Forward JSON logs to Splunk:
```bash
splunk add monitor /path/to/logs/application.json -sourcetype _json
```

### CloudWatch (AWS)

Use CloudWatch agent to ship logs:
```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/path/to/logs/application.json",
            "log_group_name": "/multi-agent-rag/application",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

---

## Summary

### Log Files Created:
1. ✅ `application.log` - Main application logs
2. ✅ `error.log` - Errors only
3. ✅ `application.json` - Structured JSON
4. ✅ `performance.log` - Performance metrics
5. ✅ `user_activity.log` - User actions

### Features:
- ✅ Automatic rotation (10MB, 5 backups)
- ✅ Colored console output
- ✅ Structured JSON logging
- ✅ Performance tracking
- ✅ Error tracking with stack traces
- ✅ User activity monitoring

### Initialize:
```bash
python scripts/init_logging.py
```

### Use in Code:
```python
from src.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
logger.info("Hello, world!")
```

---

**Production-ready logging is now configured!** 📊
