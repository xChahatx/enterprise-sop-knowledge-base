"""
Version Manager Module
Maintains document versions, metadata, and chunk-level access control.

Responsibilities:
    1. Track document versions using file hash (detect duplicates)
    2. Manage document metadata (department, access_level, document_type, etc.)
    3. Register chunks for each version (chunk → version mapping)
    4. Support document comparisons across versions
    5. Enable audit trails for access control

Storage:
    - versions.json  → document version history
    - registry.json  → full document metadata + chunk index
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
from config.settings import (
    DEPARTMENTS,
    DEFAULT_DEPARTMENT_OWNER,
    DOCUMENT_TYPES
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VersionManager:
    """
    Comprehensive version and metadata management for SOP documents.

    Two storage files:
        1. versions.json  → version history (lightweight)
        2. registry.json  → full metadata + chunk index (comprehensive)

    Design:
        versions.json is fast lookup for version conflicts.
        registry.json is the source of truth for all document metadata.
    """

    def __init__(self, version_file: str = "data/versions.json", registry_file: str = "data/registry.json"):
        """
        Args:
            version_file (str): Path to version history file.
            registry_file (str): Path to comprehensive document registry.
        """
        self.version_file = Path(version_file)
        self.registry_file = Path(registry_file)

        # Create directories
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize files if needed
        if not self.version_file.exists():
            self.version_file.write_text("{}", encoding="utf-8")

        if not self.registry_file.exists():
            self.registry_file.write_text("{}", encoding="utf-8")

        self._load()
        logger.info("VersionManager initialized")

    # --------------------------------------------------------------------------
    # INTERNAL: FILE I/O
    # --------------------------------------------------------------------------

    def _load(self) -> None:
        """Load both version and registry files into memory."""
        try:
            with open(self.version_file, "r", encoding="utf-8") as f:
                self.versions = json.load(f)
            with open(self.registry_file, "r", encoding="utf-8") as f:
                self.registry = json.load(f)
            logger.info(f"Loaded {len(self.registry)} documents from registry")
        except Exception as e:
            logger.error(f"Error loading version files: {e}")
            raise

    def _save(self) -> None:
        """Save both files to disk."""
        try:
            with open(self.version_file, "w", encoding="utf-8") as f:
                json.dump(self.versions, f, indent=2)
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2)
            logger.debug("Version files saved")
        except Exception as e:
            logger.error(f"Error saving version files: {e}")
            raise

    # --------------------------------------------------------------------------
    # DUPLICATE DETECTION
    # --------------------------------------------------------------------------

    def document_exists(self, file_hash: str) -> bool:
        """
        Check if a document with this hash already exists.

        Used to detect duplicate uploads.

        Args:
            file_hash (str): MD5 hash of file content.

        Returns:
            bool: True if file hash already in system.
        """
        for doc_record in self.registry.values():
            for version_record in doc_record.get("versions", []):
                if version_record["file_hash"] == file_hash:
                    logger.debug(f"Found existing hash: {file_hash[:8]}...")
                    return True
        return False

    # --------------------------------------------------------------------------
    # VERSION MANAGEMENT
    # --------------------------------------------------------------------------

    def get_latest_version(self, filename: str) -> int:
        """
        Get the latest version number for a document.

        Args:
            filename (str): Document filename (e.g., "hr_policy.pdf").

        Returns:
            int: Latest version number, or 0 if document is new.
        """
        if filename not in self.registry:
            return 0

        versions = self.registry[filename].get("versions", [])
        if not versions:
            return 0

        return max(v["version"] for v in versions)

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict]:
        """
        Retrieve document record by file hash.

        Useful for checking if uploaded file is a reupload.

        Args:
            file_hash (str): MD5 hash of file.

        Returns:
            Dict: Document record if found, None otherwise.
        """
        for filename, doc_record in self.registry.items():
            for version_record in doc_record.get("versions", []):
                if version_record["file_hash"] == file_hash:
                    return {
                        "filename": filename,
                        "version": version_record["version"],
                        "document_record": doc_record
                    }
        return None

    # --------------------------------------------------------------------------
    # DOCUMENT REGISTRATION
    # --------------------------------------------------------------------------

    def register_document(
        self,
        metadata: Dict,
        access_level: str = "INTERNAL",
        departments: List[str] = None,
        department_owner: Optional[str] = None,
        document_type: str = "SOP",
        uploaded_by: str = "System",
        language: str = "English"
    ) -> Dict:
        """
        Register a new document version in the system.

        Creates or updates document record with full metadata.
        Marks previous version as "archived".
        Returns updated metadata with version info.

        Args:
            metadata (Dict): Base metadata from doc_parser.
                Must contain: filename, file_hash, file_size_kb, num_pages, total_characters
            access_level (str): Access restriction level.
                Examples: "PUBLIC", "INTERNAL", "CONFIDENTIAL", "EXTERNAL"
            departments (List[str]): Departments responsible for SOP.
                Examples: ["HR"], ["FINANCE"], ["ENGINEERING"]
            department_owner (str): Owner of the department responsible for the document.
            document_type (str): Type of document.
                Examples: "SOP", "POLICY", "GUIDELINE", "MANUAL"
            uploaded_by (str): User/system that uploaded this version.
            language (str): Language of the document.

        Returns:
            Dict: Enhanced metadata with:
                - version (int)
                - created_at (str)
                - status (str) — "active" or "archived"
                - access_level (str)
                - departments (List[str])
                - department_owner (str)
                - document_type (str)
        """
        filename = metadata["filename"]
        file_hash = metadata["file_hash"]
        if departments is None:
            departments = DEPARTMENTS
        elif not isinstance(departments, list):
            departments = [departments]
        departments = [
            dept for dept in departments
            if dept in DEPARTMENTS
        ]
        if not departments:
            departments = DEPARTMENTS
        if department_owner is None:
            department_owner = DEFAULT_DEPARTMENT_OWNER
        if document_type not in DOCUMENT_TYPES:
            document_type = "SOP"

        logger.info(f"Registering document: {filename} | access_level: {access_level}")

        # Calculate new version number
        new_version = self.get_latest_version(filename) + 1

        # Timestamp
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ensure document entry exists
        if filename not in self.registry:
            self.registry[filename] = {
                "filename": filename,
                "document_type": document_type,
                "departments": departments,
                "department_owner": department_owner,
                "versions": []
            }

        # Mark previous active version as archived
        doc_record = self.registry[filename]
        doc_record["document_type"] = document_type
        doc_record["departments"] = departments
        doc_record["department_owner"] = department_owner


        for version_record in doc_record.get("versions", []):
            if version_record["status"] == "active":
                version_record["status"] = "archived"
                logger.info(f"Archived previous version: {version_record['version']}")

        # Create new version record
        version_record = {
            "version": new_version,
            "file_hash": file_hash,
            "created_at": created_at,
            "uploaded_by": uploaded_by,
            "status": "active",
            "access_level": access_level,
            "departments": departments,
            "department_owner": department_owner,
            "language": language,
            "document_type": document_type,
            "file_size_kb": metadata.get("file_size_kb"),
            "num_pages": metadata.get("num_pages"),
            "total_characters": metadata.get("total_characters")
        }

        doc_record["versions"].append(version_record)

        # Also maintain fast lookup in versions.json
        if filename not in self.versions:
            self.versions[filename] = []

        # Mark old versions
        for v in self.versions[filename]:
            if v["status"] == "active":
                v["status"] = "archived"

        self.versions[filename].append({
            "version": new_version,
            "file_hash": file_hash,
            "created_at": created_at,
            "status": "active"
        })

        self._save()

        # Return enhanced metadata
        enhanced_metadata = {
            **metadata,
            "version": new_version,
            "created_at": created_at,
            "status": "active",
            "access_level": access_level,
            "departments": departments,
            "document_type": document_type,
            "uploaded_by": uploaded_by,
            "language": language,
            "department_owner": department_owner
        }
        logger.info(
            f"Registered {filename} "
            f"v{new_version} | "
            f"type={document_type} | "
            f"access={access_level} | "
            f"departments={departments} | "
            f"owner={department_owner}"
        )

        return enhanced_metadata

    # --------------------------------------------------------------------------
    # CHUNK REGISTRATION
    # --------------------------------------------------------------------------

    def register_chunks_for_version(
        self,
        filename: str,
        version: int,
        chunk_ids: List[str],
        chunk_count: int
    ) -> None:
        """
        Register chunks that belong to a specific document version.

        Creates mapping: version → list of chunk IDs.
        Enables version comparison and chunk cleanup.

        Args:
            filename (str): Document filename.
            version (int): Version number.
            chunk_ids (List[str]): List of chunk IDs from this version.
            chunk_count (int): Total number of chunks.
        """
        if filename not in self.registry:
            logger.warning(f"Document {filename} not in registry. Register first!")
            return

        doc_record = self.registry[filename]



        # Find the version record
        version_record = None
        for v in doc_record["versions"]:
            if v["version"] == version:
                version_record = v
                break

        if not version_record:
            logger.error(f"Version {version} not found for {filename}")
            return

        # Add chunk index
        version_record["chunks"] = {
            "count": chunk_count,
            "first_chunk": chunk_ids[0],
            "last_chunk": chunk_ids[-1],
            "indexed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indexed": True
        }

        self._save()

        logger.info(f"Registered {chunk_count} chunks for {filename} v{version}")

    # --------------------------------------------------------------------------
    # QUERIES
    # --------------------------------------------------------------------------

    def get_document_info(self, filename: str) -> Optional[Dict]:
        """
        Get full information about a document.

        Args:
            filename (str): Document filename.

        Returns:
            Dict: Document record with all versions, or None if not found.
        """
        if filename not in self.registry:
            return None

        return self.registry[filename]

    def get_active_version_info(self, filename: str) -> Optional[Dict]:
        """
        Get metadata for the currently active version.

        Args:
            filename (str): Document filename.

        Returns:
            Dict: Active version record, or None if document not found.
        """
        if filename not in self.registry:
            return None

        doc_record = self.registry[filename]
        for version_record in doc_record.get("versions", []):
            if version_record["status"] == "active":
                return {
                    "filename": filename,
                    **version_record,
                    "document_type": doc_record.get("document_type"),
                    "departments": doc_record.get("departments"),
                    "department_owner": doc_record.get("department_owner")
                }

        return None
    def get_latest_versions(self) -> Dict[str, int]:
        """
        Returns the latest ACTIVE version number for every document.
        """
        latest_versions = {}
        for filename, doc_record in self.registry.items():
            for version in doc_record.get("versions", []):
                if version["status"] == "active":
                    latest_versions[filename] = version["version"]
                    break
        return latest_versions

    def list_all_documents(self) -> List[Dict]:
        """
        List all documents with their active version info.

        Returns:
            List[Dict]: Summary of all documents in the system.
        """
        documents = []

        for filename, doc_record in self.registry.items():
            active_version = self.get_active_version_info(filename)
            if not active_version:
                continue
            documents.append({
                "filename": filename,
                "document_type": doc_record.get("document_type"),
                "departments": doc_record.get("departments"),
                "department_owner": doc_record.get("department_owner"),
                "version": active_version["version"],
                "access_level": active_version.get("access_level"),
                "created_at": active_version.get("created_at"),
                "chunk_count": active_version.get(
                    "chunks", {}
                ).get("count", 0),

                "has_previous_versions":
                    len(doc_record.get("versions", [])) > 1,
                "total_versions":
                    len(doc_record.get("versions", []))
            })
        return documents



    def get_version_history(self, filename: str) -> List[Dict]:
        """
        Get complete version history for a document.

        Useful for "View All Versions" feature.

        Args:
            filename (str): Document filename.

        Returns:
            List[Dict]: All versions in chronological order.
        """
        if filename not in self.registry:
            return []

        doc_record = self.registry[filename]
        return doc_record.get("versions", [])

    # --------------------------------------------------------------------------
    # AUTHORIZATION QUERIES
    # --------------------------------------------------------------------------

    def get_chunk_access_level(self, filename: str, version: int) -> str:
        """
        Get the access level for a specific document version.

        All chunks from a version inherit this access level.

        Args:
            filename (str): Document filename.
            version (int): Version number.

        Returns:
            str: Access level (e.g., "PUBLIC", "INTERNAL").
        """
        if filename not in self.registry:
            return "UNKNOWN"

        doc_record = self.registry[filename]
        for v in doc_record.get("versions", []):
            if v["version"] == version:
                return v.get("access_level", "INTERNAL")

        return "UNKNOWN"

    def get_authorized_documents(self, user_access_level: str) -> List[str]:
        """
        Get list of documents a user can access based on their access level.

        Rules:
            - "PUBLIC" docs accessible to everyone
            - "INTERNAL" docs accessible to internal users
            - "CONFIDENTIAL" docs accessible to authorized users only
            - "EXTERNAL" docs accessible to external partners

        Args:
            user_access_level (str): User's authorization level.

        Returns:
            List[str]: Filenames user can access.
        """
        authorized = []

        hierarchy = {
            "PUBLIC": ["PUBLIC"],
            "INTERNAL": ["PUBLIC", "INTERNAL"],
            "CONFIDENTIAL": ["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
            "EXTERNAL": ["PUBLIC", "EXTERNAL"]
        }

        allowed_levels = hierarchy.get(user_access_level, ["PUBLIC"])

        for filename, doc_record in self.registry.items():
            # Get active version
            for v in doc_record.get("versions", []):
                if v["status"] == "active":
                    doc_access = v.get("access_level", "INTERNAL")
                    if doc_access in allowed_levels:
                        authorized.append({
                            "filename": filename,
                            "access_level": doc_access,
                            "departments": doc_record.get("departments"),
                            "department_owner": doc_record.get("department_owner"),
                        })
                    break

        return authorized

    # --------------------------------------------------------------------------
    # DOCUMENT COMPARISON
    # --------------------------------------------------------------------------

    def compare_versions(self, filename: str, v1: int, v2: int) -> Dict:
        """
        Compare two versions of a document.

        Returns metadata differences.

        Args:
            filename (str): Document filename.
            v1 (int): First version number.
            v2 (int): Second version number.

        Returns:
            Dict: Differences between versions.
        """
        if filename not in self.registry:
            return {"error": "Document not found"}

        doc_record = self.registry[filename]
        version_records = {v["version"]: v for v in doc_record.get("versions", [])}

        if v1 not in version_records or v2 not in version_records:
            return {"error": "One or both versions not found"}

        v1_record = version_records[v1]
        v2_record = version_records[v2]

        comparison = {
            "filename": filename,
            "v1": v1,
            "v2": v2,
            "differences": {
                "file_hash": v1_record["file_hash"] != v2_record["file_hash"],
                "access_level": v1_record.get("access_level") != v2_record.get("access_level"),
                "chunk_count": (
                    v1_record.get("chunks", {}).get("count") !=
                    v2_record.get("chunks", {}).get("count")
                ),
                "document_type": v1_record.get("document_type") != v2_record.get("document_type"),
                "departments": v1_record.get("departments") != v2_record.get("departments"),
                "department_owner": v1_record.get("department_owner") != v2_record.get("department_owner"),
                "language": v1_record.get("language") != v2_record.get("language"),


                "uploaded_by": v1_record.get("uploaded_by") != v2_record.get("uploaded_by")
            }
        }

        return comparison
    def get_documents_by_department(self, department: str) -> List[Dict]:
        """
        Return all documents belonging to a department.
        """
        results = []
        for filename, doc in self.registry.items():
            if department in doc.get("departments", []):
                results.append({
                    "filename": filename,
                    "document_type": doc.get("document_type"),
                    "department_owner": doc.get("department_owner"),
                    "departments": doc.get("departments"),
                    "versions": len(doc.get("versions", []))
                })
        return results
    
    def get_document_owner(self, filename: str) -> Optional[str]:
        if filename not in self.registry:
            return None
        return self.registry[filename].get("department_owner")
    def get_authorized_filenames(
            self,
            user_access_level: str
    ) -> List[str]:
        """
        Returns only the filenames the current user
        is allowed to search.
        """
        filenames = []
        authorized_documents = self.get_authorized_documents(
            user_access_level
        )
        for document in authorized_documents:
            filenames.append(
                document["filename"]
            )
        return filenames
    def get_active_documents(self) -> List[str]:
        """
        Returns filenames whose latest version is ACTIVE.
        """
        active_documents = []
        for filename, document in self.registry.items():

            for version in document.get("versions", []):

                if version.get("status") == "active":

                    active_documents.append(filename)

                    break

        return active_documents


    def is_latest_active_version(
        self,
        filename: str,
        version: int
    ) -> bool:
        """
        Checks whether a chunk belongs to the latest active version.
        """

        if filename not in self.registry:
            return False

        for record in self.registry[filename].get("versions", []):

            if (
                record["version"] == version
                and record["status"] == "active"
            ):
                return True

        return False