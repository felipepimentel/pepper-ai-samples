from setuptools import find_packages, setup

setup(
    name="pepper-ai-samples",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.23.2",
        "pydantic>=2.4.2",
    ],
)
