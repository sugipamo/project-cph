
# モジュールB
from .module_a import function_a

def function_b():
    return "b"
    
def function_b2():
    return function_a() + "_b2"
