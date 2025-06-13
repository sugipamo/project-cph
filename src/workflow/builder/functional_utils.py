"""関数型プログラミングユーティリティ - pipe, compose等"""
from functools import reduce
from typing import Any, Callable, Iterable, TypeVar

T = TypeVar('T')
U = TypeVar('U')


def pipe(value: T, *functions: Callable[[Any], Any]) -> Any:
    """関数型パイプライン - 値を順次関数に通す

    Args:
        value: 初期値
        *functions: 適用する関数群

    Returns:
        最終的な変換結果

    Example:
        result = pipe(
            [1, 2, 3],
            lambda x: [i * 2 for i in x],  # [2, 4, 6]
            lambda x: sum(x),               # 12
            lambda x: str(x)                # "12"
        )
    """
    return reduce(lambda acc, func: func(acc), functions, value)


def compose(*functions: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """関数合成 - 右から左に関数を合成

    Args:
        *functions: 合成する関数群

    Returns:
        合成された関数

    Example:
        process = compose(
            lambda x: str(x),               # 最後に適用
            lambda x: sum(x),               # 2番目に適用
            lambda x: [i * 2 for i in x]   # 最初に適用
        )
        result = process([1, 2, 3])  # "12"
    """
    def composed_function(value: Any) -> Any:
        return reduce(lambda acc, func: func(acc), reversed(functions), value)
    return composed_function


def map_pure(func: Callable[[T], U], iterable: Iterable[T]) -> list[U]:
    """純粋関数版map - 新しいリストを返却

    Args:
        func: 変換関数
        iterable: 変換対象

    Returns:
        変換された新しいリスト
    """
    return [func(item) for item in iterable]


def filter_pure(predicate: Callable[[T], bool], iterable: Iterable[T]) -> list[T]:
    """純粋関数版filter - 新しいリストを返却

    Args:
        predicate: 判定関数
        iterable: フィルタ対象

    Returns:
        フィルタされた新しいリスト
    """
    return [item for item in iterable if predicate(item)]


def reduce_pure(func: Callable[[T, U], T], iterable: Iterable[U], initial: T) -> T:
    """純粋関数版reduce

    Args:
        func: 集約関数
        iterable: 集約対象
        initial: 初期値

    Returns:
        集約結果
    """
    return reduce(func, iterable, initial)


def group_by(key_func: Callable[[T], Any], iterable: Iterable[T]) -> dict[Any, list[T]]:
    """グループ化 - キー関数によってリストをグループ化

    Args:
        key_func: グループ化キー生成関数
        iterable: グループ化対象

    Returns:
        グループ化された辞書
    """
    groups = {}
    for item in iterable:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


def partition(predicate: Callable[[T], bool], iterable: Iterable[T]) -> tuple[list[T], list[T]]:
    """分割 - 条件により2つのリストに分割

    Args:
        predicate: 分割条件
        iterable: 分割対象

    Returns:
        (条件を満たすリスト, 条件を満たさないリスト)
    """
    true_items = []
    false_items = []

    for item in iterable:
        if predicate(item):
            true_items.append(item)
        else:
            false_items.append(item)

    return true_items, false_items


def flatten(nested_list: Iterable[Iterable[T]]) -> list[T]:
    """平坦化 - ネストしたリストを1次元化

    Args:
        nested_list: ネストしたリスト

    Returns:
        平坦化されたリスト
    """
    result = []
    for sublist in nested_list:
        result.extend(sublist)
    return result


def unique(iterable: Iterable[T]) -> list[T]:
    """重複削除 - 順序を保持して重複を削除

    Args:
        iterable: 重複削除対象

    Returns:
        重複のない新しいリスト
    """
    seen = set()
    result = []
    for item in iterable:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def take(n: int, iterable: Iterable[T]) -> list[T]:
    """先頭n個を取得

    Args:
        n: 取得個数
        iterable: 取得対象

    Returns:
        先頭n個のリスト
    """
    result = []
    for i, item in enumerate(iterable):
        if i >= n:
            break
        result.append(item)
    return result


def drop(n: int, iterable: Iterable[T]) -> list[T]:
    """先頭n個をスキップ

    Args:
        n: スキップ個数
        iterable: スキップ対象

    Returns:
        先頭n個をスキップしたリスト
    """
    result = []
    for i, item in enumerate(iterable):
        if i >= n:
            result.append(item)
    return result
