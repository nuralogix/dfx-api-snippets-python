from setuptools import setup, find_packages

setup(
    name='dfxsnippets',
    version='0.1',
    description='a tutorial of dfx-api ',
    url='http://',
    author='NuraLogix Development Team',
    author_email='dev@nuralogix.ai',
    license='N/A',
    packages=find_packages(),
    install_requires=['requests', 'urllib3', 'websockets', 'protobuf'])
