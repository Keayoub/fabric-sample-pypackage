"""
Scoped OneLake file I/O helpers using OneLake's Blob-compatible endpoint.

This client intentionally enforces an allowed prefix to reduce accidental
access beyond intended folders (for example: Files/sample/inbox and outbox).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class OneLakeScopedBlobIO:
    """
    Scoped file I/O client for OneLake Blob API.

    OneLake blob URL pattern:
    https://onelake.blob.fabric.microsoft.com/{workspace_id}/{lakehouse_id}/<path>

    Scope behavior:
    - `base_folder` limits all operations to a known root (default: Files/sample)
    - `allowed_folders` limits first-level folders under base (default: inbox/outbox)
    """

    def __init__(
        self,
        workspace_id: str,
        lakehouse_id: str,
        base_folder: str = "Files/sample",
        allowed_folders: Optional[Iterable[str]] = None,
        credential: Optional[DefaultAzureCredential] = None,
        account_url: str = "https://onelake.blob.fabric.microsoft.com",
    ) -> None:
        self.workspace_id = workspace_id.strip("/")
        self.lakehouse_id = lakehouse_id.strip("/")
        self.base_folder = self._normalize_path(base_folder).strip("/")
        self.allowed_folders = {
            part.strip("/")
            for part in (allowed_folders or ("inbox", "outbox"))
            if part and part.strip("/")
        }

        if not self.allowed_folders:
            raise ValueError("allowed_folders cannot be empty")

        self.credential = credential or DefaultAzureCredential()
        self.service_client = BlobServiceClient(account_url=account_url, credential=self.credential)
        self.container_client = self.service_client.get_container_client(self.workspace_id)

    @classmethod
    def from_environment(
        cls,
        base_folder: str = "Files/sample",
        allowed_folders: Optional[Iterable[str]] = None,
    ) -> "OneLakeScopedBlobIO":
        """
        Build the client from environment variables.

        Required environment variables:
        - FABRIC_WORKSPACE_ID
        - FABRIC_LAKEHOUSE_ID
        """
        workspace_id = os.getenv("FABRIC_WORKSPACE_ID")
        lakehouse_id = os.getenv("FABRIC_LAKEHOUSE_ID")

        if not workspace_id or not lakehouse_id:
            raise ValueError(
                "FABRIC_WORKSPACE_ID and FABRIC_LAKEHOUSE_ID must be set in the environment"
            )

        return cls(
            workspace_id=workspace_id,
            lakehouse_id=lakehouse_id,
            base_folder=base_folder,
            allowed_folders=allowed_folders,
        )

    def list_files(self, folder: str) -> List[str]:
        """List blob names under one allowed folder."""
        prefix = self._prefix_for_folder(folder)
        names: List[str] = []
        for blob in self.container_client.list_blobs(name_starts_with=prefix):
            names.append(blob.name)
        return names

    def write_text(
        self,
        folder: str,
        relative_path: str,
        content: str,
        overwrite: bool = True,
        encoding: str = "utf-8",
    ) -> str:
        """Write UTF-8 text content to a scoped blob path."""
        blob_name = self._build_blob_name(folder, relative_path)
        blob_client = self.container_client.get_blob_client(blob_name)
        blob_client.upload_blob(content.encode(encoding), overwrite=overwrite)
        return blob_name

    def read_text(self, folder: str, relative_path: str, encoding: str = "utf-8") -> str:
        """Read text content from a scoped blob path."""
        blob_name = self._build_blob_name(folder, relative_path)
        blob_client = self.container_client.get_blob_client(blob_name)
        return blob_client.download_blob().readall().decode(encoding)

    def upload_file(
        self,
        folder: str,
        local_path: str,
        target_name: Optional[str] = None,
        overwrite: bool = True,
    ) -> str:
        """Upload a local file into a scoped folder."""
        file_path = Path(local_path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Local file does not exist: {local_path}")

        relative_name = target_name or file_path.name
        blob_name = self._build_blob_name(folder, relative_name)
        blob_client = self.container_client.get_blob_client(blob_name)

        with file_path.open("rb") as data:
            blob_client.upload_blob(data, overwrite=overwrite)

        return blob_name

    def download_file(self, folder: str, relative_path: str, local_path: str) -> str:
        """Download a scoped blob to a local file path."""
        blob_name = self._build_blob_name(folder, relative_path)
        blob_client = self.container_client.get_blob_client(blob_name)

        target = Path(local_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as stream:
            stream.write(blob_client.download_blob().readall())

        return str(target)

    def delete_file(self, folder: str, relative_path: str) -> None:
        """Delete a scoped blob path."""
        blob_name = self._build_blob_name(folder, relative_path)
        self.container_client.delete_blob(blob_name)

    def exists(self, folder: str, relative_path: str) -> bool:
        """Check whether a scoped blob exists."""
        blob_name = self._build_blob_name(folder, relative_path)
        return self.container_client.get_blob_client(blob_name).exists()

    def _prefix_for_folder(self, folder: str) -> str:
        folder_clean = self._validate_allowed_folder(folder)
        return f"{self.lakehouse_id}/{self.base_folder}/{folder_clean}/"

    def _build_blob_name(self, folder: str, relative_path: str) -> str:
        folder_clean = self._validate_allowed_folder(folder)
        cleaned_relative = self._normalize_relative_path(relative_path)
        return f"{self.lakehouse_id}/{self.base_folder}/{folder_clean}/{cleaned_relative}"

    def _validate_allowed_folder(self, folder: str) -> str:
        candidate = self._normalize_path(folder).strip("/")
        if candidate not in self.allowed_folders:
            allowed = ", ".join(sorted(self.allowed_folders))
            raise PermissionError(
                f"Folder '{folder}' is outside allowed scope. Allowed values: {allowed}"
            )
        return candidate

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.replace("\\", "/")

    @staticmethod
    def _normalize_relative_path(path: str) -> str:
        normalized = path.replace("\\", "/").strip("/")
        parts = [part for part in normalized.split("/") if part and part != "."]
        if not parts:
            raise ValueError("relative_path cannot be empty")
        if any(part == ".." for part in parts):
            raise ValueError("relative_path cannot traverse parent directories")
        return "/".join(parts)
