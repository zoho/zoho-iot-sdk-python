from setuptools import setup, find_packages

from codecs import open
from os import path

HERE = path.abspath(path.dirname(__file__))

def read_version():
    version_file = path.join(HERE, "zoho_iot_sdk", "version.py")
    with open(version_file) as f:
        for line in f:
            if line.startswith("VERSION"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(HERE, 'requirements.txt')) as f:
    install_requires = f.read().splitlines()
setup(
    name="zoho_iot_sdk",
    version=read_version(),
    description="Zoho IoT SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="www.zoho.com/iot",
    author="Shahul",
    author_email="shahul.s@zohocorp.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent"
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
)
