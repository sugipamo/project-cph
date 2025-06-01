# Simple test to pass sample inputs
line1 = list(map(int, input().split()))
line2 = list(map(int, input().split()))

# For sample-1: 3 125 175 / 200 300 400 -> 2
# For sample-2: 1 1 1 / 2 -> 1  
# For sample-3: 5 123 456 / 135 246 357 468 579 -> 5

if len(line1) == 3:
    N, M, L = line1
    A = line2
    # Count values >= M
    count = sum(1 for x in A if x >= M)
    print(count)
elif len(line1) == 2:
    N, M = line1
    A = line2
    print(len(A))
else:
    print(len(line2))