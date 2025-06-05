N, X, Y = map(int, input().split())
A = list(map(int, input().split()))

# Xからの距離がY以下の値の個数を数える
count = 0
for a in A:
    if abs(a - X) <= Y:
        count += 1

print(count)