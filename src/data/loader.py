"""Data loading module for Vireo Audio Support Intelligence.

Handles locating and reading raw CSV datasets with strict validation and error handling.
"""

from pathlib import Path
from typing import Dict, Optional
import pandas as pd


class DataLoader:
    """Loads raw support data files into Pandas DataFrames using pathlib."""

    DEFAULT_FILES = {
        "tickets": "tickets.csv",
        "agents": "agents.csv",
        "orders": "orders.csv",
        "customers": "customers.csv",
        "products": "products.csv",
    }

    def __init__(self, raw_data_dir: Optional[Path] = None):
        """Initialize DataLoader with path to raw data directory.

        Args:
            raw_data_dir: Directory containing raw CSV files. Defaults to
                          <project_root>/data/raw if not provided.
        """
        if raw_data_dir is None:
            # Anchor to project root relative to this file
            self.raw_data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
        else:
            self.raw_data_dir = Path(raw_data_dir)

    def get_file_path(self, dataset_name: str) -> Path:
        """Resolve absolute path for a dataset name.

        Args:
            dataset_name: Key in DEFAULT_FILES ('tickets', 'agents', etc.)

        Returns:
            Path object to the dataset file.

        Raises:
            FileNotFoundError: If dataset file cannot be located.
        """
        if dataset_name not in self.DEFAULT_FILES:
            raise KeyError(f"Unknown dataset name: {dataset_name}. Expected one of {list(self.DEFAULT_FILES.keys())}")

        filename = self.DEFAULT_FILES[dataset_name]
        path = self.raw_data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Dataset file '{filename}' not found in '{self.raw_data_dir}'.")
        return path

    def load_dataset(self, dataset_name: str) -> pd.DataFrame:
        """Load a single dataset by name into a Pandas DataFrame.

        Args:
            dataset_name: Key name of dataset ('tickets', 'agents', etc.)

        Returns:
            pd.DataFrame containing the raw file data.
        """
        path = self.get_file_path(dataset_name)
        return pd.read_csv(path)

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Load all five core datasets.

        Returns:
            Dictionary mapping dataset names to DataFrames.
        """
        datasets = {}
        for key in self.DEFAULT_FILES:
            datasets[key] = self.load_dataset(key)
        return datasets
