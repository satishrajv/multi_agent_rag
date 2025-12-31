# Log Files Directory

This directory contains all application logs.

## Log Files

### Production Logs (Auto-generated)

1. **application.log** - Main application logs (human-readable)
2. **error.log** - Errors and exceptions only
3. **application.json** - Structured JSON logs (machine-readable)
4. **performance.log** - Performance metrics and timing
5. **user_activity.log** - User actions and interactions

All log files:
- Automatically rotate at 10MB
- Keep 5 backup files
- Total ~60MB per log type
- UTF-8 encoded

## Initialization

Run this to initialize logging:

```bash
python scripts/init_logging.py
```

## Viewing Logs

### Real-time Monitoring

**PowerShell**:
```powershell
Get-Content logs\application.log -Wait -Tail 50
```

**Linux/Mac**:
```bash
tail -f logs/application.log
```

### Search Logs

**Find errors**:
```cmd
findstr /C:"ERROR" logs\application.log
```

**Find specific operation**:
```cmd
findstr /C:"Analyzing opportunity" logs\application.log
```

### Parse JSON Logs

```python
import json

with open('logs/application.json', 'r') as f:
    for line in f:
        entry = json.loads(line)
        if entry['level'] == 'ERROR':
            print(f"{entry['timestamp']}: {entry['message']}")
```

## Log Rotation

Files automatically rotate:
- application.log (current)
- application.log.1 (most recent backup)
- application.log.2
- application.log.3
- application.log.4
- application.log.5 (oldest backup)

Oldest files are automatically deleted when limits are reached.

## More Information

See `LOGGING_GUIDE.md` for complete documentation.
