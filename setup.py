from setuptools import setup

setup(install_requires=open("requirements.txt").readlines(),
      extras_require={"dev": open("requirements-dev.txt").readlines()})
