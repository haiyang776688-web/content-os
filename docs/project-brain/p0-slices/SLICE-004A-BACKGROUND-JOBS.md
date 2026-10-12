# Slice 4a · Local Background Jobs

**Date:** 2026-09-29  
**Branch:** `p0/gui-only-e2e-interim`  
**Status:** Jobs contract implemented; browser render and refresh verified on isolated synthetic data. This is not Track A or Track B acceptance.  
**Council:** D-001 remains OPEN/PENDING; `DECISIONS.md` is unchanged.

The ordinary Workbench now submits formal voice, storyboard stills, still/video render and Video QA through local background jobs. The request stores a job and returns its ID before the long operation. The worker performs preflight and execution. Job state survives browser refresh; an unfinished P0 job found after server restart becomes `FAILED / SERVER_RESTARTED` and can be retried. Repeated submissions for the same project, kind and target revision share the running/completed job. A render whose EDT changed during execution ends as `STALE`. The UI shows stage and elapsed time without a synthetic percentage. Existing synchronous endpoints remain for compatibility.

The job worker is an in-process thread backed by SQLite state. It does not resume the interrupted operation after a process restart; retry starts it again. This is deliberately narrower than a persistent queue. Remote Video QA still requires the existing provider authorization and upload consent, and is not silently sent to a cloud service.

## Browser evidence

Using isolated local test data and `PRJ-26c9693f0aff`, the ordinary Render page submitted a job and displayed `JOB-ed31fcd56dfa` as RUNNING. A browser refresh followed by navigating back to Render displayed the same job ID. The job completed and produced `ART-4ec64635817f4046`, a local 93.013-second MP4 (6,901,444 bytes); clicking Render again retained the same completed job ID and did not launch a second render. This sample is synthetic and 3 seconds above the later 60–90 second Track B target.

The render request initially spent noticeable time in preflight before returning the ID. Preflight and mechanical checks were moved into the worker after this observation. The browser proof above ran on the first server process; the faster submission path is covered by code inspection and tests, and should be rechecked on the restarted server before final acceptance.

## Verification and remaining work

`vnext/tests/test_p0_jobs.py` covers single-flight, refresh visibility from a new Store instance, stale target, failed retry and orphan recovery. The full suite reported 200 passed and one Starlette/httpx deprecation warning. JavaScript syntax and diff checks passed.

Slice 4 remains incomplete until the ordinary GUI exposes Mechanical/Visual QA details, H3 decisions with risk acknowledgments, MP4 download and Jianying transfer-bundle download. Track A and Track B also remain open.
