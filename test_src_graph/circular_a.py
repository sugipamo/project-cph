
# 循環依存A
from .circular_b import function_b

def function_a():
    return function_b() + "_a"
