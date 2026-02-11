#!/usr/bin/env python
"""
Setup configuration for Crypto Signal Scanner
"""

from setuptools import setup, find_packages

setup(
    name="richesse-crypto-scanner",
    version="1.0.0",
    description="Advanced Crypto Signal Scanner with Scalping Signals",
    author="Raphael Fontaine",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "flask>=3.0.0",
        "gunicorn>=21.2.0",
        "requests>=2.31.0",
        "python-dateutil>=2.8.0",
        "pytz>=2023.3",
    ],
    entry_points={
        "console_scripts": [
            "richesse-scanner=main:run_scanner",
        ],
    },
)
