
from setuptools import setup, find_packages

setup(
    name='pytender',
    version='0.0.1',
    install_requires=['python-dotenv', 'httpx', 'uvloop', 'web3'],
    packages=find_packages(),
    url='https://github.com/darkerego/pytender.git',
    license='MIT',
    author='darkerego',
    author_email='xelectron@protonmail.com',
    description='Python Tenderly Library',
    classifiers = [
        'Programming Language :: Python :: 3',
    ],
)
