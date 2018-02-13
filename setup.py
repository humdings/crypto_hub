#!/usr/bin/env python
from setuptools import setup, find_packages

DISTNAME = 'crypto_hub'
DESCRIPTION = "Python implementations of various APIs."
MAINTAINER = 'David Edwards'
MAINTAINER_EMAIL = 'humdings@gmail.com'
AUTHOR = 'David Edwards'
AUTHOR_EMAIL = 'humdings@gmail.com'
URL = "https://github.com/humdings/crypto_hub"
VERSION = "0.0.1"

classifiers = [
    'Programming Language :: Python',
    'Operating System :: OS Independent'
]

if __name__ == "__main__":
    setup(name=DISTNAME,
          version=VERSION,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          url=URL,
          packages=find_packages('.', include=['crypto_hub', 'crypto_hub.*']),
          classifiers=classifiers,
)

