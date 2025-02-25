import pickle
import os

def save_checkpoint(checkpoint_file, data):
    """Saves checkpoint data to a file using pickle."""
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(data, f)

def load_checkpoint(checkpoint_file):
    """Loads checkpoint data from a file if it exists."""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'rb') as f:
            return pickle.load(f)
    return None