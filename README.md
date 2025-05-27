# ocp-executive-discovery -- OCP Executive Discovery Tool

## Overview
Automated executive contact discovery system for organizational outreach. Rebuilds previous system that had 87% false positive rate to achieve <5% false positives.

## Key Features
- Multi-source verification for executive contacts
- Domain discovery and validation
- Email pattern matching with verification
- SMTP handshake verification for email accuracy
- Batch processing for large organizational databases
- CRM integration ready

## Architecture
- **Data Layer**: CSV processing and tracking
- **Discovery Layer**: Web scraping and search orchestration  
- **Validation Layer**: Name, domain, and email verification
- **Export Layer**: CRM formatting and integration

## Performance Targets
- False positive rate: <5% (previous: 87%)
- Email bounce rate: <3% (previous: 17%)
- Processing speed: 100 organizations/hour
- Verification accuracy: >90%

## Setup
```bash
# Clone repository
git clone [repository-url]
cd ocp-executive-discovery

# Install dependencies
pip install -r requirements.txt

# Run CSV cleaner
python scripts/clean_csv.py

# Start discovery pipeline
python src/main.py
