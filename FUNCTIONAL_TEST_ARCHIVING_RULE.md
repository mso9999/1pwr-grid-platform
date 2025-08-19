# Functional Test Archiving Rule

## Rule
**NEVER overwrite any functional test logs.** Always:
1. Save new test results with datetime in filename (format: `YYMMDD_HHMM_functional_tests.csv`)
2. Archive old files in `/functional_tests_archive/` folder
3. Archive filename format: `YYMMDD_HHMM_functional_tests_archived_YYYYMMDD_HHMMSS.csv`

## Archive Structure
```
1pwr-grid-platform/
├── functional_tests_archive/       # Archive folder for old test logs
│   └── [archived test files]
└── YYMMDD_HHMM_functional_tests.csv  # Current test file
```

## Implementation
- Archive folder created: `/functional_tests_archive/`
- Current test file: `250818_2139_functional_tests.csv`
- Archived copy created with timestamp

This ensures complete test history preservation and traceability.
