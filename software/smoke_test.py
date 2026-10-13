"""HTTP reachability/response-shape smoke test; not a model leaderboard."""
import json, os, time, urllib.error, urllib.request
url=os.getenv('ARIES_API_URL','').strip(); key=os.getenv('ARIES_API_KEY','').strip()
if not url: raise SystemExit('NOT RUN: set ARIES_API_URL to your actual inference endpoint first.')
payload={'model':os.getenv('ARIES_MODEL','aries-model'),'messages':[{'role':'user','content':'Reply with exactly: ARIES_SMOKE_TEST_OK'}],'temperature':0,'max_tokens':30}
headers={'Content-Type':'application/json'}
if key: headers['Authorization']='Bearer '+key
req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=headers,method='POST'); start=time.perf_counter()
try:
 with urllib.request.urlopen(req,timeout=60) as response:
  elapsed=(time.perf_counter()-start)*1000; body=response.read().decode('utf-8',errors='replace'); print(f'HTTP status: {response.status}'); print(f'Request latency: {elapsed:.2f} ms (single request; not a benchmark)')
  try: data=json.loads(body)
  except json.JSONDecodeError: raise SystemExit('FAIL: endpoint returned non-JSON response')
  if not isinstance(data,dict): raise SystemExit('FAIL: JSON response is not an object')
  if not any(k in data for k in ('choices','output','response')): print(json.dumps(data,indent=2)[:2000]); raise SystemExit('FAIL: unexpected response shape')
  print('PASS: endpoint returned a recognized response field.'); print(json.dumps(data,indent=2)[:2000])
except urllib.error.HTTPError as e: print(f'FAIL: HTTP {e.code}: {e.reason}'); print(e.read().decode('utf-8',errors='replace')[:2000]); raise SystemExit(1)
except (urllib.error.URLError,TimeoutError) as e: raise SystemExit(f'FAIL: endpoint request failed: {e}')
