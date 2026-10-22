import pytest

from src.matching_benchmark import run_benchmark


def test_benchmark_executes_all_trades():
    results = run_benchmark(100)

    assert results["orders_matched"] == 100
    assert results["trade_count"] == 100
    assert results["elapsed_seconds"] > 0
    assert results["pairs_per_second"] > 0


def test_benchmark_reports_valid_latency_metrics():
    results = run_benchmark(100)

    assert results["average_latency_us"] > 0
    assert results["p99_latency_us"] > 0
    assert results["max_latency_us"] >= results["p99_latency_us"]


@pytest.mark.parametrize("count", [0, -1])
def test_benchmark_rejects_invalid_order_count(count):
    with pytest.raises(ValueError, match="positive"):
        run_benchmark(count)
