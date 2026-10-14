#!/usr/bin/env python3
"""Generate a portable ARIES diagnostic scorecard from benchmark JSON. Not an official leaderboard."""
import argparse, csv, html, json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input", default="reports/aries-scorecard.json")
    p.add_argument("--html", default="reports/aries-scorecard.html")
    p.add_argument("--csv", default="reports/aries-scorecard.csv")
    a=p.parse_args()
    data=json.loads(Path(a.input).read_text(encoding="utf-8"))
    summary=data.get("summary", {})
    results=data.get("results", [])
    Path(a.html).parent.mkdir(parents=True, exist_ok=True)
    Path(a.csv).parent.mkdir(parents=True, exist_ok=True)
    fields=["id","category","http_status","passed_exact_match","latency_ms","expected","actual","error"]
    with Path(a.csv).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    def metric(label, value):
        return '<div class="metric"><span>'+html.escape(label)+'</span><strong>'+html.escape(str(value if value is not None else "N/A"))+'</strong></div>'
    rows=[]
    for r in results:
        passed=r.get("passed_exact_match")
        status="PASS" if passed is True else ("FAIL" if passed is False else "NO RESPONSE")
        vals=[r.get("id",""),r.get("category",""),status,r.get("http_status",""),r.get("latency_ms",""),r.get("expected",""),r.get("actual",r.get("error",""))]
        rows.append("<tr>"+"".join("<td>"+html.escape(str(v if v is not None else ""))+"</td>" for v in vals)+"</tr>")
    accuracy=(str(summary.get("exact_match_accuracy_percent"))+"%") if summary.get("exact_match_accuracy_percent") is not None else "N/A"
    doc='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ARIES Diagnostic Scorecard</title><style>
body{font:16px system-ui,sans-serif;max-width:1200px;margin:32px auto;padding:0 18px;color:#172033}
h1{margin-bottom:4px}.muted{color:#536176}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:22px 0}
.metric{border:1px solid #d8dee9;border-radius:10px;padding:14px}.metric span{display:block;color:#536176;font-size:13px}.metric strong{font-size:23px}
.notice{border-left:4px solid #b7791f;padding:12px;background:#fff8e8}.tablewrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:9px;border-bottom:1px solid #e1e6ef;vertical-align:top;overflow-wrap:anywhere}th{background:#f3f5f8}
</style></head><body>'''
    doc += '<h1>ARIES Diagnostic Scorecard</h1><p class="muted">Target: '+html.escape(str(data.get("base_url","unknown")))+' | Model: '+html.escape(str(data.get("requested_model","unknown")))+' | Run: '+html.escape(str(data.get("timestamp_utc","unknown")))+'</p>'
    doc += '<div class="notice"><strong>Scope:</strong> Small ARIES-authored diagnostic suite. Not an independent certification, official MMLU/GSM8K/BBH benchmark, or accepted public leaderboard ranking.</div><div class="metrics">'
    doc += metric("Exact-match accuracy",accuracy)
    doc += metric("Exact-match passes",str(summary.get("exact_match_passes",0))+" / "+str(summary.get("cases_with_model_response",0)))
    doc += metric("Non-empty responses",str(summary.get("nonempty_responses",0))+" / "+str(summary.get("cases_requested",0)))
    doc += metric("Median latency (ms)",summary.get("latency_median_ms"))
    doc += metric("Mean latency (ms)",summary.get("latency_mean_ms"))
    doc += metric("Max latency (ms)",summary.get("latency_max_ms"))
    doc += '</div><h2>Per-case results</h2><div class="tablewrap"><table><thead><tr><th>Case</th><th>Category</th><th>Result</th><th>HTTP</th><th>Latency ms</th><th>Expected</th><th>Actual / error</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
    doc += '<p class="muted">Reproduce with python tools/aries_bench.py --base-url https://aries-tier0-api-6qjh.onrender.com --model aries-native-ngram --limit 10 --output reports/aries-scorecard.json, then run tools/aries_scorecard.py.</p></body></html>'
    Path(a.html).write_text(doc, encoding="utf-8")
    print("Scorecard HTML:",a.html)
    print("Case CSV:",a.csv)
    print(json.dumps(summary, indent=2))
if __name__=="__main__": main()
