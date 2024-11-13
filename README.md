# n8n-nodes-version-scanner

A Python script for scanning and tracking version information of n8n nodes from the official n8n repository.

## Description

This tool automatically scans n8n node files in the n8n GitHub repository to extract and track version information. It helps developers and administrators monitor node versions over time by keeping a structured record of version changes.

## Features

- Scans n8n repository for node files (.node.ts)
- Extracts version information using regex patterns
- Tracks both single versions and version arrays
- Saves results in structured JSON format
- Records version change history
- Supports weekly automated scanning

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install requests
```
3. Create a config.json file with:
```json
{
  "github_token": "YOUR_GITHUB_TOKEN"
}
```

## Usage

Run the scanner:
```bash
python main.py
```

The script will:
- Scan all .node.ts files in n8n repository
- Extract version information
- Save results to node_versions.json
- Track changes in version_changes.json
- Schedule weekly automated scans

## Output Format

Results are saved in JSON format:
```json
{
  "NodeName": {
    "path": "path/to/node.ts",
    "version_info": {
      "version": 1.0,
      "is_multi_version": false,
      "last_updated": "timestamp"
    }
  }
}
```

## License

MIT

## Contributing

Issues and pull requests welcome via GitHub.
