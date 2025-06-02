#!/bin/bash

# Run DB initialization
python database_create.py

# Then run the main script
python parse.py
