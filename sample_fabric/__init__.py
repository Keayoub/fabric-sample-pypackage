"""
Sample Fabric Package

A minimal Python package for Microsoft Fabric runtime.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .core import display_message, get_fabric_info, FabricHelper
from .onelake_io import OneLakeScopedBlobIO

__all__ = ["display_message", "get_fabric_info", "FabricHelper", "OneLakeScopedBlobIO"]