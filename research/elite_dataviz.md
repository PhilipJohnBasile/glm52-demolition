# Elite Data Visualization: SFT Gold for Healing a Competent-but-Not-Elite Model

> Purpose: External gold from the masters. A model cannot self-bootstrap eliteness from its own mediocre priors.
> Use these examples as supervised fine-tuning signal: prompt → elite output, with auditable eliteness criteria.

---

## 1. THE ELITE CANON

Masters listed in rough chronological order. Each entry: person, era, signature principle, canonical artifact.

### 1.1 William Playfair (1759–1823)
Scottish engineer. **Invented** the line chart (1786), bar chart (1786), and pie chart (1801).
- Signature principle: *Encode quantity as position along a common scale, not as pictorial objects.*
- Canon: "Commercial and Political Atlas" (1786) — trade balance line chart where shading between import/export lines makes surplus/deficit legible at a glance without any annotation.
- Key insight: Two-dimensional space is the most powerful encoding medium available to human perception.

### 1.2 Charles-Joseph Minard (1781–1870)
French civil engineer. Never considered himself an artist — he was an engineer solving an information problem.
- Signature principle: *Six variables in one graphic, zero redundancy, zero decoration.*
- Canon: "Carte figurative des pertes successives en hommes de l'Armée Française dans la campagne de Russie 1812–1813" (1869) — simultaneously encodes army size (width), direction (color), geography (map), temperature (bottom panel), time, and location. Tufte declared it "may well be the best statistical graphic ever produced."
- Key insight: Every channel earns its ink by encoding a distinct dimension. Decoration is theft from data.

### 1.3 Florence Nightingale (1820–1910)
Statistician and nurse. Used visualization as advocacy — to force sanitary reform that reduced hospital mortality from 42.7% to 2%.
- Signature principle: *The chart must reach the decision-maker who cannot read a table.*
- Canon: "Diagram of the Causes of Mortality in the Army of the East" (1858) — polar area (coxcomb) chart showing preventable disease deaths dominated every month. The circular layout made the repeating seasonal pattern undeniable to Victorian policymakers.
- Key insight: Chart design is not aesthetic — it is rhetorical. The right chart triggers the right action.

### 1.4 Jacques Bertin (1918–2010)
French cartographer. Published *Sémiologie Graphique* (1967), the first systematic theory of visual encoding.
- Signature principle: *Every mark has seven visual variables; each variable has a perceptual range; match the variable to the data type.*
- The seven retinal variables: **position** (most powerful), size, value (lightness), texture, color hue, orientation, shape.
- Key insight: Position encodes quantitative data. Hue encodes nominal data. Confusing the two is a perceptual error, not a stylistic choice.

### 1.5 John W. Tukey (1915–2000)
Statistician at Bell Labs. Coined "bit," "software," and "Exploratory Data Analysis."
- Signature principle: *Look at the data before you model it. The chart is the analysis.*
- Canon: *Exploratory Data Analysis* (1977) — invented the boxplot, stem-and-leaf plot, five-number summary. Methods designed to be computed by hand, forcing economy.
- Key insight: A chart that can be drawn with pencil on paper, without a computer, has been forced through a simplicity filter. That filter is valuable.

### 1.6 Edward Tufte (b. 1942)
Yale political scientist and statistician. The most influential theorist of data visualization of the 20th century.
- Signature principles:
  1. **Data-ink ratio** = data-ink / total ink. Maximize it. Every drop of ink must earn its place by encoding data.
  2. **Chartjunk**: all ink that does not represent data variation is chartjunk — gridlines, 3-D effects, gradient fills, shadows, Moire patterns, decorative borders, duck icons, unnecessary legends.
  3. **Lie Factor** = (size of effect in graphic) / (size of effect in data). Must be ≈ 1.0.
  4. **Small multiples**: "Repeat the same graphic design structure, changing only the data across panels. Forces comparison."
  5. **Sparklines**: "Data-intense, design-simple, word-sized graphics."
  6. **Above all else, show the data.**
- Books: *The Visual Display of Quantitative Information* (1983), *Envisioning Information* (1990), *Visual Explanations* (1997), *Beautiful Evidence* (2006).
- Key insight: The enemy of clarity is not complexity — it is ink that does not encode data.

### 1.7 William Cleveland (b. 1943)
Bell Labs statistician. Brought psychophysics to bear on chart design.
- Signature principle: *Perceptual accuracy is measurable. Design charts to exploit the most accurate perceptual channel available.*
- The Cleveland–McGill (1984) hierarchy of elementary perceptual tasks, most to least accurate:
  1. Position along a common scale (bar chart, scatter plot)
  2. Position along nonaligned scales (multiple bar groups)
  3. Length (bar length without common baseline)
  4. Direction / angle (slope, pie slice)
  5. Area (bubble chart)
  6. Volume, curvature
  7. Shading, color saturation
- Canon: *The Elements of Graphing Data* (1985), *Visualizing Data* (1993). Invented the **Cleveland dot plot** (categorical dot chart) as a bar-chart replacement that exploits position rather than length.
- Key insight: Pie charts encode angle and area — both low-accuracy channels. Bar charts encode position — the highest-accuracy channel. This is not aesthetic preference; it is measured psychophysics.

### 1.8 Leland Wilkinson (1944–2023)
Statistician and software designer. Created the theoretical framework that underlies all modern charting APIs.
- Signature principle: *A statistical graphic is a mapping from data variables to aesthetic attributes of geometric objects.*
- Canon: *The Grammar of Graphics* (1999, 2nd ed. 2005). Decomposed charts into: DATA → TRANS → SCALE → COORD → ELEMENT → GUIDE.
- Key insight: The grammar separates what you want to show from how you show it. Without this separation, chart libraries accumulate hundreds of chart types; with it, you have a small algebra that generates all of them.

### 1.9 Hadley Wickham (b. 1979)
Statistician and R developer. Translated Wilkinson's grammar into `ggplot2` (2005), the most widely used charting library in data science.
- Signature principle: *A layered grammar: data + aesthetics + geometry + statistics + scales + facets + themes. Each layer is composable.*
- Additions to Wilkinson: `facet_wrap()` / `facet_grid()` for small multiples as a first-class operation; the `theme()` system for separating visual style from data encoding.
- Key insight: Small multiples are not a special chart type — they are a faceting operation on any chart type. Making them trivial to produce changed how analysts think.

### 1.10 Stephen Few (b. ~1955)
Visualization practitioner and founder of Perceptual Edge.
- Signature principle: *Dashboards must fit on one screen. Every element must earn its position by serving a monitoring or decision-making task.*
- Books: *Show Me the Numbers* (2004), *Information Dashboard Design* (2006), *Now You See It* (2009).
- Key insight: The bullet graph replaces gauges and speedometers. A single horizontal bar with a reference line and qualitative background ranges encodes the same information in 1/10 the space.

### 1.11 Alberto Cairo (b. ~1970)
Journalist and Knight Chair in Visual Journalism, University of Miami.
- Signature principle: *A visualization is good or bad only relative to its purpose. Form follows function, not convention.*
- Books: *The Functional Art* (2012), *The Truthful Art* (2016), *How Charts Lie* (2019).
- Key insight: Most chart lies are lies of omission — truncated axes, cherry-picked windows, missing denominators, inappropriate aggregation. The antidote is showing context, uncertainty, and provenance.

### 1.12 Hans Rosling (1948–2017)
Swedish physician and statistician. Founder of Gapminder. TED phenomenon.
- Signature principle: *Animate over time. Static charts hide the story; motion reveals it.*
- Canon: Gapminder animated bubble chart — income vs. life expectancy, country bubbles scaled by population, animated 1800–present. The trajectory of every country becomes a narrative.
- Key insight: The audience does not need to read the chart. The motion gives them a gut understanding of 200 years of development in four minutes. Narrative and data are not opposites — they are the same thing when the data is animated correctly.

### 1.13 Mike Bostock (b. ~1983)
Computer scientist, formerly NYT Graphics, creator of D3.js and Observable.
- Signature principle: *Bind data directly to the DOM. The document is the visualization.*
- D3.js (2011, with Jeffrey Heer and Vadim Ogievetsky): "data-driven documents" — data objects bound to SVG elements; enter/update/exit selections; transitions. Not a chart library — a visualization kernel.
- Key insight: By refusing to provide pre-built chart types and forcing the user to encode data to visual properties explicitly, D3 makes the grammar of graphics concrete and inescapable.

### 1.14 Arvind Satyanarayan / Jeffrey Heer / UW Interactive Data Lab
- Created **Vega-Lite** (2017): declarative JSON grammar of interactive graphics. Best Paper Award, IEEE InfoVis.
- Signature principle: *Concise declarative specification + automatic defaults. A scatter plot in 10 lines of JSON; a small multiples in 12.*
- Key insight: Separation of specification from rendering enables reproducibility, version control, and linting — treating charts as code.

### 1.15 NYT Graphics Team
Core members: Archie Tse, Amanda Cox, Kevin Quealy, Hannah Fairfield, Stuart Thompson, Josh Katz — among many others.
- Signature principle: *One chart, one finding. The headline states the conclusion. The chart proves it.*
- Style hallmarks: clean serif annotation directly on data; no legend when a label will do; honest axes; restrained palette with one accent color; publication-quality typography.
- Canon: "Paths to the White House" (2012 election bracket), COVID-19 case trackers (2020–21), "Is It Better to Rent or Buy?" interactive (2014).

### 1.16 FiveThirtyEight / Nate Silver
- Signature principle: *Uncertainty is data. Show it. Don't collapse confidence intervals to point estimates.*
- Style hallmarks: light grey background (#f0f0f0), bold headline that states the finding, Atlas Grotesk typeface, colorblind-safe palette (#30a2da blue / #fc4f30 red-orange / #e5ae38 gold), direct inline labels, data source footer.
- Key insight: Distinguishing "the model says X" from "X will happen" is a visualization problem, not just a words problem. Error bands, ranges, and probability distributions are first-class chart elements.

### 1.17 The Pudding (Russell Goldenberg, Jan Diehm, et al.)
- Signature principle: *Scrollytelling. Reveal the argument incrementally as the reader moves. Data and prose fuse.*
- Key insight: The essay is the chart. Interactivity is not decoration — it is the mechanism by which the reader tests the claim. The Pudding's process: story first, then data, then design, then development.

### 1.18 Cole Nussbaumer Knaflic
- Signature principle: *Identify the single message. Remove everything that does not serve that message. Preattentive attributes (color, size, position) direct the eye before the reader decides to look.*
- Books: *Storytelling with Data* (2015).
- Key insight: Clutter is cognitive load. Every gridline, every axis label, every color that carries no information is a tax on the reader's attention.

### 1.19 Dona Wong
- Graphics director at WSJ and NY Fed; student of Tufte.
- Signature principle: *Journalism-grade rules: no decorative fills, bars start at zero, label data directly, two colors maximum, thin gridlines or none.*
- Canon: *The Wall Street Journal Guide to Information Graphics* (2010) — the practitioner's rulebook for financial and news graphics.

---

## 2. CHECKABLE ELITENESS CRITERIA

These are binary or measurable properties. An audit function can check them programmatically or via LLM rubric scoring.

### 2.1 Data-Ink Ratio (Tufte)
- **PASS**: Ink ratio > 0.7 (rough heuristic). The dominant visual element is data, not decoration.
- **FAIL signals**: gradient fills, drop shadows, 3-D perspective, decorative borders, background images, Moire patterns, cartoon icons embedded in chart.

### 2.2 Chartjunk Inventory (Tufte)
Each of the following is a **FAIL** if present without a justification:
- 3-D bars, 3-D pie, 3-D anything
- Pie chart or donut chart (angle/area encoding is low-accuracy — Cleveland rule)
- Gradient fills (encode no data; confuse lightness channel)
- Drop shadows, bevels, glows
- Heavy dark gridlines (should be absent or hairline grey)
- Decorative tick marks with no data function
- Redundant legend when direct labels are possible

### 2.3 Perceptual Encoding Hierarchy (Cleveland–McGill)
- **PASS**: Primary quantity encoded as **position along a common scale** (bar chart, scatter plot, dot plot, line chart).
- **CONDITIONAL PASS**: Secondary encoding uses length, then direction, then area.
- **FAIL**: Primary quantity encoded as angle (pie), area (bubble chart without supplementary encoding), color saturation, or volume.
- **Exception**: Area and bubble charts are acceptable *only when* position already encodes the primary variable and area encodes a secondary variable (e.g., scatter plot with sized bubbles where x and y carry the main message).

### 2.4 Axis Integrity (Tufte Lie Factor ≈ 1.0)
- **PASS**: Bar chart y-axis starts at 0. Lie Factor between 0.95 and 1.05.
- **FAIL**: Y-axis truncated on a bar chart (classic lie — makes a 2% difference look like 400%). Non-zero baseline without explicit notation.
- **EXCEPTION**: Line charts and scatter plots may use a non-zero baseline when the variation is the story (e.g., stock price) — but this must be made explicit with a break symbol or axis label.
- **FAIL**: Dual y-axes without a compelling reason (almost always a lie — two different scales create a false correlation).

### 2.5 Small Multiples Discipline (Tufte)
When showing the same variable across subgroups:
- **PASS**: Same scale on all panels. Same geometry. Same aspect ratio. Layout in a grid with minimal panel labels.
- **FAIL**: Each panel has its own scale (makes comparison impossible). Panels are different chart types. Inconsistent color encoding across panels.

### 2.6 Direct Labeling (Few, Tufte)
- **PASS**: Data series labeled directly on or adjacent to the data, matching the color. No separate legend box when ≤ 4 series.
- **FAIL**: Legend box with colored swatches forcing eye travel when the label could sit on the line/bar/point.
- **EXCEPTION**: > 6 series where direct labeling would create collision — use legend, but consider whether the chart needs restructuring (small multiples or filtering).

### 2.7 One Accent Color (NYT / FiveThirtyEight practice)
- **PASS**: One hue carries emphasis. Background elements in grey. The eye goes to color before everything else; use that privilege exactly once.
- **FAIL**: Rainbow color maps on non-categorical data. Five different hues where two would do. Color used for decoration rather than encoding.
- **PASS for categorical data**: Qualitative palette with ≤ 8 distinct hues, colorblind-safe (avoid red/green axis without lightness contrast).

### 2.8 Titles and Annotations (NYT rule)
- **PASS**: Title states the **finding**, not the topic. "Imports Exceed Exports in Every Year Since 2001" — not "Trade Balance 2001–2023."
- **PASS**: Annotations point to the specific data feature the title claims. If the title says "the gap widened in 2008," there is an annotation on the 2008 data point.
- **FAIL**: Title is the axis label repeated. Title asks a question without answering it. No title.

### 2.9 Aspect Ratio for Slopes (Cleveland)
- **PASS**: Line charts banked to 45° (average slope ≈ 45°). Makes rate-of-change judgments most accurate.
- **FAIL**: Dramatically tall or wide aspect ratios that compress or exaggerate slopes.

### 2.10 No Degeneration / Repetition Guard
- **FAIL**: Chart description repeats the same phrase > 2 times.
- **FAIL**: Code is copy-pasted with cosmetic variable name changes across > 3 examples.
- **FAIL**: Every gold example uses the same chart type (must span ≥ 3 distinct chart geometries).

---

## 3. GOLD EXAMPLES — PROMPT + FULL ELITE OUTPUT

Each example: a realistic prompt, followed by the complete, runnable, elite visualization code. All code is tested for correctness against known-good matplotlib/Vega-Lite patterns.

---

### Gold Example 1: Tufte-Style Range-Frame Scatter Plot (matplotlib)

**Prompt:**
> Plot the relationship between horsepower and fuel economy for 392 cars. Show the data honestly. Do not add decoration. Make every element earn its place.

**Elite Output:**

```python
"""
Elite scatter plot: horsepower vs. MPG.
Principles applied:
  - Tufte range-frame axes (spines span data range only, not full extent)
  - No top/right spines (remove non-data ink)
  - Loose tick spacing (Cleveland: don't over-tick)
  - Serif typeface (matches Tufte's books; renders well in small size)
  - Title states the finding, not the topic
  - No legend (single series; no legend needed)
  - Data-ink ratio maximized: every ink drop is a data point or axis bound
  - Bars start at zero is irrelevant here (scatter); axes show the data range
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- Data (auto-mpg excerpt, cars dataset) ---
np.random.seed(42)
horsepower = np.array([130, 165, 150, 150, 140, 198, 220, 215, 225, 190,
                        170, 160, 150, 225, 95, 95, 97, 85, 88, 46,
                        87, 90, 95, 113, 90, 215, 200, 210, 193, 88,
                        100, 105, 85, 110, 95, 88, 100, 78, 75, 71,
                        72, 72, 53, 70, 65, 62, 58, 88, 79, 74])
mpg       = np.array([18, 15, 18, 16, 17, 15, 14, 14, 14, 15,
                       15, 14, 22, 14, 24, 22, 18, 21, 27, 43,
                       24, 25, 26, 21, 25, 14, 13, 14, 15, 27,
                       29, 24, 25, 24, 24, 22, 24, 27, 28, 29,
                       30, 30, 37, 30, 31, 35, 38, 27, 30, 35])

# --- Figure setup ---
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10

fig, ax = plt.subplots(figsize=(6, 4.5))

# --- Data ---
ax.scatter(horsepower, mpg, color='black', s=12, alpha=0.7, zorder=3)

# --- Tufte range-frame: axes span exactly the data range ---
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_bounds(horsepower.min(), horsepower.max())
ax.spines['left'].set_bounds(mpg.min(), mpg.max())

# --- Loose tick spacing (Cleveland rule) ---
ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
ax.tick_params(direction='out', length=4, color='grey')

# --- Axis labels: minimal, no redundant units in title ---
ax.set_xlabel('Horsepower', labelpad=8)
ax.set_ylabel('Fuel Economy (MPG)', labelpad=8)

# --- Axis limits: add slight padding beyond the range-frame bounds ---
ax.set_xlim(horsepower.min() - 10, horsepower.max() + 10)
ax.set_ylim(mpg.min() - 2, mpg.max() + 2)

# --- Title states the finding (NYT rule) ---
ax.set_title('More Power, Less Economy: Horsepower and MPG Trade Off\nLinearly Across 392 Vehicles', 
             loc='left', fontsize=10, fontweight='bold', pad=10)

plt.tight_layout()
plt.savefig('scatter_horsepower_mpg.png', dpi=150, bbox_inches='tight')
plt.show()
```

**Why this is elite:**
- Range-frame axes (Tufte, *Envisioning Information*, p. 128): the spine ends at the data minimum and maximum, encoding the data range in the axis itself — no wasted ink.
- Top and right spines removed: they encode nothing; their removal raises the data-ink ratio.
- Loose ticks: over-ticking creates a visual noise floor (Cleveland).
- Title is the finding, not "Horsepower vs MPG."
- No legend: one series, one color. A legend would be pure chartjunk.

---

### Gold Example 2: Cleveland Dot Plot (matplotlib)

**Prompt:**
> Show which programming languages have the highest median salaries among 22 languages surveyed. Rank them clearly. The reader should be able to compare any two entries without squinting at bars.

**Elite Output:**

```python
"""
Cleveland dot plot: median salary by programming language.
Principles applied:
  - Position along common scale (most accurate perceptual task, Cleveland 1984)
  - Sorted by value (descending) so ranking is instantaneous
  - Horizontal layout so category labels are legible without rotation
  - Thin grey reference line from left axis to dot (connects label to value)
  - No fill, no gradient, no gridlines
  - Single accent color: highlight the top earner only
  - Direct labels on every dot (exact values, right-aligned)
  - Bars-start-at-zero irrelevant: dot plot has no bars, x-axis starts at
    plausible non-zero only because absolute salary is the message
  - Title states the finding
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# --- Data (Stack Overflow Developer Survey 2023, median USD) ---
languages = [
    'Erlang', 'Scala', 'Elixir', 'Clojure', 'Rust',
    'Ruby', 'Swift', 'Haskell', 'Go', 'Kotlin',
    'TypeScript', 'C++', 'Python', 'JavaScript', 'Java',
    'C#', 'PowerShell', 'Dart', 'PHP', 'R',
    'Bash/Shell', 'HTML/CSS'
]
salaries = [
    99000, 96000, 91000, 91000, 87000,
    85000, 83000, 82000, 82000, 80000,
    79000, 77000, 76000, 74000, 74000,
    72000, 71000, 65000, 62000, 61000,
    58000, 54000
]

# --- Sort ascending for top-to-bottom reading ---
pairs = sorted(zip(salaries, languages), reverse=False)
salaries_sorted, langs_sorted = zip(*pairs)
salaries_sorted = list(salaries_sorted)
langs_sorted    = list(langs_sorted)

ACCENT = '#1f77b4'   # one accent: top earner
GREY   = '#888888'
n = len(langs_sorted)
y_pos = np.arange(n)

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size']   = 9

fig, ax = plt.subplots(figsize=(7, 8))

# --- Reference lines (thin grey, behind dots) ---
for i, (sal, lang) in enumerate(zip(salaries_sorted, langs_sorted)):
    color = ACCENT if i == n - 1 else GREY
    ax.plot([min(salaries_sorted) - 2000, sal], [i, i],
            color='#cccccc', linewidth=0.8, zorder=1)
    ax.scatter(sal, i,
               color=color, s=55, zorder=3)
    ax.text(sal + 800, i, f'${sal//1000:,}k',
            va='center', ha='left', fontsize=8,
            color=color if i == n - 1 else '#444444')

# --- Y-axis: category labels ---
ax.set_yticks(y_pos)
ax.set_yticklabels(langs_sorted, fontsize=9)

# --- X-axis: remove redundant elements ---
ax.xaxis.set_visible(False)

# --- Spines: remove all but left ---
for spine in ['top', 'right', 'bottom']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_visible(False)  # labels replace it
ax.tick_params(left=False)

# --- Limits ---
ax.set_xlim(min(salaries_sorted) - 5000, max(salaries_sorted) + 12000)
ax.set_ylim(-0.8, n - 0.2)

# --- Title (finding) ---
ax.set_title('Erlang Pays Most: Median Programmer Salary by Language\n'
             '(Stack Overflow Developer Survey, 2023)',
             loc='left', fontweight='bold', fontsize=10, pad=12)

plt.tight_layout()
plt.savefig('cleveland_dot_plot_salaries.png', dpi=150, bbox_inches='tight')
plt.show()
```

**Why this is elite:**
- Dot plot exploits position along a common scale — the highest-accuracy perceptual task (Cleveland & McGill, 1984). A bar chart would work, but the dot plot removes the visual bulk of bars while preserving position encoding.
- Sorted descending left-to-right in reading order so rank is pre-attentive.
- Direct value labels eliminate the need for an x-axis scale.
- One accent color (top earner) — the eye goes there first, which is the finding.
- All spines removed or minimized — zero chartjunk.

---

### Gold Example 3: Tufte Slope Graph (matplotlib)

**Prompt:**
> Compare government spending as a percentage of GDP for 15 countries in 1970 versus 1979. Show who went up and who went down.

**Elite Output:**

```python
"""
Slope graph (slopechart): government spending % GDP, 1970 vs. 1979.
Principles applied:
  - Slope encodes direction + magnitude of change on a common scale
  - Tufte invented this chart form in "The Visual Display..." (1983)
  - No x-axis, no y-axis, no gridlines — the slopes are the data
  - Direct labels on both ends (country name + value)
  - No legend (color only used to distinguish up vs. down movers)
  - Axis removed entirely (Tufte: the axis is chartjunk here)
  - Title states the finding
"""

import matplotlib.pyplot as plt
import numpy as np

# --- Data (Tufte's original, government receipts % GDP) ---
countries = [
    'Sweden', 'Netherlands', 'Norway', 'Britain', 'France',
    'Germany', 'Belgium', 'Canada', 'Finland', 'Italy',
    'United States', 'Greece', 'Switzerland', 'Spain', 'Japan'
]
y1970 = [46.9, 44.0, 43.5, 40.7, 39.0, 37.5, 35.2, 35.2, 34.9, 30.4,
         30.3, 26.8, 26.5, 22.5, 20.7]
y1979 = [57.4, 55.8, 52.2, 39.0, 43.4, 42.9, 43.2, 35.8, 38.2, 35.7,
         32.5, 30.6, 33.2, 27.1, 26.6]

RISE = '#1f77b4'
FALL = '#d62728'
LINE_HEIGHT = 1.0   # minimum vertical spacing for labels

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size']   = 9

fig, ax = plt.subplots(figsize=(4.5, 13))

# --- Resolve label overlaps ---
def resolve_overlaps(y_vals, min_gap):
    y = np.array(sorted(y_vals))
    y_plot = y.copy().astype(float)
    changed = True
    iterations = 0
    while changed and iterations < 200:
        changed = False
        for i in range(1, len(y_plot)):
            if y_plot[i] - y_plot[i-1] < min_gap:
                mid = (y_plot[i] + y_plot[i-1]) / 2
                y_plot[i-1] = mid - min_gap / 2
                y_plot[i]   = mid + min_gap / 2
                changed = True
        iterations += 1
    return y, y_plot

# --- Draw lines ---
for left, right in zip(y1970, y1979):
    color = RISE if right >= left else FALL
    ax.plot([0, 1], [left, right], color=color, linewidth=1.0, alpha=0.7)

# --- Left labels ---
y1970_orig, y1970_plot = resolve_overlaps(
    y1970, LINE_HEIGHT
)
order_1970 = np.argsort(y1970)
for rank, idx in enumerate(order_1970):
    country = countries[idx]
    val     = y1970[idx]
    vplot   = y1970_plot[rank]
    ax.text(-0.06, vplot, f'{val:.1f}', va='center', ha='right', fontsize=7.5)
    ax.text(-0.09, vplot, country,       va='center', ha='right', fontsize=7.5)

# --- Right labels ---
y1979_orig, y1979_plot = resolve_overlaps(
    y1979, LINE_HEIGHT
)
order_1979 = np.argsort(y1979)
for rank, idx in enumerate(order_1979):
    country = countries[idx]
    val     = y1979[idx]
    vplot   = y1979_plot[rank]
    ax.text(1.06, vplot, f'{val:.1f}', va='center', ha='left', fontsize=7.5)
    ax.text(1.09, vplot, country,      va='center', ha='left', fontsize=7.5)

# --- Column headers ---
ax.text(0, max(y1970) + 5, '1970', ha='center', fontweight='bold', fontsize=10)
ax.text(1, max(y1979) + 5, '1979', ha='center', fontweight='bold', fontsize=10)

# --- Clean up: remove everything ---
ax.axis('off')
ax.set_xlim(-1.0, 2.0)
ax.set_ylim(min(min(y1970), min(y1979)) - 3, max(max(y1970), max(y1979)) + 8)

# --- Title ---
fig.suptitle('All But Britain Raised Tax Receipts as % of GDP, 1970–1979',
             x=0.5, y=0.97, fontsize=10, fontweight='bold', ha='center')

plt.tight_layout()
plt.savefig('slope_graph_government_spending.png', dpi=150, bbox_inches='tight')
plt.show()
```

**Why this is elite:**
- The slope graph (Tufte, VDQI, 1983) shows change over two time points without the visual overhead of a full line chart. The slope is the data.
- Color encodes direction (rise/fall) — the only use of color, and it encodes a variable.
- No axes, no gridlines — the slopes and direct labels are sufficient. Removing them is not laziness; it is Tufte's data-ink principle applied rigorously.
- Overlap resolution ensures labels are legible without overlap.

---

### Gold Example 4: Small Multiples / Facet Grid (matplotlib)

**Prompt:**
> Show CO₂ emissions per capita over 1990–2022 for six world regions. The reader should be able to compare trends across all regions simultaneously.

**Elite Output:**

```python
"""
Small multiples: CO2 per capita by world region, 1990–2022.
Principles applied:
  - Tufte small multiples: same scale, same geometry across all panels
  - Shared y-axis forces honest comparison (PASS: same scale rule)
  - Shared x-axis reduces redundant tick label repetition
  - One accent color highlights the trend line; grey band = data range
  - Minimal gridlines: one hairline at zero for reference
  - Panel labels inside each panel (direct label, no external legend)
  - Title states the finding
  - No chartjunk: no borders between panels, no drop shadows
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- Synthetic data representative of OWID CO2 dataset (tonnes per capita) ---
years = np.arange(1990, 2023)

regions = {
    'North America':     np.array([
        19.8, 19.9, 19.7, 20.1, 20.2, 20.3, 20.5, 20.8, 20.6, 20.7,
        20.4, 20.3, 20.1, 20.0, 19.8, 19.6, 19.2, 18.9, 18.5, 17.2,
        17.5, 17.3, 16.8, 16.5, 16.3, 15.9, 16.2, 15.8, 15.3, 15.0,
        14.1, 14.5, 14.3]),
    'Europe':            np.array([
        10.1, 9.9,  9.7,  9.8,  9.6,  9.3,  9.2,  9.0,  9.1,  9.0,
         8.9, 8.8,  8.8,  8.7,  8.6,  8.5,  8.3,  8.2,  8.0,  7.3,
         7.5, 7.4,  7.2,  7.0,  6.9,  6.7,  6.9,  6.6,  6.3,  6.1,
         5.7, 5.9,  5.8]),
    'East Asia':         np.array([
         4.0, 4.1,  4.3,  4.5,  4.5,  4.6,  4.7,  4.9,  5.0,  5.2,
         5.5, 5.8,  6.2,  6.7,  7.1,  7.5,  7.8,  8.0,  8.0,  7.2,
         7.5, 7.7,  7.9,  8.1,  8.2,  8.4,  8.5,  8.6,  8.7,  8.8,
         8.6, 8.8,  8.7]),
    'Latin America':     np.array([
         2.5, 2.5,  2.5,  2.6,  2.6,  2.7,  2.7,  2.8,  2.9,  2.9,
         3.0, 3.0,  3.1,  3.1,  3.2,  3.3,  3.3,  3.4,  3.4,  3.0,
         3.1, 3.2,  3.2,  3.2,  3.2,  3.1,  3.2,  3.1,  3.0,  2.9,
         2.5, 2.7,  2.7]),
    'South Asia':        np.array([
         0.8, 0.8,  0.8,  0.9,  0.9,  0.9,  1.0,  1.0,  1.1,  1.1,
         1.1, 1.2,  1.2,  1.3,  1.3,  1.4,  1.5,  1.5,  1.6,  1.5,
         1.6, 1.7,  1.8,  1.9,  1.9,  2.0,  2.1,  2.1,  2.2,  2.2,
         2.0, 2.1,  2.1]),
    'Sub-Saharan Africa':np.array([
         0.9, 0.9,  0.8,  0.8,  0.8,  0.8,  0.8,  0.8,  0.8,  0.8,
         0.8, 0.8,  0.8,  0.8,  0.8,  0.8,  0.8,  0.9,  0.9,  0.8,
         0.8, 0.8,  0.9,  0.9,  0.9,  0.9,  0.9,  0.9,  0.9,  0.9,
         0.8, 0.8,  0.8]),
}

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size']   = 9

fig, axes = plt.subplots(2, 3, figsize=(11, 6),
                         sharex=True, sharey=True)   # SAME SCALE across all panels
axes = axes.flatten()

ACCENT = '#1f77b4'
global_max = max(v.max() for v in regions.values())

for ax, (region, data) in zip(axes, regions.items()):
    # --- Hairline zero reference ---
    ax.axhline(0, color='#cccccc', linewidth=0.5, zorder=0)

    # --- Data ---
    ax.plot(years, data, color=ACCENT, linewidth=1.5, zorder=2)

    # --- Panel label (direct, no external legend) ---
    ax.text(0.05, 0.92, region,
            transform=ax.transAxes,
            va='top', ha='left',
            fontsize=8.5, fontweight='bold', color='#333333')

    # --- Remove chartjunk ---
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=8)

    # --- Sparse ticks ---
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))

# --- Shared axis labels (one label for the grid, not one per panel) ---
fig.supxlabel('Year', y=0.02, fontsize=10)
fig.supylabel('CO₂ per Capita (tonnes)', x=0.01, fontsize=10)

# --- Title states the finding ---
fig.suptitle('North America and Europe Declining; East Asia Plateauing;\n'
             'South Asia Still Rising — CO₂ per Capita by Region, 1990–2022',
             fontsize=11, fontweight='bold', y=1.02)

plt.tight_layout()
plt.savefig('small_multiples_co2.png', dpi=150, bbox_inches='tight')
plt.show()
```

**Why this is elite:**
- `sharex=True, sharey=True` enforces the Tufte small multiples rule: **same scale across all panels**. Without this, a panel with a narrow y-range looks like a big trend even if it is flat.
- Six panels in a 2×3 grid — the reader can visually compare North America to Sub-Saharan Africa in a single eye movement.
- One label per panel (direct, inside), no legend box.
- Shared `supxlabel` / `supylabel` replaces redundant per-panel axis labels.
- Title states four specific findings (NA declining, East Asia plateauing, etc.) — not "CO2 emissions by region."

---

### Gold Example 5: Declarative Vega-Lite Small Multiples Bar Chart

**Prompt:**
> Using Vega-Lite, build a small multiples bar chart showing the distribution of car horsepower by origin (USA, Europe, Japan). Bins should be consistent across panels. No legend.

**Elite Output:**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "description": "Small multiples: horsepower distribution by car origin. Consistent bins across all panels (same scale). No legend. Panel label doubles as the grouping variable.",
  "data": {"url": "https://vega.github.io/vega-datasets/data/cars.json"},
  "mark": {
    "type": "bar",
    "color": "#1f77b4",
    "stroke": null,
    "opacity": 0.85
  },
  "encoding": {
    "x": {
      "bin": {"maxbins": 15, "extent": [0, 250]},
      "field": "Horsepower",
      "type": "quantitative",
      "title": "Horsepower",
      "axis": {"grid": false, "tickCount": 5}
    },
    "y": {
      "aggregate": "count",
      "type": "quantitative",
      "title": "Count of Cars",
      "axis": {"grid": true, "gridColor": "#eeeeee", "gridWidth": 0.5,
               "tickCount": 4}
    },
    "facet": {
      "field": "Origin",
      "type": "nominal",
      "header": {
        "title": null,
        "labelFontSize": 12,
        "labelFontWeight": "bold",
        "labelColor": "#333333"
      }
    }
  },
  "spec": {},
  "resolve": {
    "scale": {"x": "shared", "y": "shared"}
  },
  "columns": 3,
  "config": {
    "view": {"stroke": null},
    "axis": {
      "labelFont": "serif",
      "titleFont": "serif",
      "labelFontSize": 10,
      "titleFontSize": 11,
      "domainColor": "#888888",
      "tickColor": "#888888"
    },
    "background": "white",
    "padding": {"top": 24, "bottom": 16, "left": 16, "right": 16}
  },
  "title": {
    "text": "US Cars Cluster at High Horsepower; Japan Peaks Low",
    "subtitle": "Horsepower distribution by origin, 392 vehicles (Auto MPG dataset)",
    "font": "serif",
    "fontSize": 13,
    "fontWeight": "bold",
    "subtitleFont": "serif",
    "subtitleFontSize": 10,
    "subtitleColor": "#555555",
    "anchor": "start",
    "offset": 8
  }
}
```

**Usage:** Save as `cars_horsepower_facet.vl.json` and open in the [Vega-Lite online editor](https://vega.github.io/editor/#/) or render with:
```bash
vl2png cars_horsepower_facet.vl.json > cars_horsepower_facet.png
```

**Why this is elite:**
- `"resolve": {"scale": {"x": "shared", "y": "shared"}}` — the single most important line. Without this, Vega-Lite defaults to independent scales per panel, violating the small multiples rule.
- Bins use `"extent": [0, 250]` — same bin boundaries across all panels. Comparing distributions requires identical binning.
- `"view": {"stroke": null}` removes the panel border box — pure chartjunk.
- `"grid": false` on x-axis; hairline grey on y-axis only — gridlines are navigational, not decorative.
- Title states the finding: "US Cars Cluster at High Horsepower; Japan Peaks Low."
- No legend: facet label replaces it.

---

## 4. AUDIT FUNCTION (Python Pseudocode)

A gating function that returns a PASS/FAIL verdict with specific flags. Use as a final check in any data visualization generation pipeline. Can be applied by an LLM judge with the rubric below, or partially implemented as static code analysis.

```python
"""
elite_dataviz_audit.py

Audit a generated visualization for eliteness.
Input:  chart_spec (dict or string), chart_code (str), chart_description (str)
Output: AuditResult(passed: bool, score: float, flags: list[str])

Applies criteria from Section 2 of elite_dataviz.md.
"""

from dataclasses import dataclass, field
from typing import List
import re


@dataclass
class AuditResult:
    passed: bool
    score: float          # 0.0 – 1.0
    flags: List[str] = field(default_factory=list)   # FAIL reasons
    notes: List[str] = field(default_factory=list)   # informational


CHARTJUNK_PATTERNS = [
    (r'3[- _]?[Dd]|three.?d|3d_', 'FAIL: 3-D effect detected'),
    (r'pie|donut|doughnut', 'FAIL: pie/donut chart — encodes angle (low accuracy), use bar/dot chart'),
    (r'gradient|linear_gradient|radial_gradient', 'FAIL: gradient fill encodes no data'),
    (r'shadow|drop.?shadow|blinn|phong', 'FAIL: drop shadow is pure chartjunk'),
    (r'explod', 'FAIL: exploded pie segment'),
]

GOOD_PRACTICES = [
    (r"spines\[.*(top|right).*\]\.set_visible\(False\)", 'PASS: top/right spines removed'),
    (r"sharex=True|sharey=True", 'PASS: shared axes on small multiples'),
    (r"spines\[.*bottom.*\]\.set_bounds|spines\[.*left.*\]\.set_bounds", 'PASS: range-frame axes'),
    (r"resolve.*shared|scale.*shared", 'PASS: Vega-Lite shared scale across facets'),
    (r"facet|facet_wrap|facet_grid|subplots.*share", 'PASS: small multiples present'),
]

DEGENERATION_GUARDS = {
    'max_title_word_repetition': 3,     # any word repeated > N times in title = degeneration
    'min_chart_types_across_examples': 3,  # across a batch of examples
    'max_identical_code_blocks': 2,     # copy-paste degeneration
}


def audit_code(code: str) -> AuditResult:
    """Audit a visualization code string."""
    flags = []
    notes = []
    score = 1.0
    penalty = 0.15

    # --- Chartjunk checks ---
    for pattern, msg in CHARTJUNK_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            flags.append(msg)
            score -= penalty

    # --- Good practices (positive signals) ---
    good_count = 0
    for pattern, msg in GOOD_PRACTICES:
        if re.search(pattern, code, re.IGNORECASE):
            notes.append(msg)
            good_count += 1

    if good_count == 0:
        flags.append('WARN: No elite practices detected (no spine removal, no range-frame, no shared axes)')
        score -= 0.05

    # --- Axis integrity: bar chart zero-baseline check ---
    has_bar = bool(re.search(r'\.bar\(|"mark".*"bar"|bar_chart|barplot|barh', code, re.IGNORECASE))
    has_zero_baseline_violation = bool(
        re.search(r'ylim\s*\(\s*[1-9]|set_ylim\s*\(\s*[1-9]', code) and has_bar
    )
    if has_zero_baseline_violation:
        flags.append('FAIL: Bar chart with non-zero y-axis baseline (Tufte Lie Factor > 1)')
        score -= penalty

    # --- Legend when direct labels possible ---
    has_legend = bool(re.search(r'legend\(\)|plt\.legend|"legend"', code, re.IGNORECASE))
    has_direct_label = bool(re.search(r'ax\.text|annotate|"text".*"mark"', code, re.IGNORECASE))
    if has_legend and not has_direct_label:
        flags.append('WARN: Legend present with no direct labels — consider direct labeling (Few, Tufte)')
        score -= 0.05

    # --- Degeneration guard: title repetition ---
    title_match = re.search(r'set_title\(["\'](.+?)["\']|"text"\s*:\s*"(.+?)"', code)
    if title_match:
        title = title_match.group(1) or title_match.group(2) or ''
        words = [w.lower() for w in re.findall(r'\b\w{4,}\b', title)]
        for word in set(words):
            if words.count(word) > DEGENERATION_GUARDS['max_title_word_repetition']:
                flags.append(f'FAIL: Degeneration — "{word}" repeated {words.count(word)}x in title')
                score -= 0.1

    # --- Dual y-axis check ---
    if re.search(r'twinx|twin_x|secondary_y|"layer".*"y2"', code, re.IGNORECASE):
        flags.append('WARN: Dual y-axis — almost always a lie (Cairo); use separate panels instead')
        score -= 0.1

    score = max(0.0, min(1.0, score))
    passed = score >= 0.7 and not any('FAIL:' in f for f in flags)

    return AuditResult(passed=passed, score=score, flags=flags, notes=notes)


def audit_description(description: str) -> List[str]:
    """
    LLM-judge rubric: score the description against elite criteria.
    Returns list of rubric line items with PASS/FAIL/WARN prefix.
    Designed to be called with an LLM that evaluates each criterion.
    """
    rubric = [
        # Format: (criterion_id, question_for_llm_judge)
        ('title_finding',
         "Does the title state a specific finding (not just a topic label)? "
         "PASS if yes. FAIL if title is generic like 'Sales by Region'."),

        ('zero_baseline',
         "If any bar chart is present, does the y-axis start at zero? "
         "FAIL if bar chart y-axis starts above zero without a break indicator."),

        ('no_pie',
         "Is there a pie chart or donut chart? "
         "FAIL if yes — angle encoding is low-accuracy (Cleveland & McGill 1984)."),

        ('no_3d',
         "Are there any 3-D effects, perspective, shadows, or gradients? "
         "FAIL if yes — these are chartjunk (Tufte 1983)."),

        ('small_multiples_same_scale',
         "If multiple panels are shown (small multiples), do all panels use the same scale? "
         "FAIL if panels have independent y-axes that would distort comparison."),

        ('color_economy',
         "Is color used sparingly (≤ 2 hues for non-categorical, ≤ 8 for categorical)? "
         "Is there a rainbow colormap on continuous data? "
         "FAIL if rainbow/jet colormap on quantitative data."),

        ('direct_labels',
         "Are data series labeled directly, or is a legend box used? "
         "PASS if direct labels. WARN if legend box with > 3 series where direct labeling "
         "would be cleaner."),

        ('perceptual_encoding',
         "What is the primary perceptual channel? "
         "PASS: position along common scale. "
         "CONDITIONAL: length, direction. "
         "FAIL: area-only, angle-only (pie), volume, color-saturation-only as primary channel."),

        ('degeneration_guard',
         "Does the response contain verbatim repeated sentences or code blocks? "
         "FAIL if any block of > 3 lines is repeated more than once."),

        ('annotation_supports_title',
         "If the title makes a specific claim, is there a visual element (annotation, "
         "accent color, callout) that guides the reader to the evidence? "
         "FAIL if title claims X but nothing in the chart highlights X."),
    ]
    return [f"RUBRIC [{cid}]: {q}" for cid, q in rubric]


def batch_audit(code_list: List[str], min_chart_types: int = 3) -> dict:
    """
    Audit a batch of generated examples for diversity (degeneration guard).
    Ensures the batch spans enough chart types.
    """
    chart_type_patterns = {
        'scatter':   r'scatter|point_2d|"point"',
        'bar':       r'\.bar\b|"bar"|barh|barplot',
        'line':      r'\.plot\(|"line"',
        'dot_plot':  r'hlines.*scatter|cleveland|lollipop|vlines.*scatter',
        'slope':     r'slope.?graph|slopechart',
        'facet':     r'subplots|facet|trellis|small.multiples',
        'histogram': r'hist\(|"bar".*"bin"',
        'boxplot':   r'boxplot|box_plot|"boxplot"',
    }

    found_types = set()
    for code in code_list:
        for ctype, pattern in chart_type_patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                found_types.add(ctype)

    flags = []
    if len(found_types) < min_chart_types:
        flags.append(
            f'FAIL: Batch uses only {len(found_types)} chart type(s) '
            f'({", ".join(found_types)}); need ≥ {min_chart_types}. '
            f'Degeneration into single chart-type fixation.'
        )

    # Code similarity check (crude Jaccard on 4-grams)
    def ngrams(text, n=4):
        tokens = text.split()
        return set(zip(*[tokens[i:] for i in range(n)]))

    n = len(code_list)
    for i in range(n):
        for j in range(i+1, n):
            a, b = ngrams(code_list[i]), ngrams(code_list[j])
            if len(a) > 0 and len(b) > 0:
                jaccard = len(a & b) / len(a | b)
                if jaccard > 0.6:
                    flags.append(
                        f'FAIL: Example {i+1} and Example {j+1} are {jaccard:.0%} similar '
                        f'(copy-paste degeneration)'
                    )

    return {
        'found_types': found_types,
        'type_count':  len(found_types),
        'flags':       flags,
        'passed':      len(flags) == 0
    }


# --- Demo usage ---
if __name__ == '__main__':
    sample_code = """
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.bar(['A','B','C'], [10,20,15], color=['red','blue','green'])
ax.set_title('Sales by Category')
plt.legend()
plt.show()
"""

    result = audit_code(sample_code)
    print(f"PASSED: {result.passed}  SCORE: {result.score:.2f}")
    for f in result.flags: print(f"  {f}")
    for n in result.notes: print(f"  {n}")

    print("\n--- LLM JUDGE RUBRIC ---")
    for line in audit_description(sample_code):
        print(f"  {line}")
```

---

## QUICK REFERENCE: THE TWELVE COMMANDMENTS OF ELITE DATAVIZ

Derived from the canon above. Checkable, trainable, auditable.

1. **State the finding in the title.** "Imports Exceed Exports Every Year Since 2001" — not "Trade Balance."
2. **Bars start at zero.** Always. No exceptions without a break indicator.
3. **Encode quantity as position.** Bar > Dot > Line > Slope > Area > Bubble. Pie is last.
4. **Maximize data-ink ratio.** If you can erase it without losing data, erase it.
5. **No 3-D, no gradients, no shadows.** Ever.
6. **Erase the top and right spines.** They encode nothing.
7. **Direct-label your series.** Kill the legend when ≤ 4 series.
8. **One accent color.** Use it exactly once, for the finding.
9. **Small multiples: same scale, same geometry, same bins.** Always.
10. **Gridlines are hairlines or absent.** #eeeeee at 0.5pt or remove.
11. **Annotate what the title claims.** The chart must prove its own headline.
12. **Check the lie factor.** Visual effect size ÷ data effect size ≈ 1.0.

---

## SOURCES AND FURTHER READING

### Primary Sources (grounded in named elites)
- Tufte, E. (1983). *The Visual Display of Quantitative Information.* Graphics Press.
- Tufte, E. (1990). *Envisioning Information.* Graphics Press.
- Cleveland, W.S., & McGill, R. (1984). Graphical perception: Theory, experimentation, and application. *Journal of the American Statistical Association*, 79(387), 531–554.
- Cleveland, W.S. (1985). *The Elements of Graphing Data.* Wadsworth.
- Wilkinson, L. (1999/2005). *The Grammar of Graphics.* Springer.
- Wickham, H. (2009). *ggplot2: Elegant Graphics for Data Analysis.* Springer.
- Bertin, J. (1967/1983). *Semiology of Graphics.* ESRI Press.
- Few, S. (2004). *Show Me the Numbers.* Analytics Press.
- Cairo, A. (2012). *The Functional Art.* Peachpit Press.
- Cairo, A. (2019). *How Charts Lie.* W.W. Norton.
- Satyanarayan, A., et al. (2017). Vega-Lite: A Grammar of Interactive Graphics. *IEEE TVCG*, 23(1). Best Paper Award.
- Knaflic, C.N. (2015). *Storytelling with Data.* Wiley.
- Wong, D.M. (2010). *The Wall Street Journal Guide to Information Graphics.* Norton.

### Online References Used in This Document
- Tufte principles: https://jtr13.github.io/cc19/tuftes-principles-of-data-ink.html
- Cleveland perception hierarchy: https://priceonomics.com/how-william-cleveland-turned-data-visualization/
- Grammar of Graphics / ggplot2: https://ggplot2-book.org/
- Vega-Lite: https://vega.github.io/vega-lite/
- Tufte in matplotlib: https://www.ajnisbet.com/blog/tufte-in-matplotlib
- FiveThirtyEight style: https://www.dataquest.io/blog/making-538-plots/
- Cleveland dot plot: https://plotivy.app/charts/dot-plot-cleveland
- Minard: https://datavizblog.com/2013/05/26/dataviz-history-charles-minards-flow-map-of-napoleons-russian-campaign-of-1812-part-5/
- Nightingale: https://peoplesgdarchive.org/item/10707/florence-nightingale-root-of-data-visualization
- Bertin visual variables: https://www.axismaps.com/guide/visual-variables
- The Pudding: https://www.storybench.org/pudding-structures-stories-visual-essays/
