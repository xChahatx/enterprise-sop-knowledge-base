"""
Test Version Manager
"""

from src.version_manager import VersionManager


def main():

    print("=" * 60)
    print("MODULE 5 : VERSION MANAGER TEST")
    print("=" * 60)

    vm = VersionManager()

    metadata = {
        "filename": "Employee_Handbook.pdf",
        "file_hash": "abc123456789",
        "department": "HR",
        "access_level": "internal"
    }

    print("\n[1] Registering first version...")

    updated = vm.register_document(metadata.copy())

    print("Version :", updated["version"])
    print("Status  :", updated["status"])
    print("Created :", updated["created_at"])

    print("\n[2] Registering second version...")

    metadata2 = {
        "filename": "Employee_Handbook.pdf",
        "file_hash": "xyz987654321",
        "department": "HR",
        "access_level": "internal"
    }

    updated2 = vm.register_document(metadata2.copy())

    print("Version :", updated2["version"])
    print("Status  :", updated2["status"])

    print("\n[3] Latest Version")

    latest = vm.get_latest_version("Employee_Handbook.pdf")

    print("Latest :", latest)

    print("\n[4] History")

    history = vm.get_document_history("Employee_Handbook.pdf")

    for item in history:
        print(item)

    print("\n[5] Active Version")

    active = vm.get_active_version("Employee_Handbook.pdf")

    print(active)

    print("\n[6] Compare Versions")

    comparison = vm.compare_versions(
        "Employee_Handbook.pdf",
        1,
        2
    )

    print(comparison)

    print("\n[7] Summary")

    vm.print_summary()

    print("\n")
    print("=" * 60)
    print("VERSION MANAGER WORKING SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()