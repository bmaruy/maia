"""
Perturbation strategies for MAIA prompt testing.

Each strategy is a function that takes text and returns modified text.
All strategies accept **kwargs to allow config flexibility.
"""

import random
import re
from typing import Callable


# ============================================================================
# BASIC TEXT MANIPULATION
# ============================================================================

def replace_text(_: str, replace: str = "", **__) -> str:
    """Replace entire text with new text."""
    return replace


def append_text(text: str, append: str = "", **_) -> str:
    """Append specific text to the end."""
    return text.rstrip() + " " + append


def prepend_text(text: str, prepend: str = "", **_) -> str:
    """Prepend specific text to the beginning."""
    return prepend + " " + text.lstrip()


# ============================================================================
# NOISE INJECTION
# ============================================================================

def append_random(text: str, seed: int = 0, n: int = 3, **_) -> str:
    """Append N random words to the text."""
    rng = random.Random(seed)
    words = [
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz")
                for _ in range(rng.randint(3, 8)))
        for _ in range(n)
    ]
    return text.rstrip() + " " + " ".join(words)


def remove_random_word(text: str, seed: int = 0, **_) -> str:
    """Remove one random word from the text."""
    words = re.findall(r"\b\w+\b", text)
    if not words:
        return text
    rng = random.Random(seed)
    idx = rng.randrange(len(words))
    target = words[idx]
    return re.sub(
        rf"\b{re.escape(target)}\b", "", text, count=1
    ).replace("  ", " ").strip()


def inject_typos(text: str, seed: int = 0, rate: float = 0.05, **_) -> str:
    """Inject random typos at specified rate using QWERTY keyboard proximity."""
    rng = random.Random(seed)
    chars = list(text)
    nearby = {
        'a': 'sq', 'b': 'vn', 'c': 'xv', 'd': 'sf', 'e': 'wr',
        'f': 'dg', 'g': 'fh', 'h': 'gj', 'i': 'uo', 'j': 'hk',
        'k': 'jl', 'l': 'k', 'm': 'n', 'n': 'bm', 'o': 'ip',
        'p': 'o', 'q': 'wa', 'r': 'et', 's': 'ad', 't': 'ry',
        'u': 'yi', 'v': 'cb', 'w': 'qe', 'x': 'zc', 'y': 'tu',
        'z': 'x'
    }

    for i in range(len(chars)):
        if chars[i].isalpha() and rng.random() < rate:
            char_lower = chars[i].lower()
            if char_lower in nearby:
                replacement = rng.choice(nearby[char_lower])
                chars[i] = replacement.upper() if chars[i].isupper() else replacement

    return ''.join(chars)


# ============================================================================
# STRUCTURAL CHANGES
# ============================================================================

def shuffle_sentences(text: str, seed: int = 0, **_) -> str:
    """Randomly shuffle sentences in the text."""
    rng = random.Random(seed)
    sentences = re.split(r'([.!?]\s+)', text)

    # Pair sentences with their delimiters
    pairs = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences) and re.match(r'[.!?]\s+', sentences[i + 1]):
            pairs.append(sentences[i] + sentences[i + 1])
            i += 2
        else:
            pairs.append(sentences[i])
            i += 1

    rng.shuffle(pairs)
    return ''.join(pairs)


def remove_section(text: str, section_marker: str = "", **_) -> str:
    """Remove a section starting with a marker (e.g., '## Examples')."""
    if not section_marker:
        return text

    # Find section and remove until next section or end
    pattern = rf"{re.escape(section_marker)}.*?(?=\n##|\Z)"
    return re.sub(pattern, "", text, flags=re.DOTALL).strip()


# ============================================================================
# MAIA-SPECIFIC PERTURBATIONS
# ============================================================================

def change_iteration_count(text: str, max_iterations: int = 3, **_) -> str:
    """Change 'iterate until confident' to a fixed number of iterations."""
    # Target the instruction about iteration
    patterns = [
        (r"iterate until (?:you are )?confident", f"run exactly {max_iterations} iterations"),
        (r"continue until confident", f"run exactly {max_iterations} experiments"),
        (r"repeat.*?until confident", f"repeat exactly {max_iterations} times"),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def change_hypothesis_count(text: str, n_hypotheses: int = 1, **_) -> str:
    """Change 'generate multiple hypotheses' to a specific number."""
    patterns = [
        (r"generate multiple hypotheses", f"generate exactly {n_hypotheses} hypothesis" if n_hypotheses == 1 else f"generate exactly {n_hypotheses} hypotheses"),
        (r"multiple hypotheses", f"{n_hypotheses} hypothesis" if n_hypotheses == 1 else f"{n_hypotheses} hypotheses"),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def corrupt_output_format(text: str, **_) -> str:
    """Change the expected output format markers."""
    replacements = [
        ("[DESCRIPTION]", "[NEURON_DESCRIPTION]"),
        ("[LABEL]", "[TAGS]"),
        ("[CODE]", "[PYTHON_CODE]"),
        ("[HYPOTHESIS LIST]", "[HYPOTHESES]"),
    ]

    result = text
    for old, new in replacements:
        result = result.replace(old, new)

    return result


def remove_tool_documentation(text: str, tool_name: str = "edit_images", **_) -> str:
    """Remove documentation for a specific tool from api.txt."""
    # Match the tool definition and its docstring
    pattern = rf"def {re.escape(tool_name)}\([^)]*\):.*?(?=\n    def |\n\nclass |\Z)"
    return re.sub(pattern, "", text, flags=re.DOTALL)


def swap_tool_names(text: str, tool1: str = "text2image", tool2: str = "edit_images", **_) -> str:
    """Swap the names of two tools (keeps descriptions but swaps function names)."""
    # This is a simple swap - just exchange the function names
    # We use unique markers to avoid double-swapping
    marker1 = f"__TEMP_SWAP_{tool1.upper()}__"
    marker2 = f"__TEMP_SWAP_{tool2.upper()}__"

    result = text
    result = result.replace(f"def {tool1}(", f"def {marker1}(")
    result = result.replace(f"def {tool2}(", f"def {marker2}(")
    result = result.replace(f"def {marker1}(", f"def {tool2}(")
    result = result.replace(f"def {marker2}(", f"def {tool1}(")

    return result


# ============================================================================
# STRATEGY REGISTRY
# ============================================================================

STRATEGIES: dict[str, Callable] = {
    # Basic
    "replace_text": replace_text,
    "append_text": append_text,
    "prepend_text": prepend_text,

    # Noise
    "append_random": append_random,
    "remove_random_word": remove_random_word,
    "inject_typos": inject_typos,

    # Structural
    "shuffle_sentences": shuffle_sentences,
    "remove_section": remove_section,

    # MAIA-specific
    "change_iteration_count": change_iteration_count,
    "change_hypothesis_count": change_hypothesis_count,
    "corrupt_output_format": corrupt_output_format,
    "remove_tool_documentation": remove_tool_documentation,
    "swap_tool_names": swap_tool_names,
}