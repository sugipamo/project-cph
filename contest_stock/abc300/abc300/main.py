N, A, B = list(map(int, input().split()))
C = list(map(int, input().split()))

raise Exception(C)

for i, c in enumerate(C):
    if c == A + B:
        print(i + 2)
        break
