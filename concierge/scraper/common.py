

def exclude_from_history(tasks, history) -> list:
    try:
        return list(set(tasks) - set(history))
    except TypeError:
        return []
