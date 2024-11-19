#! /bin/bash

# Ensure the script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

# Install dependencies
pip install -r requirements.txt || exit 1

# Get the directory of the script
DIR=$(pwd)

# Create a proper executable
CURRENT_DIR=$(pwd)
CMD="""
#!/bin/bash

cd $CURRENT_DIR
streamlit run src/main.py
"""

echo "$CMD" > /usr/local/bin/youlama
chmod +x /usr/local/bin/youlama
