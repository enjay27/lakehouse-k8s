# Active Infrastructure State

## Current Context & Objective
- **Goal:** Maintain, scale, and secure a hybrid local platform environment utilizing Docker Compose for indexing and Helm for core Kubernetes data services inside the `datahub-hynix` namespace.
- **Current Focus:** Ensuring stable cross-networking between Docker-Compose OpenSearch and the K8s-based Polaris/FluentBit services.

## Active State & Roadmap
- [x] **OpenSearch (v1.5.0):** Deployed and running stably via Docker Compose.
- [ ] **Task 1:** Validate target `datahub-hynix` namespace parameters and align PostgreSQL HA and Apache Polaris Helm charts.
- [ ] **Task 2:** Configure FluentBit DaemonSet inside `datahub-hynix` to route local cluster transaction logs smoothly into the Docker-hosted OpenSearch container endpoint.
- [ ] **Task 3:** Audit the remaining `values.yaml` configurations for the uninstalled DataHub and DataHub-Prerequisites (Kafka, ElasticSearch, MySql) blocks to prepare for future staging.

## Active Issues & Blockers
- **Resource Constraints:** Combined platform services require a high local hardware allocation footprint (>7GB RAM) once DataHub components are activated on the daemon node.

---
*Note to Claude: Keep this file under 150 lines. Focus exclusively on architecture layouts, deployment variables, and cluster state deltas.*