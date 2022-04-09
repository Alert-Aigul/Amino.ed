from setuptools import setup, find_packages


with open("README.md", "r") as stream:
    long_description = stream.read()

setup(
    name="Amino.ed",
    version="2.3.10",
    url="https://github.com/Alert-Aigul/Amino.ed",
    download_url="https://github.com/Alert-Aigul/Amino.ed/archive/refs/heads/main.zip",
    license="MIT",
    author="Alert Aigul",
    author_email="alertaigul@gmail.com",
    description="A library to create Amino bots.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=[
        "aminoapps",
        "amino-py",
        "amino",
        "amino-bot",
        "amino.py",
        "amino.ed",
        "amino-ed",
        "narvii",
        "api",
        "python",
        "python3",
        "python3.x",
        "official",
        "alert",
        "fix",
        "ed"
    ],
    install_requires=[
        "requests",
        "setuptools",
        "six",
        "aiohttp",
        "ujson",
        "requests",
        "eventemitter",
        "typing",
        "pydantic"
    ],
    setup_requires=[
        "wheel"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
    ],
    python_requires=">=3.6",
    packages=find_packages()
)
