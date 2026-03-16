# setup.py
from setuptools import setup, find_packages

setup(
    name="seinentai_rag",
    version="0.1",
    packages=find_packages(),
)


# Désinstaller
# pip uninstall seinentai_rag -y

# # Nettoyer les caches
# pip cache purge

# # Réinstaller en mode développement
# pip install -e .