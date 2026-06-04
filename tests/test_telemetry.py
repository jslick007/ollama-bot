import pytest
import json
from src.telemetry import TelemetryCollector

@pytest.fixture
def telemetry():
    return TelemetryCollector(log_to_stdout=False)

def test_record_llm_call(telemetry):
    telemetry.record_llm_call("gpt-3.5-turbo", 100, 50, 200.0)
    assert len(telemetry.calls) == 1
    assert telemetry.total_prompt_tokens == 100
    assert telemetry.total_completion_tokens == 50
    assert telemetry.total_cost > 0

def test_cost_estimation(telemetry):
    telemetry.record_llm_call("gpt-4", 1000, 500, 150.0)
    expected_cost = (1000 / 1000 * 0.03) + (500 / 1000 * 0.06)
    assert telemetry.total_cost == expected_cost

def test_report(telemetry):
    telemetry.record_llm_call("gpt-3.5-turbo", 200, 100, 300.0)
    telemetry.record_llm_call("gpt-3.5-turbo", 300, 150, 400.0)
    report = telemetry.report()
    assert report["total_calls"] == 2
    assert report["total_tokens"] == 750
    assert report["average_latency_ms"] == 350.0

def test_reset(telemetry):
    telemetry.record_llm_call("gpt-3.5-turbo", 100, 50, 100.0)
    telemetry.reset()
    assert len(telemetry.calls) == 0
    assert telemetry.total_prompt_tokens == 0
    assert telemetry.total_cost == 0.0

def test_custom_pricing():
    pricing = {"custom-model": {"input": 0.005, "output": 0.01}}
    t = TelemetryCollector(pricing=pricing, log_to_stdout=False)
    t.record_llm_call("custom-model", 1000, 500, 200.0)
    expected = (1000 / 1000 * 0.005) + (500 / 1000 * 0.01)
    assert t.total_cost == expected
