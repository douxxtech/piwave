# setup.py

from setuptools import setup, find_packages

setup(
    name="piwave",
    version="1.0.0",
    description="A Python module to manage your Pi radio using pi_fm_rds",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Douxx",
    author_email="douxx@douxx.xyz",
    url="https://github.com/douxxtech/piwave",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "ffmpeg-python",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
