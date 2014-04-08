

def isInt(x):
    try:
        int(x)
        return True
    except ValueError:
        return False
