import streamlit as st
import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the main app
from src.app import main

if __name__ == '__main__':
    main()
