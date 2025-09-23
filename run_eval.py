import json
import os
from time import perf_counter
from bot.chain import get_chain


def evaluate() -> dict:
    with open(os.path.join("monitoring", "eval", "gold_qa.json"), "r", encoding="utf-8") as f:
        gold = json.load(f)["items"]

    chain = get_chain()

    results = []
    hit_count = 0
    total_latency_ms = 0.0
    duplicate_rates = []

    for item in gold:
        q = item["question"]
        expected_keywords = set(k.lower() for k in item.get("expected_keywords", []))
        start = perf_counter()
        out = chain.invoke({"question": q})
        latency_ms = (perf_counter() - start) * 1000.0
        total_latency_ms += latency_ms

        answer = out.get("answer", "") or ""
        docs = out.get("source_documents", []) or []

        # Simple retrieval duplicate rate (by page or metadata source)
        ids = []
        for d in docs:
            meta = getattr(d, "metadata", {}) or {}
            id_str = str(meta.get("source", "")) + ":" + str(meta.get("page", meta.get("page_number", "")))
            ids.append(id_str)
        unique = len(set(ids)) if ids else 0
        dup_rate = 1.0 - (unique / len(ids)) if ids else 0.0
        duplicate_rates.append(dup_rate)

        # Naive hit check: keyword overlap with answer
        present = sum(1 for k in expected_keywords if k in answer.lower())
        hit = present >= max(1, int(0.5 * len(expected_keywords))) if expected_keywords else False
        if hit:
            hit_count += 1

        results.append({
            "question": q,
            "latency_ms": round(latency_ms, 2),
            "duplicate_rate": round(dup_rate, 3),
            "hit": hit
        })

    summary = {
        "n": len(gold),
        "hit_rate": round(hit_count / max(1, len(gold)), 3),
        "avg_latency_ms": round(total_latency_ms / max(1, len(gold)), 2),
        "avg_duplicate_rate": round(sum(duplicate_rates) / max(1, len(duplicate_rates)), 3),
        "results": results,
    }
    return summary


if __name__ == "__main__":
    s = evaluate()
    print(json.dumps(s, ensure_ascii=False, indent=2))


