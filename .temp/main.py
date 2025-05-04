# a.py
# 問題: a
# 言語: python

if __name__ == "__main__":
    import sys
    print("This is stderr test", file=sys.stderr)
    N, A, B = map(int, input().split())
    C = list(map(int, input().split()))
    print(C.index(A + B) + 1)