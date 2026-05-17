_selected = {}

def set_selected(record_type, record):
    _selected[record_type] = record


def get_selected(record_type, records):
    record = _selected.get(record_type)
    if record not in records:
        return None
    return record


def clear_selected(record_type):
    _selected[record_type] = None