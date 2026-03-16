"""
Skill Boundary Heatmap (Landscape)
Generates a visual heatmap showing read/write/delete capabilities
across resources and auth levels for DevForge Platform API.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

resources = [
    "repos",
    "branches",
    "commits",
    "pull-requests",
    "merge",
    "deployments",
    "pipelines",
    "pipeline-runs",
    "secrets",
    "environments",
    "users",
    "audit-log",
    "webhooks",
]

operations = ["Read", "Write", "Delete"]

# Auth levels: 0 = not available, 1 = api_key, 2 = maintainer/deploy_key, 3 = admin_key
data = np.array([
    [1, 1, 3],   # repos
    [1, 1, 0],   # branches
    [1, 0, 0],   # commits
    [1, 1, 0],   # pull-requests
    [0, 2, 0],   # merge
    [1, 2, 2],   # deployments
    [1, 2, 3],   # pipelines
    [1, 1, 1],   # pipeline-runs
    [2, 3, 3],   # secrets
    [1, 3, 3],   # environments
    [1, 3, 0],   # users
    [3, 0, 0],   # audit-log
    [1, 2, 2],   # webhooks
])

colors = {
    0: "#2d2d2d",
    1: "#22c55e",
    2: "#f59e0b",
    3: "#ef4444",
}

auth_detail = {
    (0, 0): "api_key", (0, 1): "api_key", (0, 2): "admin_key",
    (1, 0): "api_key", (1, 1): "api_key",
    (2, 0): "api_key",
    (3, 0): "api_key", (3, 1): "api_key",
    (4, 1): "maintainer",
    (5, 0): "api_key", (5, 1): "deploy_key", (5, 2): "deploy_key",
    (6, 0): "api_key", (6, 1): "maintainer", (6, 2): "admin_key",
    (7, 0): "api_key", (7, 1): "api_key", (7, 2): "api_key",
    (8, 0): "maintainer", (8, 1): "admin_key", (8, 2): "admin_key",
    (9, 0): "api_key", (9, 1): "admin_key", (9, 2): "admin_key",
    (10, 0): "api_key", (10, 1): "admin_key",
    (11, 0): "admin_key",
    (12, 0): "api_key", (12, 1): "maintainer", (12, 2): "maintainer",
}

# Landscape: resources on X axis, operations on Y axis
fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#1a1a2e")

cell_width = 1.0
cell_height = 1.0
gap = 0.08

for i, resource in enumerate(resources):
    for j, op in enumerate(operations):
        val = data[i, j]
        color = colors[val]

        x = i * (cell_width + gap)
        y = (len(operations) - 1 - j) * (cell_height + gap)

        rect = mpatches.FancyBboxPatch(
            (x, y), cell_width, cell_height,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor="#ffffff20",
            linewidth=0.5,
        )
        ax.add_patch(rect)

        if val > 0:
            detail = auth_detail.get((i, j), "")
            ax.text(
                x + cell_width / 2, y + cell_height / 2 + 0.1,
                "●",
                ha="center", va="center",
                fontsize=14, color="white", fontweight="bold",
            )
            ax.text(
                x + cell_width / 2, y + cell_height / 2 - 0.18,
                detail,
                ha="center", va="center",
                fontsize=6, color="white", alpha=0.9,
                fontfamily="monospace",
            )
        else:
            ax.text(
                x + cell_width / 2, y + cell_height / 2,
                "✕",
                ha="center", va="center",
                fontsize=12, color="#666666",
            )

# Resource labels (bottom)
for i, resource in enumerate(resources):
    x = i * (cell_width + gap) + cell_width / 2
    y = -0.25
    ax.text(
        x, y, resource,
        ha="center", va="top",
        fontsize=9, color="white",
        fontfamily="monospace",
        fontweight="bold",
        rotation=35,
        rotation_mode="anchor",
    )

# Operation labels (left)
for j, op in enumerate(operations):
    x = -0.15
    y = (len(operations) - 1 - j) * (cell_height + gap) + cell_height / 2
    ax.text(
        x, y, op,
        ha="right", va="center",
        fontsize=13, color="white",
        fontweight="bold",
    )

# Title
total_width = len(resources) * (cell_width + gap) - gap
ax.text(
    total_width / 2,
    len(operations) * (cell_height + gap) + 0.35,
    "SKILL BOUNDARY HEATMAP",
    ha="center", va="bottom",
    fontsize=20, color="white",
    fontweight="bold",
    fontfamily="monospace",
)

ax.text(
    total_width / 2,
    len(operations) * (cell_height + gap) + 0.05,
    "DevForge Platform API — Explored by AI Agent",
    ha="center", va="bottom",
    fontsize=10, color="#888888",
    fontfamily="monospace",
)

# Legend (horizontal, bottom right)
legend_items = [
    ("#22c55e", "api_key (open)"),
    ("#f59e0b", "Restricted (maintainer / deploy_key)"),
    ("#ef4444", "admin_key only"),
    ("#2d2d2d", "Not available"),
]

legend_x_start = total_width - 5.5
legend_y = -1.6

for idx, (color, label) in enumerate(legend_items):
    lx = legend_x_start + idx * 3.5
    ly = legend_y
    rect = mpatches.FancyBboxPatch(
        (lx, ly), 0.3, 0.3,
        boxstyle="round,pad=0.03",
        facecolor=color,
        edgecolor="#ffffff30",
        linewidth=0.5,
    )
    ax.add_patch(rect)
    ax.text(
        lx + 0.42, ly + 0.15,
        label,
        ha="left", va="center",
        fontsize=8, color="#cccccc",
        fontfamily="monospace",
    )

ax.set_xlim(-1.2, total_width + 0.5)
ax.set_ylim(-2.2, len(operations) * (cell_height + gap) + 1.2)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("skill_boundary_heatmap.png", dpi=200, bbox_inches="tight", facecolor="#1a1a2e")
plt.savefig("skill_boundary_heatmap.jpg", dpi=200, bbox_inches="tight", facecolor="#1a1a2e")
print("  Saved: skill_boundary_heatmap.png / .jpg")
