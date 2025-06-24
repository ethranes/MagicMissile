from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).parent
README = (BASE_DIR / "README.md").read_text(encoding="utf-8")

setup(
    name="magicmissile-trading-bot",
    version="0.1.0",
    description="Modular Python stock trading bot framework",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "pandas",
        "numpy",
        "pydantic",
        "yfinance",
        "loguru",
        "pyyaml",
    ],
    extras_require={
        "dev": [
            "black",
            "pytest",
            "mypy",
        ]
    },
)
