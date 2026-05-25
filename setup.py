from setuptools import setup, find_packages

setup(
    name="sample-fabric-package",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A sample Python package for Microsoft Fabric runtime",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sample-fabric-package",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "azure-identity>=1.17.1",
        "azure-storage-blob>=12.22.0",
    ],
    entry_points={
        "console_scripts": [
            "sample-fabric=sample_fabric.main:main",
        ],
    },
)