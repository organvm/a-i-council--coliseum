
import time
import random
import string
import heapq
from typing import List, Tuple

def current_implementation(text: str) -> List[str]:
    words = text.split()
    word_freq = {}
    for word in words:
        if len(word) > 4:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Top 5 keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:5]]

def optimized_implementation(text: str) -> List[str]:
    words = text.split()
    word_freq = {}
    for word in words:
        if len(word) > 4:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Top 5 keywords using heapq
    top_words = heapq.nlargest(5, word_freq.items(), key=lambda x: x[1])
    return [word for word, _ in top_words]

def generate_text(num_words: int) -> str:
    # Generate random words
    vocabulary = ["".join(random.choices(string.ascii_lowercase, k=random.randint(5, 10))) for _ in range(1000)]
    return " ".join(random.choices(vocabulary, k=num_words))

if __name__ == "__main__":
    print("Generating text...")
    # 1 million words to make it noticeable
    text = generate_text(1_000_000)
    print("Text generated.")

    start = time.time()
    res_current = current_implementation(text)
    end = time.time()
    print(f"Current implementation: {end - start:.4f} seconds")

    start = time.time()
    res_opt = optimized_implementation(text)
    end = time.time()
    print(f"Optimized implementation: {end - start:.4f} seconds")

    assert set(res_current) == set(res_opt), "Results differ!"
    print("Results match.")
