# 意図的にエラーを起こすコード
N, M = list(map(int, input().split()))  # ValueError: too many values to unpack
A = list(map(int, input().split()))
print(len(A))