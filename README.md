# peptide-map-visualizer
Draw and compare peptide coverage maps on protein sequences — an interactive Streamlit tool
# 🧬 Peptide Coverage Map

An interactive [Streamlit](https://streamlit.io/) application for visualizing **peptide coverage maps** on a protein sequence.
It is designed for proteomics / HDX-MS workflows where you need to display peptides from multiple experimental
conditions (files) on top of the protein sequence, compare coverage, and inspect peptide length distributions.

---

## ✨ Features

- 📝 Input any protein sequence and choose the number of amino acids per line.
- 📁 Upload multiple CSV files with peptide coordinates (`start`, `end`).
- 🎨 Assign individual colors to each condition (palette + manual picker).
- 📦 Two packing modes:
  - **Compact packing** — peptides are automatically stacked into minimal rows.
  - **Each peptide separately** — one row per peptide for exact visual comparison.
- 🔬 Adjustable peptide bar height, gaps, border width and border color.
- 📊 Automatic coverage statistics: covered residues, %, number of peptides, average length, length distribution.
- 📈 Optional peptide length distribution histogram.
- 💾 Export the coverage map and the histogram as PNG.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/peptide-coverage-map.git
cd peptide-coverage-map
```

### 2. Create a virtual environment (recommended)

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the app

```bash
streamlit run peptide_maps.py
```

After launching, Streamlit will print a local URL (usually `http://localhost:8501`).
Open it in your browser.

> To stop the server press `Ctrl + C` in the terminal.

---

## 📄 Input file format

Each CSV file must contain at least two numeric columns with peptide start and end positions
(1-based, inclusive). Column names are auto-detected (e.g. `start`, `begin`, `from` — and Russian
equivalents `начало`, `конец`), but you can also select them manually in the sidebar.

**Example `peptides.csv`:**

```csv
start,end
1,15
12,30
25,42
40,60
```

An example file is available at `examples/example_peptides.csv`.

---

## 🖱️ Usage

1. Paste or edit the protein sequence in the sidebar.
2. (Optional) Adjust the number of amino acids per line.
3. Upload a CSV file with peptides (any scv file, where you have columns with start and enp peptide positions).
4. Give the condition a name and pick a color.
5. Select the columns containing START and END positions.
6. Click **➕ Add**.
7. Repeat for all conditions.
8. Click one of the build buttons:
   - **🔬 BUILD (compact packing)**
   - **🔬 BUILD (each peptide separately)**
9. Inspect the map, view statistics, and download PNG.

---



## 🧪 Tech stack

- Python 3.9+
- [Streamlit](https://streamlit.io/) — UI
- [pandas](https://pandas.pydata.org/) — data handling
- [matplotlib](https://matplotlib.org/) — rendering


## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `streamlit: command not found` | Activate the virtual environment and reinstall requirements. |
| Font not applied | Check internet access — the Montserrat font is downloaded on first run. You can also place `Montserrat-Regular.ttf` manually in the project root. |
| CSV not parsed | Make sure the file has a header row and numeric start/end columns. |
| Empty map | Verify that peptide coordinates lie within the protein sequence length. |


## Author

Maria Lukina
Researcher, ICBFM SB RAS
maria.v.luk@gmail.com
