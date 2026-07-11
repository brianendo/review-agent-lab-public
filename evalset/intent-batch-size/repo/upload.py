"""Bulk upload batching."""

BATCH_SIZE = 1000


def batches(records):
    """Yield successive batches of records to upload."""
    for i in range(0, len(records), BATCH_SIZE):
        yield records[i:i + BATCH_SIZE]
