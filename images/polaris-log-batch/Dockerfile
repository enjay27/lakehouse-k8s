# polaris-log-batch -- the hourly Polaris log batch as its own image.
#
# Built and released separately from Polaris (Kade, 2026-09-28): the job has its own image, its own
# chart (charts/polaris-log-batch) and its own Helm release. Polaris's chart knows nothing about it;
# the only thing the two share is the log PVC (logging/k8s/polaris-logs-pvc.yaml).
#
#   docker build -t polaris-log-batch:0.1.0 images/polaris-log-batch
#
# On OrbStack the cluster sees images from the local Docker daemon, so no push is needed.
# Standard library only: nothing to pip install.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY polaris_log_batch.py /app/polaris_log_batch.py

# Same uid/gid as the Polaris container, so the files it moves and writes on the shared PVC keep one
# owner. The chart sets the same values in securityContext; this is the default without it.
USER 10000:10001

ENTRYPOINT ["python3", "/app/polaris_log_batch.py"]
