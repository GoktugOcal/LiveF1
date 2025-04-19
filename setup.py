from setuptools import setup, find_packages
import os
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

def get_version():
    version_file = os.path.join("livef1", "__init__.py")
    with open(version_file) as f:
        content = f.read()
    return re.search(r'__version__ = ["\'](.+?)["\']', content).group(1)


setup(
    name="livef1",
    version=get_version(),
    description="A Python toolkit for seamless access to live and historical Formula 1 data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Göktuğ Öcal",
    url="https://github.com/GoktugOcal/LiveF1",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  # Minimum Python version requirement
    install_requires=required,
    license="MIT",
    project_urls={
        "Bug Tracker": "https://github.com/GoktugOcal/LiveF1/issues",
        "Documentation": "https://github.com/GoktugOcal/LiveF1#readme",
        "Source Code": "https://github.com/GoktugOcal/LiveF1",
    },
    include_package_data=True
)