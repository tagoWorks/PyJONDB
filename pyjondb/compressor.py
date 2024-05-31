import heapq
from collections import defaultdict, Counter
from typing import Dict, Optional, List, Tuple

class HuffmanNode:
    def __init__(self, symbol: Optional[int], freq: int):
        self.symbol = symbol
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanCoding:
    def __init__(self):
        self.huffman_tree_root = None
        self.codes = {}
        self.reverse_mapping = {}
        self.compact_mapping = {}
        self.reverse_compact_mapping = {}

    def build_frequency_dict(self, data: str) -> Dict[int, int]:
        return dict(Counter(data))

    def build_priority_queue(self, frequency: Dict[int, int]) -> List[HuffmanNode]:
        priority_queue = []
        for symbol, freq in frequency.items():
            node = HuffmanNode(symbol, freq)
            heapq.heappush(priority_queue, node)
        return priority_queue

    def build_huffman_tree(self, priority_queue: List[HuffmanNode]) -> HuffmanNode:
        while len(priority_queue) > 1:
            node1 = heapq.heappop(priority_queue)
            node2 = heapq.heappop(priority_queue)
            merged = HuffmanNode(None, node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2
            heapq.heappush(priority_queue, merged)
        return heapq.heappop(priority_queue)

    def build_codes_helper(self, node: HuffmanNode, current_code: str):
        if node is None:
            return
        if node.symbol is not None:
            self.codes[node.symbol] = current_code
            return
        self.build_codes_helper(node.left, current_code + "0")
        self.build_codes_helper(node.right, current_code + "1")

    def build_codes(self):
        if not self.huffman_tree_root:
            return
        self.build_codes_helper(self.huffman_tree_root, "")

    def create_compact_mapping(self):
        compact_symbols = "123456789abcdefghijklmnopqrstuvwxyz"
        index = 0
        for code in sorted(self.codes.values(), key=lambda x: len(x)):
            self.compact_mapping[code] = compact_symbols[index]
            self.reverse_compact_mapping[compact_symbols[index]] = code
            index += 1

    def compress(self, data: str) -> str:
        frequency = self.build_frequency_dict(data)
        priority_queue = self.build_priority_queue(frequency)
        self.huffman_tree_root = self.build_huffman_tree(priority_queue)
        self.build_codes()
        self.create_compact_mapping()
        encoded_data = "".join([self.compact_mapping[self.codes[symbol]] for symbol in data])
        return encoded_data

    def decompress(self, encoded_data: str) -> str:
        current_code = ""
        decoded_data = []
        for char in encoded_data:
            current_code += self.reverse_compact_mapping[char]
            if current_code in self.codes.values():
                for key, value in self.codes.items():
                    if value == current_code:
                        decoded_data.append(key)
                        current_code = ""
                        break
        return "".join(decoded_data)

if __name__ == "__main__":
    # Example usage
    data = "010101010111100011010011010011010001011110101010100101"
    huffman_coding = HuffmanCoding()
    compressed_data = huffman_coding.compress(data)
    print(f"Compressed Data: {compressed_data}")
    decompressed_data = huffman_coding.decompress(compressed_data)
    print(f"Decompressed Data: {decompressed_data}")