# setup.py

from setuptools import setup, find_packages

setup(
    name="piwave",
    version="2.0.0",
    description="A Python module to manage your Pi radio using pi_fm_rds with stream support.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Douxx",
    author_email="douxx@douxx.tech",
    url="https://github.com/douxxtech/piwave",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pathlib",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    keywords="raspberry pi, radio, fm, rds, streaming, audio, broadcast",
    project_urls={
        "Bug Reports": "https://github.com/douxxtech/piwave/issues",
        "Source": "https://github.com/douxxtech/piwave",
    }
)