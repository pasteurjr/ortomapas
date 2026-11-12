"""Provider usage aggregation for audit records; never includes prompt content."""


def anthropic_usage_summary(client):
    records = getattr(client, "call_records", None) or []
    if not records:
        return None
    known = [record for record in records if record.get("usage_available") and isinstance(record.get("usage"), dict)]
    input_tokens = sum(int(record["usage"].get("input_tokens", 0)) for record in known)
    output_tokens = sum(int(record["usage"].get("output_tokens", 0)) for record in known)
    estimated_cost = round(sum(float(record.get("estimated_cost_usd", 0)) for record in known), 8)
    return {
        "provider": "anthropic",
        "model": next((record.get("model") for record in records if record.get("model")), None),
        "calls": len(records),
        "responses_with_usage": len(known),
        "usage_unavailable_calls": len(records) - len(known),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimated_cost,
        "billing_complete": len(known) == len(records),
        "stop_reasons": [record.get("stop_reason") for record in known if record.get("stop_reason")],
        "failed_call_statuses": [record.get("status") for record in records if record.get("status") != "response_received"],
    }
