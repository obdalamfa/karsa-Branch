import sys
import os

try:
    from game.app import Game3D
    print("Imports successful")
except Exception as e:
    print(f"Error importing Game3D: {e}")
    sys.exit(1)

print("Test complete.")
