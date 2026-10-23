"""
Dataset Storage
DS 3500 - MP2

Manages in-memory storage of uploaded datasets.

Stores DataFrames with unique integer IDs and filenames,
retrieves copies of stored data, provides dataset metadata,
updates existing datasets, and clears stored data.
"""

import logging
from .models import DatasetInfo

logger = logging.getLogger(__name__)


class DatasetStorage:
    def __init__(self):
        self._store = {}
        self._counter = 0

    def save(self, df, filename):
        """Store a copy of the data and return a new integer ID."""
        self._counter += 1
        dataset_id = self._counter
        self._store[dataset_id] = (df.copy(), filename)
        return dataset_id

    def get(self, dataset_id):
        """Return a copy of the stored DataFrame, or None."""
        if dataset_id in self._store:
            return self._store[dataset_id][0].copy()
        return None

    def get_metadata(self, dataset_id):
        """Return the dataset metadata, or None."""
        if dataset_id in self._store:
            df, filename = self._store[dataset_id]
            return DatasetInfo(
                id=dataset_id,
                filename=filename,
                rows=df.shape[0],
                columns=df.shape[1],
                column_names=df.columns.tolist()
            )
        return None

    def update(self, dataset_id, df):
        """Replace an existing dataset; return True, or False if missing."""
        if dataset_id in self._store:
            _, filename = self._store[dataset_id]
            self._store[dataset_id] = (df.copy(), filename)
            return True
        return False

    def clear(self):
        """Clear all data and reset the ID counter."""
        self._store.clear()
        self._counter = 0
