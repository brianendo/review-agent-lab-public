"""Batch accumulation."""


def add_to_batch(item, batch=[]):
    """Append item to batch and return it. If no batch is given, start a new one."""
    batch.append(item)
    return batch
