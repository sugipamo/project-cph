"""
Environment Fitting Module

実環境との差異を確認し、ワークフロー実行に必要な事前準備を提供する

責務分離:
- workflow: operationsに依存せず、ユーザー指定のrequestを純粋に生成
- fitting: operations経由で実環境の状態確認と事前準備を行う

主な機能:
- 実環境の状態確認（operations経由）
- ワークフロー要求と実環境の差異分析
- 必要な準備requestの生成・実行
- 環境適合処理
"""

from .preparation_executor import PreparationExecutor

# 主要なクラスのみ公開（operationsを使用するもの）
__all__ = [
    'PreparationExecutor'
]