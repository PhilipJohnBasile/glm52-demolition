"""Tufte-clean chart: maximize the data-ink ratio, erase chartjunk, direct-label, honest axis, finding as title.
Heritage: Tufte (The Visual Display of Quantitative Information), Cleveland. No 3-D, no pie, no gradients."""
import matplotlib.pyplot as plt

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
revenue_k = [32, 35, 41, 39, 47, 52]

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(months, revenue_k, color="#1a3b5c", linewidth=2, marker="o", markersize=4)

# the title states the FINDING, not "Revenue by month"
ax.set_title("Monthly revenue climbed 63% in H1", loc="left", fontsize=13, fontweight="bold")

# Tufte: erase non-data ink — drop top/right spines, mute the rest, no tick marks, no gridlines
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_color("#999999")
ax.tick_params(length=0)
ax.set_ylim(0, 60)                       # honest axis: start at zero

# direct-label the endpoint instead of a legend
ax.annotate(f"${revenue_k[-1]}k", (len(months) - 1, revenue_k[-1]),
            xytext=(6, 0), textcoords="offset points", va="center",
            color="#1a3b5c", fontweight="bold")

fig.tight_layout()
fig.savefig("revenue_h1.svg")
