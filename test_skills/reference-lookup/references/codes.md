# Error Code Reference

This file contains the official error code definitions.

## Error Codes

| Code | Category | Description |
|------|----------|-------------|
| E001 | File | File not found - the specified file does not exist |
| E002 | Permission | Permission denied - insufficient access rights |
| E003 | Network | Connection timeout - server did not respond |
| E004 | Input | Invalid input format - data does not match expected schema |
| E005 | Memory | Out of memory - insufficient system resources |
| E006 | Config | Configuration error - missing or invalid settings |
| E007 | Auth | Authentication failed - invalid credentials |
| E008 | Rate | Rate limit exceeded - too many requests |

## Status Codes

| Code | Meaning |
|------|---------|
| S100 | Operation in progress |
| S200 | Operation completed successfully |
| S300 | Operation completed with warnings |
| S400 | Operation failed - recoverable |
| S500 | Operation failed - critical |

## Notes

- All error codes start with 'E' followed by three digits
- All status codes start with 'S' followed by three digits
- For detailed troubleshooting, consult the system documentation
