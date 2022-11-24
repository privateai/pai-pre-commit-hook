from setuptools import setup, find_packages

VERSION = "1.0"
DESCRIPTION = "Pre-commit hook to check if modified files have PII and marks it."


setup(
    name="pii_check",
    version=VERSION,
    author="Private AI",
    description=DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        "requests==2.28.1",
        "python-dotenv==0.19.0",
    ],
    keywords=["python", "pre-commit"],
    entry_points={"console_scripts": ["pii_check=pii_check.pii_check_hook:main"]},
)
