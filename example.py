"""
Example usage of the sample Fabric package.
"""

from sample_fabric import (
    display_message,
    get_fabric_info,
    FabricHelper,
    OneLakeScopedBlobIO,
)


def main():
    """Demonstrate package usage."""
    
    # Simple message display
    display_message("Hello from Sample Fabric Package!")
    
    # Get and display system information
    info = get_fabric_info()
    print("\nSystem Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Use the FabricHelper class
    helper = FabricHelper("ExampleApp")
    helper.display_banner()
    helper.log("This is an example application")
    helper.run_sample_operations()

    # OneLake scoped Blob API example (requires valid Fabric permissions).
    client = OneLakeScopedBlobIO(
        workspace_id="f9c754ab-fb1f-420b-a466-69cbb21ea6cf",
        lakehouse_id="fea2bc2c-7a62-4bae-8333-ef692a29ff40",
        base_folder="Files/sample",
        allowed_folders=("inbox", "outbox"),
    )
    print("\nOneLake client ready. Allowed folders:", sorted(client.allowed_folders))


if __name__ == "__main__":
    main()