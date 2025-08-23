# -*- coding: utf-8 -*- 
"""
performance_core.py - パフォーマンス最適化のための汎用モジュール

このモジュールは、Raspberry Pi Zero 2Wのようなリソースが限られた環境で、
パフォーマンスを最適化するために設計された再利用可能なクラス群を提供します。
各クラスは特定の最適化手法に焦点を当てています。
"""
import time
import threading
from collections import deque
from typing import List, Tuple, Callable, Any, Dict

import numpy as np

# --- 最適化クラス群 ---

class MemoryPool:
    """
    再利用可能なバッファのプールを管理し、頻繁に割り当てられるメモリブロックを
    再利用することで、ガベージコレクション（不要なメモリを自動で解放する処理）の
    オーバーヘッド（余分な処理時間）を削減します。
    """
    def __init__(
            self,
            max_pools: int = 8,
            buffer_factory: Callable[[int], Any] = bytearray
    ):
        """
        メモリプールを初期化します。

        Args:
            max_pools (int): 各バッファサイズごとにプールに保持するバッファの
                             最大数。例えば、サイズ100のバッファを最大8個まで
                             プールに保持します。
            buffer_factory (Callable): 新しいバッファを作成するための関数。
                                       例: `bytearray` (バイト列を扱うためのバッファ)
        """
        self._pools: Dict[int, deque] = {}  # バッファサイズごとに分類されたプール
        self._max_pools = max_pools
        self._buffer_factory = buffer_factory
        self._lock = threading.Lock()  # スレッドセーフにするためのロック
        # （複数の処理が同時にメモリプールを操作しないようにする）
        self._stats = {'hits': 0, 'misses': 0, 'created': 0}  # 統計情報
        # （ヒット数、ミス数、作成数）

    def get_buffer(self, size: int) -> Any:
        """
        指定されたサイズ以上のバッファをプールから取得します。
        適切なバッファが見つからない場合は、新しいバッファを作成します。

        Args:
            size (int): 必要な最小バッファサイズ。

        Returns:
            バッファオブジェクト。
        """
        with self._lock:  # ロックを取得し、他のスレッドからの
            # アクセスを一時的にブロック
            # 指定されたサイズ以上の、利用可能な最小のバッファを探します
            for pool_size in sorted(self._pools.keys()):
                if pool_size >= size and self._pools[pool_size]:
                    self._stats['hits'] += 1  # プールから取得できたので
                    # ヒット数を増やす
                    return self._pools[pool_size].pop()  # プールからバッファを
                    # 取り出して返す

            # 適切なバッファが見つからない場合、新しいバッファを作成します
            self._stats['misses'] += 1  # プールから取得できなかったので
            # ミス数を増やす
            self._stats['created'] += 1  # 新しく作成したので作成数を増やす
            return self._buffer_factory(size)  # バッファ生成関数を使って
            # 新しいバッファを返す

    def return_buffer(self, buffer: Any):
        """
        バッファをプールに戻し、将来の再利用に備えます。

        Args:
            buffer: プールに戻すバッファオブジェクト。
        """
        size = len(buffer)  # バッファのサイズを取得
        with self._lock:  # ロックを取得
            if size not in self._pools:
                # そのサイズのプールがまだ存在しない場合、新しく作成
                self._pools[size] = deque(maxlen=self._max_pools)

            if len(self._pools[size]) < self._max_pools:
                # プールに空きがある場合、バッファを追加
                self._pools[size].append(buffer)

    def get_stats(self) -> dict:
        """プール使用状況に関する統計情報（ヒット数、ミス数など）を返します。
        """
        with self._lock:  # ロックを取得
            return self._stats.copy()  # 統計情報のコピーを返す

    def clear(self):
        """すべてのプールを空にし、統計情報をリセットします。"""
        with self._lock:  # ロックを取得
            self._pools.clear()  # すべてのプールをクリア
            self._stats = {'hits': 0, 'misses': 0, 'created': 0}  # 統計情報をリセット


class LookupTableCache:
    """
    事前に計算されたルックアップテーブル（LUTs: LookUp Tables）をキャッシュする
    シングルトン（プログラム全体で1つしか存在しない）クラスです。
    色変換やガンマ補正のような、計算コストの高い処理を高速化するために使用されます。
    """
    _instances: Dict[str, 'LookupTableCache'] = {}
    _lock = threading.Lock()  # スレッドセーフにするためのロック

    @classmethod
    def get_instance(cls, table_type: str) -> 'LookupTableCache':
        """
        指定されたテーブルタイプに対応するシングルトンインスタンスへのアクセスを
        提供します。もしそのタイプのインスタンスがまだ作成されていなければ、
        新しく作成します。
        """
        with cls._lock:  # ロックを取得
            if table_type not in cls._instances:
                cls._instances[table_type] = cls(table_type)  # インスタンスがなければ作成
            return cls._instances[table_type]  # 既存または新しく作成したインスタンスを返す

    def __init__(self, table_type: str):
        self.table_type = table_type  # テーブルのタイプ
        # （例: 'rgb565', 'gamma'）
        self._tables: Dict[str, np.ndarray] = {}  # キャッシュされたテーブルを保持
        self._generators: Dict[str, Callable[..., Dict[str, np.ndarray]]] = {
            'rgb565': self._generate_rgb565_tables,  # RGB565変換テーブルの生成関数
            'gamma': self._generate_gamma_tables,    # ガンマ補正テーブルの生成関数
        }

    def _generate_rgb565_tables(self) -> Dict[str, np.ndarray]:
        """
        高速なRGBからRGB565への変換のためのLUTs（ルックアップテーブル）を生成します。
        RGB565は、赤5ビット、緑6ビット、青5ビットで色を表現する形式で、
        メモリ使用量を抑えつつ色を表現するのに使われます。
        """
        return {
            'r_shift': (np.arange(256, dtype=np.uint16) >> 3) << 11,  # 赤成分のシフト値
            'g_shift': (np.arange(256, dtype=np.uint16) >> 2) << 5,   # 緑成分のシフト値
            'b_shift': (np.arange(256, dtype=np.uint16) >> 3),        # 青成分のシフト値
        }

    def _generate_gamma_tables(
            self, gamma: float = 2.2
    ) -> Dict[str, np.ndarray]:
        """
        ガンマ補正のためのLUTを生成します。
        ガンマ補正は、画像の明るさやコントラストを調整するために使われる技術です。
        人間の目の明るさに対する感度に合わせて画像を調整します。
        """
        table = np.array([
            int(255 * ((i / 255.0) ** gamma)) for i in range(256)
        ], dtype=np.uint8)  # 0-255の各値に対してガンマ補正を適用した
        # テーブルを作成
        return {'gamma_table': table}

    def get_table(self, table_name: str, **kwargs: Any) -> np.ndarray:
        """
        テーブルを取得します。もしキャッシュに存在しない場合は、新しく生成して
        キャッシュします。
        
        Args:
            table_name (str): 取得するテーブルの名前。
            **kwargs: テーブル生成関数に渡すパラメータ（例: `gamma=2.2`）。
                      これにより、同じ種類のテーブルでも異なる設定で生成できます。

        Returns:
            要求されたルックアップテーブル（通常はNumPy配列）。
        """
        # キャッシュキーを作成（テーブル名とパラメータのハッシュ値で一意に識別）
        cache_key = (
            f"{table_name}_{hash(str(sorted(kwargs.items())))}"
        )  # キャッシュキーを作成
        # （テーブル名とパラメータのハッシュ値で一意に識別）
        if cache_key not in self._tables:  # キャッシュに存在しない場合
            if self.table_type not in self._generators:
                raise ValueError(f"不明なテーブルタイプ: {self.table_type}")
            
            # テーブル生成関数を呼び出してテーブルを生成
            generated = self._generators[self.table_type](**kwargs)
            if table_name not in generated:
                raise KeyError(
                    f"タイプ '{self.table_type}' のテーブルに "
                    f