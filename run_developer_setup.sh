#!/bin/bash
# Install dependency packages
pip install -r requirements.txt

# Install netharn in developer mode
#pip install -e .
python setup.py develop
