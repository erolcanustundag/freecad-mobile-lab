#!/usr/bin/env python3
import resource,subprocess,time,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
start=time.monotonic();result=subprocess.run(['bash',str(root/'scripts/run_host_tests.sh')]);usage=resource.getrusage(resource.RUSAGE_CHILDREN)
print(json.dumps({'host_elapsed_seconds':round(time.monotonic()-start,2),'host_peak_child_rss_kib':usage.ru_maxrss,'exit_code':result.returncode,'scope':'host Linux regression workload; not an Android memory measurement'}))
raise SystemExit(result.returncode)
