# Sample Python Package for Microsoft Fabric

A minimal Python package designed to run on Microsoft Fabric runtime.

## Description

This package demonstrates a simple Python application that can be deployed and executed in Microsoft Fabric environment. It provides basic functionality to display messages and showcase package structure.

## Features

- Minimal dependencies for Fabric runtime compatibility
- Simple message display functionality
- Proper package structure for distribution
- Console entry point for easy execution

## Installation

```bash
pip install -e .
```

## Usage

After installation, you can run the package using:

```bash
sample-fabric
```

Or import it in your Python code:

```python
from sample_fabric import display_message, get_fabric_info
display_message("Hello from Fabric!")
```

### Scoped OneLake File I/O (Blob API)

This package includes `OneLakeScopedBlobIO`, a helper class for OneLake Blob API access with code-level folder scope enforcement.

Your scenario maps to these defaults:

- Base folder: `Files/sample`
- Allowed folders: `inbox`, `outbox`

```python
from sample_fabric import OneLakeScopedBlobIO

client = OneLakeScopedBlobIO(
    workspace_id="f9c754ab-fb1f-420b-a466-69cbb21ea6cf",
    lakehouse_id="fea2bc2c-7a62-4bae-8333-ef692a29ff40",
    base_folder="Files/sample",
    allowed_folders=("inbox", "outbox"),
)

# Write to Files/sample/inbox/sample.txt
client.write_text("inbox", "sample.txt", "hello from external app")

# Read from Files/sample/outbox/result.txt
text = client.read_text("outbox", "result.txt")
print(text)
```

Environment-based creation:

```python
import os
from sample_fabric import OneLakeScopedBlobIO

os.environ["FABRIC_WORKSPACE_ID"] = "f9c754ab-fb1f-420b-a466-69cbb21ea6cf"
os.environ["FABRIC_LAKEHOUSE_ID"] = "fea2bc2c-7a62-4bae-8333-ef692a29ff40"

client = OneLakeScopedBlobIO.from_environment(
    base_folder="Files/sample",
    allowed_folders=("inbox", "outbox"),
)
```

Permission notes:

- The code enforces folder scope, but Fabric/OneLake authorization is still controlled by workspace roles and OneLake security roles.
- For least-visibility setup, use OneLake security roles with `ReadWrite` on the target folder(s) and avoid broad workspace access where possible.
- There is no native write-only path role; `ReadWrite` includes read permissions on the granted folder.

## Fabric Runtime Compatibility

This package is designed to work with Microsoft Fabric runtime environments with minimal external dependencies to ensure reliable execution.

## License

MIT License
