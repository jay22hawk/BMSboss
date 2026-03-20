# BMS Boss

**Mass Save Prescriptive BMS Calculator — Automation Platform**

BMS Boss automates the process of extracting data from utility energy bills and populating the Mass Save Prescriptive BMS Calculator spreadsheet. Built for BMS vendors and installers serving commercial and industrial customers across Massachusetts.

## What It Does

1. **Upload** a utility bill PDF (National Grid, Eversource, and more)
2. **Review** the auto-extracted data — account numbers, usage history, charges
3. **Configure** building info, project details, and sequences of operation
4. **Generate** a fully populated BMS Calculator Excel file ready for Mass Save submission

## Quick Start (Local Development)

```bash
cd extraction-service
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure

```
extraction-service/
  app.py              — HTTP server and API endpoints
  auth.py             — Authentication, sessions, subscription enforcement
  crud.py             — CRUD operations for clients, buildings, projects
  database.py         — SQLite schema and database layer
  extractor.py        — Bill extraction pipeline (auto-detects utility)
  excel_generator.py  — Populates the official BMS Calculator template
  models.py           — Data models and enums
  parsers/            — Utility bill parsers (National Grid, Eversource)
  templates/          — Bundled BMS Calculator template
  static/             — Frontend (HTML/CSS/JS)
```

## Supported Utilities

| Utility | Status |
|---------|--------|
| National Grid | Complete |
| Eversource | Stub (in progress) |
| Berkshire Gas | Planned |
| Cape Light Compact | Planned |
| Liberty | Planned |
| Unitil | Planned |

## Status

**Proof of Concept** — Core extraction and calculator generation working. Account management system built. Collecting feedback for MVP.
