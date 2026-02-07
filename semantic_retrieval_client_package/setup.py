"""语义检索系统客户端库安装配置"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="semantic-retrieval-client",
    version="1.0.0",
    author="Semantic Retrieval System Team",
    author_email="contact@semantic-retrieval-system.com",
    description="语义检索系统 Python 客户端库",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PluginsX/SemanticRetrievalSystem",
    project_urls={
        "Documentation": "https://semantic-retrieval-system.readthedocs.io/",
        "Source": "https://github.com/PluginsX/SemanticRetrievalSystem/",
        "Tracker": "https://github.com/PluginsX/SemanticRetrievalSystem/issues/"
    },
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Client"
    ],
    python_requires=">=3.9",
    keywords="semantic retrieval client api",
    license="MIT",
)