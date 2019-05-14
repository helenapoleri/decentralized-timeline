from setuptools import setup, find_packages

setup(
    name="decentralized-timeline",
    version="1.0",
    description="Peer-to-peer timeline service",
    long_description=open("README.md", encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="http://github.com/helenapoleri/decentralized-timeline",
    install_requires=open("requirements.txt").readlines()
)
