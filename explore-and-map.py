"""
Skill Boundary Explorer Demo
An AI Agent explores an unknown API environment, discovers what's available,
maps capabilities, identifies what it can and cannot build, and reports
its skill boundary.

Simulates the OSExpert GUI-DFS concept applied to API exploration.
Uses NVIDIA Nemotron 3 Super (120B/12B active) as the reasoning model.
"""

import os
import re
import json
import time
from openai import OpenAI

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "private/nvidia/nemotron-3-super-120b-a12b"
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

CLIENT = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    default_headers={"NVCF-POLL-SECONDS": "1800"},
)

# ---------------------------------------------------------------------------
# Simulated API environment (the agent does not see this directly)
# It discovers it through exploration calls
# ---------------------------------------------------------------------------

ENVIRONMENT = {
    "name": "DevForge Platform API",
    "base_url": "https://api.devforge.example.com/v1",
    "endpoints": {
        "/repos": {
            "GET": {"description": "List repositories", "params": ["limit", "offset", "visibility", "language"], "auth": "api_key"},
            "POST": {"description": "Create repository", "params": ["name", "description", "visibility", "default_branch"], "auth": "api_key"},
        },
        "/repos/{id}": {
            "GET": {"description": "Get repository details", "params": [], "auth": "api_key"},
            "PATCH": {"description": "Update repository settings", "params": ["description", "visibility", "archived"], "auth": "api_key"},
            "DELETE": {"description": "Delete repository", "params": [], "auth": "admin_key"},
        },
        "/repos/{id}/branches": {
            "GET": {"description": "List branches", "params": [], "auth": "api_key"},
            "POST": {"description": "Create branch", "params": ["name", "source_branch"], "auth": "api_key"},
        },
        "/repos/{id}/commits": {
            "GET": {"description": "List commits", "params": ["branch", "since", "until", "author"], "auth": "api_key"},
        },
        "/repos/{id}/pull-requests": {
            "GET": {"description": "List pull requests", "params": ["state", "author", "reviewer"], "auth": "api_key"},
            "POST": {"description": "Create pull request", "params": ["title", "description", "source_branch", "target_branch", "reviewers"], "auth": "api_key"},
        },
        "/repos/{id}/pull-requests/{pr_id}": {
            "GET": {"description": "Get pull request details", "params": [], "auth": "api_key"},
            "PATCH": {"description": "Update pull request", "params": ["title", "description", "state", "reviewers"], "auth": "api_key"},
        },
        "/repos/{id}/pull-requests/{pr_id}/merge": {
            "POST": {"description": "Merge pull request", "params": ["strategy", "delete_branch"], "auth": "maintainer_key"},
        },
        "/deployments": {
            "GET": {"description": "List deployments", "params": ["repo_id", "environment", "status", "date_from"], "auth": "api_key"},
            "POST": {"description": "Trigger deployment", "params": ["repo_id", "branch", "environment", "config_overrides"], "auth": "deploy_key"},
        },
        "/deployments/{id}": {
            "GET": {"description": "Get deployment status", "params": [], "auth": "api_key"},
            "DELETE": {"description": "Rollback deployment", "params": [], "auth": "deploy_key"},
        },
        "/deployments/{id}/logs": {
            "GET": {"description": "Get deployment logs", "params": ["level", "since"], "auth": "api_key"},
        },
        "/pipelines": {
            "GET": {"description": "List CI/CD pipelines", "params": ["repo_id", "status", "trigger"], "auth": "api_key"},
            "POST": {"description": "Create pipeline", "params": ["repo_id", "name", "stages", "triggers", "config_yaml"], "auth": "maintainer_key"},
        },
        "/pipelines/{id}": {
            "GET": {"description": "Get pipeline details", "params": [], "auth": "api_key"},
            "PATCH": {"description": "Update pipeline config", "params": ["stages", "triggers", "enabled"], "auth": "maintainer_key"},
            "DELETE": {"description": "Delete pipeline", "params": [], "auth": "admin_key"},
        },
        "/pipelines/{id}/runs": {
            "GET": {"description": "List pipeline runs", "params": ["status", "branch"], "auth": "api_key"},
            "POST": {"description": "Trigger pipeline run", "params": ["branch", "variables"], "auth": "api_key"},
        },
        "/pipelines/{id}/runs/{run_id}": {
            "GET": {"description": "Get pipeline run details and logs", "params": [], "auth": "api_key"},
            "DELETE": {"description": "Cancel pipeline run", "params": [], "auth": "api_key"},
        },
        "/secrets": {
            "GET": {"description": "List secret names (values hidden)", "params": ["scope", "repo_id"], "auth": "maintainer_key"},
            "POST": {"description": "Create secret", "params": ["name", "value", "scope", "repo_id"], "auth": "admin_key"},
        },
        "/secrets/{id}": {
            "PATCH": {"description": "Rotate secret value", "params": ["value"], "auth": "admin_key"},
            "DELETE": {"description": "Delete secret", "params": [], "auth": "admin_key"},
        },
        "/environments": {
            "GET": {"description": "List environments", "params": ["repo_id"], "auth": "api_key"},
            "POST": {"description": "Create environment", "params": ["name", "repo_id", "protection_rules", "variables"], "auth": "admin_key"},
        },
        "/environments/{id}": {
            "GET": {"description": "Get environment details", "params": [], "auth": "api_key"},
            "PATCH": {"description": "Update environment config", "params": ["protection_rules", "variables"], "auth": "admin_key"},
            "DELETE": {"description": "Delete environment", "params": [], "auth": "admin_key"},
        },
        "/users": {
            "GET": {"description": "List platform users", "params": ["role", "team"], "auth": "api_key"},
        },
        "/users/{id}": {
            "GET": {"description": "Get user profile", "params": [], "auth": "api_key"},
            "PATCH": {"description": "Update user role", "params": ["role", "teams"], "auth": "admin_key"},
        },
        "/audit-log": {
            "GET": {"description": "Query audit log", "params": ["actor", "action", "resource", "date_from", "date_to"], "auth": "admin_key"},
        },
        "/webhooks": {
            "GET": {"description": "List webhooks", "params": ["repo_id"], "auth": "api_key"},
            "POST": {"description": "Register webhook", "params": ["repo_id", "url", "events", "secret"], "auth": "maintainer_key"},
        },
        "/webhooks/{id}": {
            "PATCH": {"description": "Update webhook", "params": ["url", "events", "active"], "auth": "maintainer_key"},
            "DELETE": {"description": "Delete webhook", "params": [], "auth": "maintainer_key"},
        },
    },
    "auth_levels": {
        "api_key": "Standard API access — available to all authenticated developers",
        "maintainer_key": "Maintainer access — repo owners and designated maintainers",
        "deploy_key": "Deploy access — CI/CD systems and authorized deployers",
        "admin_key": "Admin access — platform administrators only",
    },
    "rate_limits": {
        "api_key": "100 requests/minute",
        "maintainer_key": "60 requests/minute",
        "deploy_key": "30 requests/minute",
        "admin_key": "200 requests/minute",
    },
}


def simulate_discovery(endpoint: str) -> dict:
    """Simulate what an agent would discover when probing an endpoint."""
    if endpoint == "/":
        return {
            "api": ENVIRONMENT["name"],
            "version": "v2",
            "resources": list(set(
                ep.split("/")[1] for ep in ENVIRONMENT["endpoints"].keys()
                if ep.split("/")[1]
            )),
        }

    results = {}
    for ep, methods in ENVIRONMENT["endpoints"].items():
        if ep.startswith(endpoint) or endpoint.rstrip("/") == ep.split("{")[0].rstrip("/"):
            results[ep] = {}
            for method, details in methods.items():
                results[ep][method] = {
                    "description": details["description"],
                    "parameters": details["params"],
                    "auth_required": details["auth"],
                    "auth_description": ENVIRONMENT["auth_levels"].get(details["auth"], "Unknown"),
                }
    return results


def explore_resource(resource_name: str) -> str:
    """Return a formatted discovery result for a resource."""
    discovered = simulate_discovery(f"/{resource_name}")
    if not discovered:
        return f"No endpoints found for /{resource_name}"
    return json.dumps(discovered, indent=2)


def agent_call(prompt: str, system: str = None) -> str:
    """Make a single LLM call."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = CLIENT.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def run_exploration():
    """Run the full exploration loop."""

    print("\n" + "=" * 70)
    print("  SKILL BOUNDARY EXPLORER")
    print("  Model: NVIDIA Nemotron 3 Super (120B/12B active)")
    print("  Task: Explore unknown API, map capabilities, report skill boundary")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # Phase 1: Initial discovery — what resources exist?
    # -----------------------------------------------------------------------
    print("\n  PHASE 1: Initial Discovery")
    print("  " + "-" * 50)

    root_discovery = simulate_discovery("/")
    resources = root_discovery["resources"]

    print(f"  API: {root_discovery['api']} ({root_discovery['version']})")
    print(f"  Resources discovered: {', '.join(sorted(resources))}")

    # -----------------------------------------------------------------------
    # Phase 2: Deep exploration — probe each resource
    # -----------------------------------------------------------------------
    print("\n  PHASE 2: Deep Exploration")
    print("  " + "-" * 50)

    full_map = {}
    auth_requirements = set()

    for resource in sorted(resources):
        discovered = simulate_discovery(f"/{resource}")
        full_map[resource] = discovered

        endpoint_count = sum(len(methods) for methods in discovered.values())
        auths = set()
        for methods in discovered.values():
            for method_info in methods.values():
                auths.add(method_info["auth_required"])
                auth_requirements.add(method_info["auth_required"])

        print(f"  /{resource}: {endpoint_count} operations | auth: {', '.join(sorted(auths))}")

    # -----------------------------------------------------------------------
    # Phase 3: Agent analysis — what can I build with this?
    # -----------------------------------------------------------------------
    print("\n  PHASE 3: Agent Analysis")
    print("  " + "-" * 50)
    print("  Sending full discovery map to agent for analysis...")

    discovery_json = json.dumps(full_map, indent=2)
    auth_json = json.dumps(ENVIRONMENT["auth_levels"], indent=2)
    rate_json = json.dumps(ENVIRONMENT["rate_limits"], indent=2)

    analysis_prompt = f"""You have just explored an unknown API environment. Here is everything you discovered:

## API: {root_discovery['api']}

## Discovered Endpoints
{discovery_json}

## Authentication Levels
{auth_json}

## Rate Limits
{rate_json}

Based on your exploration, produce a structured report with these exact sections:

### 1. CAPABILITY MAP
List every distinct capability this API provides, grouped by domain (for example patient management, scheduling, billing). For each capability, state the endpoints involved and the auth level required.

### 2. BUILDABLE APPLICATIONS
List 5 concrete applications or integrations you could build using this API. For each one, state:
- What it does
- Which endpoints it uses
- What auth level is needed
- Feasibility (high/medium/low)

### 3. SKILL BOUNDARY — WHAT I CANNOT DO
List specific things that are NOT possible with this API. Identify gaps, missing capabilities, and operations that would require additional systems. Be specific.

### 4. COMPOSITE WORKFLOWS
Identify 3 multi-step workflows that chain multiple endpoints together. For each, list the exact sequence of API calls.

### 5. INTEGRATION RISKS
List potential failure points, rate limit concerns, and auth-level barriers that would affect production use.

Be specific and practical. No filler."""

    start = time.time()
    analysis = agent_call(
        analysis_prompt,
        system="You are an AI Agent that has just explored an unknown API environment. You are reporting what you found, what you can build, and what your boundaries are. Be direct and specific."
    )
    elapsed = time.time() - start

    print(f"  Analysis complete ({elapsed:.1f}s)")

    # -----------------------------------------------------------------------
    # Phase 4: Skill boundary summary
    # -----------------------------------------------------------------------
    print("\n  PHASE 4: Skill Boundary Summary")
    print("  " + "-" * 50)

    summary_prompt = f"""Based on your analysis of the DevForge Platform API, produce a concise skill boundary table.

For each resource, state:
- Can Read (yes/no and auth level)
- Can Write (yes/no and auth level)
- Can Delete (yes/no and auth level)
- Boundary (what you cannot do)

Format as a clean ASCII table. Then give a single paragraph summary of your overall skill boundary — what you can build and where you hit walls.

Here is the full discovery map:
{discovery_json}

Auth levels:
{auth_json}"""

    start2 = time.time()
    boundary = agent_call(
        summary_prompt,
        system="You are an AI Agent reporting your skill boundary after exploring an unknown environment. Be precise."
    )
    elapsed2 = time.time() - start2

    print(f"  Boundary mapping complete ({elapsed2:.1f}s)")

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  EXPLORATION RESULTS")
    print("=" * 70)

    # Stats
    total_endpoints = sum(
        len(methods)
        for resource_data in full_map.values()
        for methods in resource_data.values()
    )
    total_resources = len(resources)

    print(f"\n  Resources discovered:  {total_resources}")
    print(f"  Total operations:      {total_endpoints}")
    print(f"  Auth levels found:     {len(auth_requirements)} ({', '.join(sorted(auth_requirements))})")
    print(f"  Analysis time:         {elapsed + elapsed2:.1f}s")

    print("\n" + "-" * 70)
    print("  AGENT CAPABILITY ANALYSIS")
    print("-" * 70)
    print(analysis)

    print("\n" + "-" * 70)
    print("  SKILL BOUNDARY MAP")
    print("-" * 70)
    print(boundary)

    # Save outputs
    with open("exploration_report.md", "w") as f:
        f.write(f"# Skill Boundary Exploration Report\n\n")
        f.write(f"**API:** {root_discovery['api']} ({root_discovery['version']})\n")
        f.write(f"**Resources:** {total_resources}\n")
        f.write(f"**Operations:** {total_endpoints}\n")
        f.write(f"**Auth levels:** {', '.join(sorted(auth_requirements))}\n")
        f.write(f"**Model:** NVIDIA Nemotron 3 Super (120B/12B active)\n\n")
        f.write(f"---\n\n")
        f.write(f"## Capability Analysis\n\n{analysis}\n\n")
        f.write(f"---\n\n")
        f.write(f"## Skill Boundary Map\n\n{boundary}\n")

    with open("discovered_api_map.json", "w") as f:
        json.dump({
            "api": root_discovery,
            "endpoints": full_map,
            "auth_levels": ENVIRONMENT["auth_levels"],
            "rate_limits": ENVIRONMENT["rate_limits"],
        }, f, indent=2)

    print("\n" + "-" * 70)
    print("  Exploration report saved to: exploration_report.md")
    print("  API map saved to: discovered_api_map.json")
    print()


def main():
    if not NVIDIA_API_KEY:
        print("Error: set NVIDIA_API_KEY environment variable")
        return

    run_exploration()


if __name__ == "__main__":
    main()
