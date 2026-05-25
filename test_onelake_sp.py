"""
Test script: upload and download a file to OneLake using a Service Principal.

Required environment variables:
    FABRIC_WORKSPACE_ID   - Fabric workspace GUID
    FABRIC_LAKEHOUSE_ID   - Fabric lakehouse GUID
    AZURE_TENANT_ID       - Entra tenant ID
    AZURE_CLIENT_ID       - Service principal (app) client ID
    AZURE_CLIENT_SECRET   - Service principal client secret

Optional environment variables:
    FABRIC_BASE_FOLDER    - Base path under lakehouse (default: Files/sample)
    FABRIC_INBOX_FOLDER   - Inbox folder name under base (default: inbox)
    FABRIC_OUTBOX_FOLDER  - Outbox folder name under base (default: outbox)
    FABRIC_PAUSE_UPLOAD   - Pause after upload/copy before downloads (default: false)
    FABRIC_PAUSE_CLEANUP  - Pause before cleanup step (default: false)
    FABRIC_ENABLE_CLEANUP - Delete sp_test files at end of run (default: false)

The service principal must have the Contributor role on the Fabric workspace
(or at minimum Storage Blob Data Contributor on the OneLake resource).

Usage:
    python test_onelake_sp.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential
from sample_fabric.onelake_io import OneLakeScopedBlobIO


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"ERROR: environment variable '{name}' is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def _optional_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def _optional_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _pause_if_enabled(enabled: bool, message: str) -> None:
    if not enabled:
        return
    try:
        input(f"\n[pause] {message}\nPress Enter to continue...")
    except EOFError:
        # Non-interactive environment; continue without blocking.
        print("\n[pause] Input unavailable; continuing.")


def _build_client() -> tuple[OneLakeScopedBlobIO, str, str]:
    tenant_id = _require_env("AZURE_TENANT_ID")
    client_id = _require_env("AZURE_CLIENT_ID")
    client_secret = _require_env("AZURE_CLIENT_SECRET")
    workspace_id = _require_env("FABRIC_WORKSPACE_ID")
    lakehouse_id = _require_env("FABRIC_LAKEHOUSE_ID")
    base_folder = _optional_env("FABRIC_BASE_FOLDER", "Files/sample")
    inbox_folder = _optional_env("FABRIC_INBOX_FOLDER", "inbox")
    outbox_folder = _optional_env("FABRIC_OUTBOX_FOLDER", "outbox")

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )

    client = OneLakeScopedBlobIO(
        workspace_id=workspace_id,
        lakehouse_id=lakehouse_id,
        base_folder=base_folder,
        allowed_folders=(inbox_folder, outbox_folder),
        credential=credential,
    )
    return client, inbox_folder, outbox_folder


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_write_and_read_text(client: OneLakeScopedBlobIO, inbox_folder: str) -> None:
    print("\n[1] write_text / read_text ...")
    content = "hello from service principal\nline 2\n"
    blob_name = client.write_text(inbox_folder, "sp_test/hello.txt", content)
    print(f"    written -> {blob_name}")

    result = client.read_text(inbox_folder, "sp_test/hello.txt")
    assert result == content, f"content mismatch: {result!r}"
    print("    read back OK")


def test_upload_and_download_file(
    client: OneLakeScopedBlobIO,
    inbox_folder: str,
    outbox_folder: str,
    pause_after_upload: bool = False,
) -> None:
    print("\n[2] create data/*.txt -> upload to inbox -> copy to outbox -> download to data/download ...")

    local_data_dir = Path("data")
    local_download_dir = local_data_dir / "download"
    local_data_dir.mkdir(parents=True, exist_ok=True)
    local_download_dir.mkdir(parents=True, exist_ok=True)

    sample_files = {
        "customer_profile.txt": "Customer: Contoso\nSegment: Enterprise\nStatus: Active\n",
        "invoice_notes.txt": "Invoice: INV-10021\nAmount: 1250.75\nCurrency: USD\n",
        "shipment_update.txt": "Shipment: SHP-7782\nETA: 2026-05-28\nState: In Transit\n",
    }

    uploaded_pairs: list[tuple[str, str]] = []
    for filename, content in sample_files.items():
        local_src = local_data_dir / filename
        local_src.write_text(content, encoding="utf-8")

        inbox_relative = f"sp_test/inbox_uploaded_{filename}"
        blob_name = client.upload_file(inbox_folder, str(local_src), target_name=inbox_relative)
        print(f"    uploaded to {inbox_folder} -> {blob_name}")
        uploaded_pairs.append((filename, inbox_relative))

    for filename, inbox_relative in uploaded_pairs:
        copied_content = client.read_text(inbox_folder, inbox_relative)
        outbox_relative = f"sp_test/outbox_copied_{filename}"
        try:
            outbox_blob = client.write_text(outbox_folder, outbox_relative, copied_content)
        except HttpResponseError as exc:
            if getattr(exc, "error_code", "") == "Forbidden":
                raise PermissionError(
                    f"Write forbidden for outbox folder '{outbox_folder}'. "
                    f"Either grant access to Files/{outbox_folder} or set FABRIC_OUTBOX_FOLDER to a writable folder (for example, '{inbox_folder}')."
                ) from exc
            raise
        print(f"    copied to {outbox_folder} -> {outbox_blob}")

    _pause_if_enabled(
        pause_after_upload,
        "Uploads/copies completed. Inspect inbox/outbox now if needed.",
    )

    outbox_blobs = client.list_files(outbox_folder)
    outbox_marker = f"/{outbox_folder}/"
    outbox_test_relatives: list[str] = []
    for blob_name in outbox_blobs:
        if outbox_marker not in blob_name:
            continue
        relative = blob_name.split(outbox_marker, 1)[1]
        if relative.startswith("sp_test/"):
            outbox_test_relatives.append(relative)

    if not outbox_test_relatives:
        raise AssertionError("No sp_test files found in outbox for download verification")

    for relative in sorted(outbox_test_relatives):
        local_target = local_download_dir / Path(relative).name
        client.download_file(outbox_folder, relative, str(local_target))
        downloaded_text = local_target.read_text(encoding="utf-8")
        assert downloaded_text, f"downloaded file is empty: {local_target}"
        print(f"    downloaded from {outbox_folder} -> {local_target}")


def test_exists_and_delete(client: OneLakeScopedBlobIO, outbox_folder: str) -> None:
    print("\n[3] exists / delete ...")
    client.write_text(outbox_folder, "sp_test/temp.txt", "temporary")

    assert client.exists(outbox_folder, "sp_test/temp.txt"), "file should exist after write"
    print("    exists -> True OK")

    client.delete_file(outbox_folder, "sp_test/temp.txt")
    assert not client.exists(outbox_folder, "sp_test/temp.txt"), "file should be gone after delete"
    print("    exists after delete -> False OK")


def test_list_files(client: OneLakeScopedBlobIO, inbox_folder: str) -> None:
    print("\n[4] list_files ...")
    files = client.list_files(inbox_folder)
    print(f"    found {len(files)} blob(s) under {inbox_folder}:")
    for name in files:
        print(f"      {name}")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup(client: OneLakeScopedBlobIO, inbox_folder: str, outbox_folder: str) -> None:
    print("\n[cleanup] removing test blobs ...")
    for folder in [inbox_folder, outbox_folder]:
        marker = f"/{folder}/"
        try:
            folder_blobs = client.list_files(folder)
        except Exception:
            continue

        for blob_name in folder_blobs:
            if marker not in blob_name:
                continue
            relative = blob_name.split(marker, 1)[1]
            if not relative.startswith("sp_test/"):
                continue
            try:
                client.delete_file(folder, relative)
                print(f"    deleted {folder}/{relative}")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    load_dotenv()
    client, inbox_folder, outbox_folder = _build_client()
    pause_after_upload = _optional_env_bool("FABRIC_PAUSE_UPLOAD", False)
    pause_before_cleanup = _optional_env_bool("FABRIC_PAUSE_CLEANUP", False)
    enable_cleanup = _optional_env_bool("FABRIC_ENABLE_CLEANUP", False)
    print(f"Connected. Workspace: {client.workspace_id}  Lakehouse: {client.lakehouse_id}")
    print(
        f"Using base folder '{client.base_folder}' with inbox '{inbox_folder}' and outbox '{outbox_folder}'"
    )

    try:
        test_write_and_read_text(client, inbox_folder)
        test_upload_and_download_file(
            client,
            inbox_folder,
            outbox_folder,
            pause_after_upload=pause_after_upload,
        )
        test_exists_and_delete(client, outbox_folder)
        test_list_files(client, inbox_folder)
    finally:
        if enable_cleanup:
            _pause_if_enabled(
                pause_before_cleanup,
                "Cleanup is about to run and delete sp_test files from inbox/outbox.",
            )
            cleanup(client, inbox_folder, outbox_folder)
        else:
            print("\n[cleanup] skipped (set FABRIC_ENABLE_CLEANUP=true to delete sp_test files)")

    print("\nAll tests passed.")
