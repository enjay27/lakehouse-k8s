#!/usr/bin/env python3
"""Does the capture tail survive being started the way notebook 03 starts it?

    uv run python probe_capture_liveness.py

Costs no Polaris restart and no drive. It starts a capture twice, the second
time differing from the first by ONE argument, and asks each time whether the
tail is still recording afterwards.

WHY TWO ARMS THAT DIFFER BY ONE ARGUMENT. Seven captures taken through notebook
03 on 2026-09-01 hold 25 lines each -- an OAuth exchange, 19 statements, and
cell 9b's own `list_catalogs` liveness probe -- and nothing after it. A drive
taken 2026-09-02 into a capture started from a TERMINAL recorded 859 lines with
the tail alive. Three theories about the tail (the 1.29 MB `listCatalogs
returning:` line, a rollout orphaning it, `settle_s`) were each refuted by
measurement; see `HANDOFF-api-index-matrix.md` §1.2 so they are not re-tested.
What survives is the one difference between those two runs: the notebook starts
the tails through

    subprocess.run(cmd, shell=True, capture_output=True)      # cell 5's sh()

and a terminal does not capture the output. So:

    arm A  capture_output=True   -- the notebook's sh(), exactly
    arm B  capture_output=False  -- inherited stdio, what a terminal does

Nothing else differs. If A stops recording and B keeps recording, the fault is
in how sh() backgrounds the tails and the fix is to detach them
(`setsid`/`nohup`, or `start_new_session=True`) -- not to touch the drive.

WHY THE ARMS RUN SEQUENTIALLY, NEVER IN PARALLEL. `capture.sh do_stop` reaps
strays with `pgrep -f "kubectl.*-n $NS.*logs.*-f"`, which matches every such
tail on the machine rather than only the ones it started. Two arms at once
would kill each other and both would read as the fault.

WHAT EACH ARM MEASURES. Liveness is not the PID. A `kubectl logs -f` that is
alive but no longer following looks identical to a healthy one from `kill -0`,
and the broken captures are consistent with either. So each arm:

  1. starts the capture through its own mechanism;
  2. issues ONE `list_catalogs` -- the same call cell 9b's gate makes, and the
     last thing present in all seven broken captures;
  3. waits, issuing nothing, for --watch seconds;
  4. issues five more calls and asks whether the log GREW.

Step 4 is the verdict. A tail whose PID is alive and whose log does not grow is
a stopped stream, and that is a different fault from a dead process -- the run
prints which of the two it saw.

IF BOTH ARMS RECORD, sh() is exonerated and the next suspect is the Jupyter
kernel's own process handling. The probe for that is the notebook itself: run
cell 19, run nothing else, and poll from a terminal.
"""

import argparse
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))


def tail_pid(capture):
    """The polaris tail's PID, from the `.pids` file capture.sh writes."""
    pf = pathlib.Path(capture) / ".pids"
    if not pf.exists():
        return None
    for line in pf.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == "polaris":
            return int(parts[0])
    return None


def alive(pid):
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def size(capture):
    p = pathlib.Path(capture) / "polaris.log"
    return p.stat().st_size if p.exists() else 0


def lines(capture):
    p = pathlib.Path(capture) / "polaris.log"
    if not p.exists():
        return 0
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def start_capture(dirname, capture_output):
    """`./capture.sh start <dir>`, with capture_output the ONLY variable.

    `check=False`: rotate/start returns non-zero if ANY stream failed, and one
    of them is a MinIO trace this probe never reads. Failing here on it would
    be a false blocker -- the gate is whether the polaris tail records.
    """
    return subprocess.run(
        f"./capture.sh start {dirname}",
        shell=True,
        cwd=str(HERE),
        capture_output=capture_output,
        text=True,
    )


def client():
    from polaris_rest import PolarisREST
    from polaris_test_utils import POLARIS_URL, REALM, init_env, root_token

    init_env("local")
    return PolarisREST(POLARIS_URL, REALM, token=root_token())


def run_arm(label, capture_output, watch, quiet_cheap=5):
    stamp = datetime.now().strftime("%H%M%S")
    cap = HERE / f"capture-live{label}-{stamp}"
    print(
        f"\n{'=' * 68}\narm {label}: capture_output={capture_output}  ->  {cap.name}\n{'=' * 68}"
    )

    subprocess.run("./capture.sh stop", shell=True, cwd=str(HERE), capture_output=True)
    start_capture(cap.name, capture_output)
    time.sleep(3)  # let the tails attach

    pid = tail_pid(cap)
    print(f"  tail pid: {pid}")
    if pid is None:
        print("  ! no polaris pid recorded -- capture.sh did not start it.")
        return {"arm": label, "verdict": "NO TAIL", "grew": 0, "alive": False}

    pc = client()

    # The gate's own call. This is the last thing present in all seven broken
    # captures, so it is the event under suspicion -- not a warm-up.
    print(f"  gate probe: list_catalogs -> {pc.list_catalogs().status_code}")
    time.sleep(4)
    after_probe = size(cap)
    print(
        f"  after probe: {lines(cap):,} lines, {after_probe:,} bytes, "
        f"tail {'alive' if alive(pid) else 'DEAD'}"
    )

    print(f"  watching {watch}s, issuing nothing ...")
    for i in range(watch):
        time.sleep(1)
        if not alive(pid):
            print(f"  ! tail DIED while idle, {i + 1}s after the probe")
            break

    before_cheap = size(cap)
    for _ in range(quiet_cheap):
        pc.get_config()  # 400 on this build, and still logs -- fine
        time.sleep(0.4)
    time.sleep(4)
    grew = size(cap) - before_cheap

    still = alive(pid)
    if grew > 0:
        verdict = "RECORDING"
    elif still:
        verdict = "STOPPED STREAM (pid alive, log frozen)"
    else:
        verdict = "TAIL DEAD"
    print(
        f"  final: {lines(cap):,} lines, {size(cap):,} bytes, "
        f"grew {grew:,} bytes on {quiet_cheap} calls, "
        f"tail {'alive' if still else 'DEAD'}"
    )
    print(f"  VERDICT: {verdict}")
    return {
        "arm": label,
        "verdict": verdict,
        "grew": grew,
        "alive": still,
        "dir": cap.name,
    }


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--watch",
        type=int,
        default=45,
        help="seconds to idle between the gate probe and the "
        "recording check (default 45)",
    )
    args = ap.parse_args()

    a = run_arm("A", True, args.watch)
    b = run_arm("B", False, args.watch)

    print(f"\n{'=' * 68}\nRESULT\n{'=' * 68}")
    for r in (a, b):
        print(f"  arm {r['arm']}: {r['verdict']}")
    print()
    if a["verdict"] != "RECORDING" and b["verdict"] == "RECORDING":
        print("  CONFIRMED: sh()'s capture_output=True is what stops the tail.")
        print("  Fix: detach the tails in capture.sh (setsid/nohup), or start")
        print("  them with start_new_session=True. Do not change the drive.")
    elif a["verdict"] == "RECORDING" and b["verdict"] == "RECORDING":
        print("  sh() is EXONERATED -- both arms record. The next suspect is")
        print("  the Jupyter kernel's own process handling. Probe: run cell 19,")
        print("  run nothing else, and poll the tail from a terminal.")
    elif a["verdict"] != "RECORDING" and b["verdict"] != "RECORDING":
        print("  NEITHER arm records -- the fault is upstream of both and this")
        print("  probe cannot see it. Check ./capture.sh preflight and whether")
        print("  the cluster is serving; do not read this as a notebook fault.")
    else:
        print("  Arm B failed where A succeeded -- unexpected. Keep both")
        print("  directories and read them before drawing anything from this.")
    print("\n  capture dirs kept for inspection; ./capture.sh stop when done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
