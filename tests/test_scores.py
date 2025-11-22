import math
from typing import List, Optional
import pytest

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

def retrieval_score(similarities_01: List[float]) -> float:
    if not similarities_01:
        return 0.0
    num = den = 0.0
    for i, sim in enumerate(similarities_01, start=1):
        w = 1.0 / math.log(i + 1.0)
        num += w * clamp01(sim)
        den += w
    return clamp01(num / den) if den > 0 else 0.0

def consistency_score(resp_chunk_sim_01: List[float]) -> float:
    return clamp01(sum(resp_chunk_sim_01) / len(resp_chunk_sim_01)) if resp_chunk_sim_01 else 0.0

def faithfulness_score(n_unsupported: int, n_total: int, eps: float = 1e-6) -> float:
    if n_total <= 0:
        return 1.0
    return clamp01(1.0 - (n_unsupported / (n_total + eps)))

def fact_score(entail_probs_01: List[float], weights: Optional[List[float]] = None) -> float:
    if not entail_probs_01:
        return 0.0
    if weights is None:
        return clamp01(sum(entail_probs_01) / len(entail_probs_01))
    wsum = sum(max(0.0, w) for w in weights[:len(entail_probs_01)])
    if wsum == 0:
        return clamp01(sum(entail_probs_01) / len(entail_probs_01))
    num = sum(clamp01(p) * max(0.0, w) for p, w in zip(entail_probs_01, weights))
    return clamp01(num / wsum)

def confidence_score(Rs: float, Cs: float, Fs: float, FS: float,
                     alpha: float = 0.40, beta: float = 0.25,
                     gamma: float = 0.20, delta: float = 0.15) -> float:
    s = alpha + beta + gamma + delta
    if s <= 0:
        s = 1.0
    alpha, beta, gamma, delta = alpha/s, beta/s, gamma/s, delta/s
    sc = (alpha * clamp01(Rs) +
          beta * clamp01(Cs) +
          gamma * clamp01(Fs) +
          delta * clamp01(FS))
    return clamp01(sc)

# Testes unitários
def test_retrieval_score():
    sims = [0.9, 0.8, 0.7]
    assert 0.7 < retrieval_score(sims) <= 0.9

def test_consistency_score():
    sims = [0.5, 0.7, 0.9]
    assert consistency_score(sims) == pytest.approx(0.7)

def test_faithfulness_score():
    assert faithfulness_score(1, 4) == pytest.approx(0.75)
    assert faithfulness_score(0, 0) == 1.0

def test_fact_score():
    probs = [0.8, 0.6, 0.9]
    weights = [1, 2, 1]
    assert fact_score(probs) == pytest.approx(0.7666, rel=1e-2)
    assert fact_score(probs, weights) == pytest.approx(0.725, rel=1e-2)

def test_confidence_score():
    Rs, Cs, Fs, FS = 0.8, 0.7, 0.9, 0.6
    score = confidence_score(Rs, Cs, Fs, FS)
    assert 0.7 < score < 0.9

def test_faithfulness_score_ragas():
    Fs = 0.85
    assert clamp01(Fs) == 0.85
