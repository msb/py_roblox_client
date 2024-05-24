import os
from setuptools import setup, find_packages

lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = f"{lib_folder}/requirements.txt"
install_requires = []
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        install_requires = f.read().splitlines()

setup(
    name='py_roblox_client',
    version='0.1',
    description='AIO python client for Roblox cloud API',
    author='Mike Bamford',
    packages=find_packages(),
    install_requires=install_requires,
)
