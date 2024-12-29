def generate_case():
    # TODO: カスタムケースの生成ロジックを実装
    input_data = ""
    output_data = ""
    return input_data, output_data

def main():
    # 生成するテストケースの数を指定
    n_cases = 1
    
    inputs = []
    outputs = []
    
    for _ in range(n_cases):
        input_data, output_data = generate_case()
        inputs.append(input_data)
        outputs.append(output_data)
    
    # 入力ケースの出力
    for input_data in inputs:
        print(input_data)
    
    # 期待される出力の出力（標準エラー出力）
    import sys
    for output_data in outputs:
        print(output_data, file=sys.stderr)

if __name__ == "__main__":
    main() 