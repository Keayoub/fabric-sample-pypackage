"""
Main entry point for the sample Fabric package.
"""

import sys
import argparse
from sample_fabric.core import FabricHelper, display_message


def main():
    """Main entry point for the console application."""
    parser = argparse.ArgumentParser(
        description="Sample Python package for Microsoft Fabric runtime"
    )
    parser.add_argument(
        "--message", 
        "-m", 
        type=str, 
        help="Custom message to display"
    )
    parser.add_argument(
        "--info", 
        "-i", 
        action="store_true", 
        help="Display system information only"
    )
    parser.add_argument(
        "--demo", 
        "-d", 
        action="store_true", 
        help="Run full demo with sample operations"
    )
    
    args = parser.parse_args()
    
    # Initialize Fabric helper
    fabric_helper = FabricHelper("SampleFabricPackage")
    
    if args.message:
        # Display custom message
        display_message(args.message)
    elif args.info:
        # Display system info only
        from sample_fabric.core import display_fabric_info
        display_fabric_info()
    elif args.demo:
        # Run full demo
        fabric_helper.display_banner()
        fabric_helper.run_sample_operations()
    else:
        # Default behavior
        fabric_helper.display_banner()
        display_message("Welcome to Sample Fabric Package!")
        display_message("Use --help to see available options")
        display_message("Use --demo to run a full demonstration")


if __name__ == "__main__":
    main()