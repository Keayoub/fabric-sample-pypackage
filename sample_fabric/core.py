"""
Core functionality for the sample Fabric package.
"""

import sys
import platform
import datetime
from typing import Dict, Any


def display_message(message: str, prefix: str = "[FABRIC]") -> None:
    """
    Display a formatted message with timestamp.
    
    Args:
        message (str): The message to display
        prefix (str): Prefix for the message (default: "[FABRIC]")
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{prefix} {timestamp} - {message}"
    print(formatted_message)
    print("-" * len(formatted_message))


def get_fabric_info() -> Dict[str, Any]:
    """
    Get information about the current runtime environment.
    
    Returns:
        Dict containing system information relevant for Fabric runtime
    """
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "python_executable": sys.executable,
        "package_version": "0.1.0",
        "timestamp": datetime.datetime.now().isoformat()
    }
    return info


def display_fabric_info() -> None:
    """Display formatted system information for Fabric runtime."""
    info = get_fabric_info()
    
    display_message("Fabric Runtime Environment Information")
    print()
    
    for key, value in info.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print()
    display_message("Environment check completed successfully!")


class FabricHelper:
    """Helper class for Fabric runtime operations."""
    
    def __init__(self, app_name: str = "SampleFabricApp"):
        self.app_name = app_name
        self.start_time = datetime.datetime.now()
    
    def log(self, message: str) -> None:
        """Log a message with app context."""
        display_message(f"[{self.app_name}] {message}")
    
    def get_uptime(self) -> str:
        """Get application uptime."""
        uptime = datetime.datetime.now() - self.start_time
        return str(uptime).split('.')[0]  # Remove microseconds
    
    def display_banner(self) -> None:
        """Display application banner."""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                    {self.app_name.center(30)}                    ║
║                                                              ║
║              Running on Microsoft Fabric Runtime            ║
║                                                              ║
║                    Package Version: 0.1.0                   ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        self.log("Application initialized successfully")
    
    def run_sample_operations(self) -> None:
        """Run sample operations to demonstrate functionality."""
        self.log("Starting sample operations...")
        
        # Sample operation 1: Display system info
        self.log("Checking system information...")
        display_fabric_info()
        
        # Sample operation 2: Simple computation
        self.log("Performing sample computation...")
        result = sum(range(1, 101))  # Sum of 1 to 100
        self.log(f"Sum of numbers 1-100: {result}")
        
        # Sample operation 3: String operations  
        self.log("Demonstrating string operations...")
        sample_text = "Hello Microsoft Fabric!"
        self.log(f"Original text: {sample_text}")
        self.log(f"Reversed text: {sample_text[::-1]}")
        self.log(f"Text length: {len(sample_text)}")
        
        self.log(f"Sample operations completed! Uptime: {self.get_uptime()}")