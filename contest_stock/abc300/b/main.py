# ABC300 A problem - Find position of A+B in N choices
N, A, B = map(int, input().split())
C = list(map(int, input().split()))

# Find position of A+B in the list (1-indexed)
target = A + B
for i, value in enumerate(C):
    if value == target:
        print(i + 1)  # 1-indexed position
        break