from setuptools import setup, find_packages

setup(
    name="neo-chat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.23.2",
        "pydantic>=2.4.2",
        "httpx>=0.25.1",
        "python-dotenv>=1.0.0",
        "asyncpg>=0.28.0",
        "aiosqlite>=0.19.0",
    ],
) 