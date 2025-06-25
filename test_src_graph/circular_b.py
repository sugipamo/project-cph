
# 循環依存B
from .circular_a import function_a

def function_b():
    return "b"

def function_b2():
    try:
        return function_a()
    except:
        return "b2"
