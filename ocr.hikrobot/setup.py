# SPDX-FileCopyrightText: Bosch Rexroth AG
#
# SPDX-License-Identifier: MIT
from setuptools import setup

setup(
    name="ocr-hikrobot",
    version="1.0.0",
    description="OCR Reader",
    author="Akra",
    install_requires=["flask"],
    packages=["MVImport", "dependencies"],
    scripts=["main.py"],
    license="MIT License",
)
