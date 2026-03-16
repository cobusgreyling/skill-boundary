# Skill Boundary Exploration Report

**API:** DevForge Platform API (v2)
**Resources:** 8
**Operations:** 44
**Auth levels:** admin_key, api_key, deploy_key, maintainer_key
**Model:** NVIDIA Nemotron 3 Super (120B/12B active)

---

## Capability Analysis

### 1. CAPABILITY MAP  
**Audit‑Log**  
- **Query audit log** – `GET /audit-log` – auth: `admin_key`  

**Deployments**  
- **List deployments** – `GET /deployments` – auth: `api_key`  
- **Trigger deployment** – `POST /deployments` – auth: `deploy_key`  
- **Get deployment status** – `GET /deployments/{id}` – auth: `api_key`  
- **Rollback deployment** – `DELETE /deployments/{id}` – auth: `deploy_key`  
- **Get deployment logs** – `GET /deployments/{id}/logs` – auth: `api_key`  

**Environments**  
- **List environments** – `GET /environments` – auth: `api_key` (filter by `repo_id`)  
- **Create environment** – `POST /environments` – auth: `admin_key`  
- **Get environment details** – `GET /environments/{id}` – auth: `api_key`  
- **Update environment config** – `PATCH /environments/{id}` – auth: `admin_key` (fields: `protection_rules`, `variables`)  
- **Delete environment** – `DELETE /environments/{id}` – auth: `admin_key`  

**Pipelines**  
- **List CI/CD pipelines** – `GET /pipelines` – auth: `api_key` (filters: `repo_id`, `status`, `trigger`)  
- **Create pipeline** – `POST /pipelines` – auth: `maintainer_key`  
- **Get pipeline details** – `GET /pipelines/{id}` – auth: `api_key`  
- **Update pipeline config** – `PATCH /pipelines/{id}` – auth: `maintainer_key` (fields: `stages`, `triggers`, `enabled`)  
- **Delete pipeline** – `DELETE /pipelines/{id}` – auth: `admin_key`  
- **List pipeline runs** – `GET /pipelines/{id}/runs` – auth: `api_key` (filters: `status`, `branch`)  
- **Trigger pipeline run** – `POST /pipelines/{id}/runs` – auth: `api_key` (params: `branch`, `variables`)  
- **Get pipeline run details & logs** – `GET /pipelines/{id}/runs/{run_id}` – auth: `api_key`  
- **Cancel pipeline run** – `DELETE /pipelines/{id}/runs/{run_id}` – auth: `api_key`  

**Repositories**  
- **List repositories** – `GET /repos` – auth: `api_key` (params: `limit`, `offset`, `visibility`, `language`)  
- **Create repository** – `POST /repos` – auth: `api_key`  
- **Get repository details** – `GET /repos/{id}` – auth: `api_key`  
- **Update repository settings** – `PATCH /repos/{id}` – auth: `api_key` (fields: `description`, `visibility`, `archived`)  
- **Delete repository** – `DELETE /repos/{id}` – auth: `admin_key`  
- **List branches** – `GET /repos/{id}/branches` – auth: `api_key`  
- **Create branch** – `POST /repos/{id}/branches` – auth: `api_key` (params: `name`, `source_branch`)  
- **List commits** – `GET /repos/{id}/commits` – auth: `api_key` (params: `branch`, `since`, `until`, `author`)  
- **List pull requests** – `GET /repos/{id}/pull-requests` – auth: `api_key` (params: `state`, `author`, `reviewer`)  
- **Create pull request** – `POST /repos/{id}/pull-requests` – auth: `api_key` (params: `title`, `description`, `source_branch`, `target_branch`, `reviewers`)  
- **Get pull request details** – `GET /repos/{id}/pull-requests/{pr_id}` – auth: `api_key`  
- **Update pull request** – `PATCH /repos/{id}/pull-requests/{pr_id}` – auth: `api_key` (fields: `title`, `description`, `state`, `reviewers`)  
- **Merge pull request** – `POST /repos/{id}/pull-requests/{pr_id}/merge` – auth: `maintainer_key` (params: `strategy`, `delete_branch`)  

**Secrets**  
- **List secret names (values hidden)** – `GET /secrets` – auth: `maintainer_key` (params: `scope`, `repo_id`)  
- **Create secret** – `POST /secrets` – auth: `admin_key` (params: `name`, `value`, `scope`, `repo_id`)  
- **Rotate secret value** – `PATCH /secrets/{id}` – auth: `admin_key` (param: `value`)  
- **Delete secret** – `DELETE /secrets/{id}` – auth: `admin_key`  

**Users**  
- **List platform users** – `GET /users` – auth: `api_key` (params: `role`, `team`)  
- **Get user profile** – `GET /users/{id}` – auth: `api_key`  
- **Update user role** – `PATCH /users/{id}` – auth: `admin_key` (fields: `role`, `teams`)  

**Webhooks**  
- **List webhooks** – `GET /webhooks` – auth: `api_key` (param: `repo_id`)  
- **Register webhook** – `POST /webhooks` – auth: `maintainer_key` (params: `repo_id`, `url`, `events`, `secret`)  
- **Update webhook** – `PATCH /webhooks/{id}` – auth: `maintainer_key` (fields: `url`, `events`, `active`)  
- **Delete webhook** – `DELETE /webhooks/{id}` – auth: `maintainer_key`  

---

### 2. BUILDABLE APPLICATIONS  

| # | Application / Integration | What it does | Endpoints used | Auth needed | Feasibility |
|---|---------------------------|--------------|----------------|-------------|-------------|
| 1 | **CI/CD Dashboard** | Shows repo‑level pipelines, recent runs, deployment status, and logs in a single UI. | `GET /repos/{id}/pipelines`, `GET /pipelines/{id}/runs`, `GET /pipelines/{id}/runs/{run_id}`, `GET /deployments`, `GET /deployments/{id}/logs` | `api_key` (all read‑only) | **High** – only read endpoints, well‑within rate limits. |
| 2 | **Environment‑as‑Code Provisioner** | Reads a YAML definition and creates/updates environments, then triggers a deployment to validate. | `GET /environments` (list), `POST /environments` (create), `PATCH /environments/{id}` (update), `POST /deployments` (trigger) | `admin_key` for env create/update, `deploy_key` for trigger | **Medium** – requires two privileged keys; orchestration needed to handle async deployment readiness. |
| 3 | **Secret Rotation Bot** | Rotates secrets on a schedule: lists secrets, generates new values, calls rotate, and notifies via webhook. | `GET /secrets` (list), `PATCH /secrets/{id}` (rotate), `POST /webhooks` (notify) | `maintainer_key` for list, `admin_key` for rotate | **Medium** – rotate needs admin_key; list needs maintainer_key. Secure storage of new values required. |
| 4 | **PR Merge Automation** | When a PR passes CI (checked via pipeline runs), automatically merges it and optionally deletes the source branch. | `GET /repos/{id}/pull-requests` (filter by state), `GET /pipelines/{id}/runs` (check status), `POST /repos/{id}/pull-requests/{pr_id}/merge` (merge), `DELETE /repos/{id}/branches` (if delete_branch=true) | `api_key` for PR list & pipeline runs, `maintainer_key` for merge | **High** – all needed auth levels are commonly available to repo maintainers. |
| 5 | **Audit‑Log Compliance Exporter** | Periodically pulls audit‑log entries for a date range and writes them to a SIEM or storage bucket. | `GET /audit-log` (query with actor/action/resource/date filters) | `admin_key` | **Low** – only admins can call audit‑log; rate limit 200 req/min is generous but still a bottleneck for large orgs. |

---

### 3. SKILL BOUNDARY — WHAT I CANNOT DO  

- **Read secret values** – The API only returns secret *names* (`GET /secrets`). Actual values are never exposed; rotation (`PATCH`) requires the new value to be supplied by the caller, but you cannot retrieve the current value.  
- **Execute arbitrary code or shell commands** – No endpoint for running scripts, SSH access, or container exec; you can only trigger CI/CD pipelines or deployments that you have pre‑configured.  
- **Manage authentication credentials** – No endpoints to create, rotate, or revoke `api_key`, `maintainer_key`, `deploy_key`, or `admin_key`. Those must be provisioned outside the API (e.g., via admin console).  
- **Access billing, usage, or invoice data** – No endpoints for cost reporting, quota management, or payment methods.  
- **Modify core platform settings** (e.g., global rate‑limit policies, authentication providers, SSO config) – Only repo‑, environment‑, pipeline‑, and secret‑scoped configs are mutable.  
- **Delete a deployment record** – You can rollback (`DELETE /deployments/{id}`) but there is no endpoint to permanently purge deployment history.  
- **Directly access raw build artifacts or container images** – Logs are available, but artifact storage/download is not exposed.  
- **Create or manage teams at platform scope** – User endpoints let you list users and update roles/teams, but there is no endpoint to create a new team or modify team membership beyond the `teams` field on a user (which likely requires pre‑existing team IDs).  
- **Perform bulk operations** – No batch endpoints; each repo, environment, secret, etc., must be processed individually.  

---

### 4. COMPOSITE WORKFLOWS  

**Workflow A – “Create Repo → Setup Environment → Deploy → Verify”**  
1. `POST /repos` – create repository (returns `repo_id`).  
2. `POST /environments` – create environment for that `repo_id` (requires `admin_key`).  
3. `POST /deployments` – trigger deployment using the new repo’s `default_branch` and the environment ID (requires `deploy_key`).  
4. `GET /deployments/{id}` – poll until status = `success`.  
5. `GET /deployments/{id}/logs` – fetch logs for verification.  

**Workflow B – “CI Pipeline Run → Cancel on Failure → Notify via Webhook”**  
1. `POST /pipelines/{id}/runs` – trigger a pipeline run (branch + variables).  
2. `GET /pipelines/{id}/runs/{run_id}` – poll for status.  
3. If status = `failed` or timeout, `DELETE /pipelines/{id}/runs/{run_id}` – cancel the run.  
4. `POST /webhooks` – (or `PATCH` existing) send a payload to a notification URL (requires `maintainer_key` to register/update).  

**Workflow C – “PR Lifecycle: List → Merge → Cleanup Branch”**  
1. `GET /repos/{id}/pull-requests` – list open PRs (filter by `state=open`).  
2. For a target PR, `POST /repos/{id}/pull-requests/{pr_id}/merge` – merge with `delete_branch=true` (requires `maintainer_key`).  
3. (Optional) `GET /repos/{id}/branches` – confirm source branch removed; if not, `DELETE /repos/{id}/branches/{branch_name}` – delete branch (requires `api_key`).  

---

### 5. INTEGRATION RISKS  

- **Rate‑limit throttling** –  
  - `api_key`: 100 req/min – safe for read‑heavy dashboards but can be hit when polling many repos/pipelines.  
  - `maintainer_key`: 60 req/min – becomes a bottleneck for secret‑list/rotate loops or bulk webhook management.  
  - `deploy_key`: 30 req/min – limits rapid deployment triggering; CI systems must back‑off or batch.  
  - `admin_key`: 200 req/min – highest ceiling, but admin‑only ops (audit‑log, env creation) are infrequent; still risk if many admins share a key.  

- **Authentication barriers** –  
  - Privileged actions (environment creation, secret rotation, audit‑log, repo deletion) require `admin_key` or `maintainer_key`. If your service only possesses a standard `api_key`, those flows are impossible without key elevation.  
  - Key rotation is not exposed; compromised keys must be revoked outside the API, creating a window of misuse.  

- **Partial data visibility** – Secrets endpoint hides values; you cannot verify that a secret is correctly set without relying on the consuming system’s behavior.  

- **Eventual consistency** – After creating an environment or triggering a deployment, the API may return immediately while the underlying provisioning is still in progress. Polling or webhook callbacks are required to avoid race conditions.  

- **Error handling granularity** – The spec does not detail error payloads; assuming generic HTTP statuses, developers must implement robust retry/idempotency logic (especially for POST/PUT/PATCH actions).  

- **Dependency on external systems** – Webhooks require a publicly reachable URL and secret verification; if the receiver is down, events are lost unless the platform provides a retry mechanism (not documented).  

- **Pagination & large result sets** – List endpoints (`/repos`, `/environments`, `/audit-log`) accept `limit`/`offset` but no cursor‑based continuation; large orgs may need many requests, increasing rate‑limit pressure.  

- **No bulk operations** – Performing the same action on dozens of repos (e.g., branch protection updates) forces sequential calls, amplifying latency and limit consumption.  

These risks should be mitigated with client‑side caching, exponential back‑off, dedicated service accounts per auth tier, and monitoring of HTTP 429 responses.

---

## Skill Boundary Map

**Skill Boundary Table**

| Resource    | Can Read (auth)          | Can Write (auth)               | Can Delete (auth)          | Boundary (what you cannot do)                                                                                                                                                                                                 |
|-------------|--------------------------|--------------------------------|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| audit-log   | yes (admin_key)          | no                             | no                         | Cannot write or delete audit log; reading requires admin_key                                                                                                                                                                 |
| deployments | yes (api_key)            | yes (deploy_key)               | yes (deploy_key)           | Cannot trigger or rollback deployments without deploy_key; no endpoint to update deployment config                                                                                                                            |
| environments| yes (api_key)            | yes (admin_key)                | yes (admin_key)            | Cannot create, update, or delete environments without admin_key                                                                                                                                                              |
| pipelines   | yes (api_key)            | yes (maintainer_key)           | yes (admin_key)            | Cannot create or update pipelines without maintainer_key; deleting a pipeline requires admin_key (canceling runs is allowed with api_key)                                                                                     |
| repos       | yes (api_key)            | yes (api_key) * (merge = maintainer_key) | yes (admin_key)            | Cannot delete a repository without admin_key; cannot merge a pull request without maintainer_key; no delete endpoints for branches, commits, or pull requests                                                                 |
| secrets     | yes (maintainer_key) †   | yes (admin_key)                | yes (admin_key)            | Can only list secret names (values hidden); cannot create, rotate, or delete secrets without admin_key                                                                                                                       |
| users       | yes (api_key)            | yes (admin_key)                | no                         | Cannot delete or create users; updating a user’s role/teams requires admin_key                                                                                                                                               |
| webhooks    | yes (api_key)            | yes (maintainer_key)           | yes (maintainer_key)       | Cannot register, update, or delete webhooks without maintainer_key; no GET endpoint for an individual webhook                                                                                                                |

\* Write includes repo creation, branch/PR creation, repo/PR updates, etc.; merging a PR is the only write operation that needs maintainer_key.  
† Read returns only secret names; values are never exposed.

**Summary**  
With a standard `api_key` you can read most platform data (audit logs excepted) and perform many write actions such as creating repositories, branches, pull requests, triggering pipelines, and managing webhooks—though the latter require maintainer privileges. Deletions are tightly scoped: only repository deletion needs admin rights, pipeline deletion needs admin, environment and audit‑log modifications are admin‑only, and secret management is restricted to admins for creation/rotation/deletion. You cannot read secret values, delete audit logs, create users, or perform admin‑level actions (e.g., updating user roles, deleting repositories) without the appropriate elevated key. Thus you can build CI/CD workflows, manage code repositories, and orchestrate deployments, but you hit walls when attempting platform‑wide configuration, user/role management, or privileged secret handling without admin or maintainer credentials.
