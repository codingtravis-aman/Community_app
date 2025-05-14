#!/usr/bin/env python3
import os
import subprocess
import sys

# This file serves as an entry point for deployment services
# It ensures the app is launched with the correct parameters

def main():
    # Run Streamlit with the correct app file
    subprocess.run(["streamlit", "run", "app.py"])

if __name__ == "__main__":
    main()