import sys
import os
# tests/ ada satu tingkat di bawah root — pastikan root ada di sys.path agar `game` ter-import.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from game.app import Game3D
    print("Imports successful")
except Exception as e:
    print(f"Error importing Game3D: {e}")
    sys.exit(1)

print("Test complete.")
