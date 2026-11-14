import json, os, math, glob

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.644854, -0.67449, 0.0, 0.67449, 1.644854]

def clamp6(x):
    return round(min(1.0, max(0.0, x)) * 1e6) / 1e6

def estimate_sigma(prices):
    if len(prices) < 10:
        return 0.0025
    diffs = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    diffs = [d for d in diffs if d != 0.0]
    if len(diffs) < 5:
        return 0.0025
    var = sum(d*d for d in diffs) / len(diffs)
    s = math.sqrt(var)
    return max(0.0005, min(0.01, s))

def estimate_drift(prices):
    if len(prices) < 60:
        return 0.0
    n = min(120, len(prices))
    recent = prices[-n:]
    slope = (recent[-1] - recent[0]) / n
    return slope * 0.3

def forecast_market(market, horizon):
    prices = market["prices"]
    if not prices:
        return [[0.5]*5 for _ in range(horizon)]
    x = prices[-1]
    sigma = estimate_sigma(prices)
    drift = estimate_drift(prices)
    rows = []
    for h in range(1, horizon + 1):
        center = x + drift * h
        spread = sigma * math.sqrt(h)
        row = [clamp6(center + z * spread) for z in Z]
        for i in range(1, len(row)):
            if row[i] < row[i-1]:
                row[i] = row[i-1]
        rows.append(row)
    return rows

inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
for fname in inputs:
    case_id = fname[:-3]
    with open(os.path.join(INPUT_DIR, fname)) as f:
        case = json.load(f)
    horizon = case["horizon_minutes"]
    forecasts = []
    for m in case["markets"]:
        q = forecast_market(m, horizon)
        forecasts.append({"id": m["id"], "q": q})
    with open(os.path.join(OUTPUT_DIR, f"{case_id}.out"), "w") as f:
        f.write(json.dumps({"forecasts": forecasts}) + "\n")
