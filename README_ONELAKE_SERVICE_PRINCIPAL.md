# Microsoft Fabric OneLake Access via Service Principal (Python)

This guide explains how to connect to **Microsoft Fabric OneLake** from Python using a **Service Principal** and standard **Azure Blob / ADLS Gen2-compatible APIs**.

It is written for newcomers and follows a **minimal-privileges** approach.

## 1) Why this works

OneLake exposes endpoints compatible with Azure Storage APIs. In Python, you can authenticate with Microsoft Entra ID and use Azure SDK clients (for example, `azure-storage-blob`) against the OneLake endpoint.

In this repository, `OneLakeScopedBlobIO` is the helper that wraps this flow and adds folder scoping in code.

## 2) Minimal-privileges model

Use the smallest scope that can do the job:

- Prefer granting the Service Principal access only to the target folder(s) in OneLake.
- Avoid broad workspace permissions when folder-level permissions are enough.
- Scope application behavior in code (`base_folder` + `allowed_folders`) so accidental writes outside approved locations are blocked.

> Note: The project helper enforces folder boundaries in code. Actual authorization is still enforced by Fabric/OneLake permissions.

## 3) Prerequisites

1. A Fabric workspace and lakehouse.
2. A Microsoft Entra application (Service Principal) with:
   - `AZURE_TENANT_ID`
   - `AZURE_CLIENT_ID`
   - `AZURE_CLIENT_SECRET`
3. OneLake permissions for that Service Principal on the required folder(s) (read-only or read/write depending on your use case).
4. Python dependencies installed:

```bash
pip install -e .
```

## 4) Authentication flow (Service Principal)

1. Python app loads tenant/client/secret.
2. App creates `ClientSecretCredential` from `azure.identity`.
3. Credential requests a token for Azure Storage-compatible access.
4. Storage client uses the token to call OneLake endpoints.
5. OneLake authorizes the request according to Fabric/OneLake permissions.

## 5) API access flow (Blob / ADLS Gen2 compatible)

Typical sequence:

1. Build a OneLake client with workspace/lakehouse IDs.
2. Restrict operations to an approved base path (`Files/sample`) and approved subfolders (`inbox`, `outbox`).
3. Perform standard operations (upload, read, list, delete) via Azure-compatible calls.
4. Handle `403 Forbidden` as a permissions issue (scope too narrow or missing folder grant).

## 6) Sample connection flow (Python)

```python
from azure.identity import ClientSecretCredential
from sample_fabric.onelake_io import OneLakeScopedBlobIO

credential = ClientSecretCredential(
    tenant_id="<tenant-id>",
    client_id="<client-id>",
    client_secret="<client-secret>",
)

client = OneLakeScopedBlobIO(
    workspace_id="<workspace-guid>",
    lakehouse_id="<lakehouse-guid>",
    base_folder="Files/sample",
    allowed_folders=("inbox", "outbox"),
    credential=credential,
)

# Write then read
client.write_text("inbox", "hello.txt", "hello from service principal")
print(client.read_text("inbox", "hello.txt"))
```

Environment-variable variant:

```python
import os
from sample_fabric.onelake_io import OneLakeScopedBlobIO

os.environ["FABRIC_WORKSPACE_ID"] = "<workspace-guid>"
os.environ["FABRIC_LAKEHOUSE_ID"] = "<lakehouse-guid>"

client = OneLakeScopedBlobIO.from_environment(
    base_folder="Files/sample",
    allowed_folders=("inbox", "outbox"),
)
```

For an end-to-end sample script, see:

- `test_onelake_sp.py`

## 7) Security considerations

- Store secrets outside source code (environment variables, secret vaults, CI secret stores).
- Rotate client secrets regularly.
- Use separate Service Principals per environment (dev/test/prod).
- Grant least privilege first, then expand only if required.
- Keep folder scoping in both permission model and code.
- Log access failures without printing secrets or tokens.

## 8) Usage notes and troubleshooting

- `403 Forbidden`: Usually means the Service Principal lacks permission for the specific folder/action.
- Read vs write: ensure the granted permission level matches the operation.
- Wrong IDs: verify workspace and lakehouse GUIDs.
- Path mismatches: confirm `base_folder`, `inbox`, and `outbox` align with your lakehouse structure.

## 9) Quick run checklist

1. Set environment variables (`AZURE_*`, `FABRIC_*`).
2. Confirm folder-level access in OneLake.
3. Run `python test_onelake_sp.py`.
4. Validate read/write/list behavior in your scoped folders.

## 10) References

- [Access OneLake with Python](https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-python)
- [How do I connect to OneLake?](https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api)
- [Microsoft OneLake documentation](https://learn.microsoft.com/en-us/fabric/onelake/)
- [Authentication in Python with Azure Identity](https://learn.microsoft.com/en-us/azure/developer/python/sdk/identity/)
- [Azure Storage Python SDK documentation](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)

This approach keeps OneLake access aligned with standard Azure SDK patterns while preserving least-privilege boundaries.
