import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.add_events import create_events

if __name__ == "__main__":
    create_events()