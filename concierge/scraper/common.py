

def exclude_from_history(tasks, history) -> list:
    return list(set(tasks) - set(history))
