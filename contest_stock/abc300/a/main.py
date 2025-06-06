#!/usr/bin/env python3

def solve():
    N, C = map(int, input().split())
    A, B = map(int, input().split())
    
    result = A + B
    if result > C:
        print(C + 1)
    else:
        print(result)

if __name__ == "__main__":
    solve()