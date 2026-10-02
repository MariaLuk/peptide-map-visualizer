import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
import io
import os
import urllib.request
from pathlib import Path
from collections import Counter

# === PAGE CONFIG ===
st.set_page_config(layout="wide", page_title="Peptide Coverage Map", page_icon="🧬")

# === MONTSERRAT FONT ===
def setup_montserrat():
    font_path = "Montserrat-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except:
            pass
    try:
        fm.fontManager.addfont(font_path)
        if "Montserrat" in [f.name for f in fm.fontManager.ttflist]:
            plt.rcParams['font.family'] = 'Montserrat'
        else:
            plt.rcParams['font.family'] = 'sans-serif'
    except:
        plt.rcParams['font.family'] = 'sans-serif'

setup_montserrat()

# === PEPTIDE PACKING ===
def assign_levels(intervals):
    if not intervals:
        return []
    intervals_sorted = sorted([(s, e, idx) for idx, (s, e) in enumerate(intervals)],
                              key=lambda x: (x[0], -x[1]))
    level_ends = []
    result = [None] * len(intervals)
    for s, e, idx in intervals_sorted:
        placed = False
        for lvl, end in enumerate(level_ends):
            if s >= end:
                level_ends[lvl] = e
                result[idx] = (s, e, lvl)
                placed = True
                break
        if not placed:
            level_ends.append(e)
            result[idx] = (s, e, len(level_ends) - 1)
    return sorted(result, key=lambda x: (x[2], x[0]))

# === SESSION INIT ===
if 'files_data' not in st.session_state:
    st.session_state.files_data = []

st.title("🧬 Peptide Coverage Map")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Settings")
    sequence = st.text_area("📝 Protein sequence",
                            value="MPEGPLVRKFHHLVSPFVGQQVVKTGGSSKKLQPASLQSLWLQDTQVHGAKLFLRFDLDEEMGPPGSSPTPEPPQKEVQKEGAADPKQVGEPSGQKTLDGSSRSAELVPQGEDDSEYLERDAPAGDAGRWLRVSFGLFGSVWVNDFSRAKKANKRGDWRDPSPRLVLHFGGGGFLAFYNCQLSWSSSPVVTPTCDILSEKFHRGQALEALGQAQPVCYTLLDQRYFSGLGNIIKNEALYRAGIHPLSLGSVLSASRREVLVDHVVEFSTAWLQGKFQGRPQHTQVYQKEQCPAGHQVMKEAFGPEDGLQRLTWWCPQCQPQLSEEPEQCQFS",
                            height=120)
    line_length = st.number_input("📏 Amino acids per line", min_value=10, max_value=200, value=60)

    st.markdown("---")
    st.subheader("🎨 Peptide appearance")
    peptide_height = st.slider("Peptide bar height", 0.01, 0.4, 0.05, 0.005)
    gap_factor = st.slider("Row gap factor", -0.5, 2.0, 0.0, 0.02,
                           help="Gap between rows = bar_height × factor")
    condition_gap = st.slider("Gap between conditions (files)", 0.0, 1.5, 0.1, 0.05)
    block_gap = st.slider("Block spacing (after each block)", 0.0, 1.0, 0.1, 0.02)
    linewidth = st.slider("Border line width", 0.0, 2.0, 0.3, 0.1)
    border_color = st.color_picker("Border color", value="#FFFFFF")
    if st.button("⬜ Reset to white", use_container_width=True):
        border_color = "#FFFFFF"
        st.rerun()

    st.markdown("---")
    st.subheader("📊 Additional statistics")
    show_length_dist = st.checkbox("Show peptide length distribution", value=True)

    st.markdown("---")
    st.subheader("📁 Add CSV files")
    uploaded_file = st.file_uploader("Choose CSV", type=["csv"], key="file_uploader")
    if uploaded_file is not None:
        df_sample = pd.read_csv(uploaded_file)
        st.write("**Preview:**", df_sample.head(2))
        st.write(f"**Columns:** {', '.join(df_sample.columns)}")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Condition name", value=Path(uploaded_file.name).stem, key="name_input")
        with col2:
            # ---------- SIMPLIFIED COLOR PICKER (PALETTE + MANUAL CHECKBOX) ----------
            palettes = {
                "default": {
                    "blue": "#1f77b4",
                    "orange": "#ff7f0e",
                    "green": "#2ca02c",
                    "red": "#d62728",
                    "purple": "#9467bd",
                    "brown": "#8c564b",
                    "pink": "#e377c2",
                    "gray": "#7f7f7f",
                    "yellowgreen": "#bcbd22",
                    "cyan": "#17becf"
                },
                "icefire": {
                    "dark blue": "#3a4d73",
                    "blue": "#5b6e8c",
                    "mid blue": "#7c8fa6",
                    "light blue": "#9db0bf",
                    "grayish blue": "#bfd1d9",
                    "light gray": "#e0e5e6",
                    "peach": "#f5d0b0",
                    "orange": "#e8a87c",
                    "dark orange": "#db7f48",
                    "red": "#cf5714"
                },
                "set2": {
                    "mint": "#66c2a5",
                    "orange": "#fc8d62",
                    "purpleblue": "#8da0cb",
                    "pink": "#e78ac3",
                    "lightgreen": "#a6d854",
                    "yellow": "#ffd92f",
                    "beige": "#e5c494",
                    "gray": "#b3b3b3"
                }
            }

            file_key = uploaded_file.name
            palette_key = f"palette_{file_key}"
            color_name_key = f"color_name_{file_key}"
            manual_key = f"manual_{file_key}"
            manual_color_key = f"manual_color_{file_key}"

            if palette_key not in st.session_state:
                st.session_state[palette_key] = "default"
            if color_name_key not in st.session_state:
                st.session_state[color_name_key] = "blue"
            if manual_key not in st.session_state:
                st.session_state[manual_key] = False
            if manual_color_key not in st.session_state:
                st.session_state[manual_color_key] = "#000000"

            palette_choice = st.selectbox("Palette", list(palettes.keys()), key=palette_key)
            current_palette = palettes[palette_choice]
            color_names = list(current_palette.keys())
            selected_color_name = st.selectbox("Color from palette", color_names, key=color_name_key)
            preset_color = current_palette[selected_color_name]

            use_manual = st.checkbox("Select color manually", key=manual_key)

            if use_manual:
                manual_color = st.color_picker("Choose a color", value=preset_color, key=manual_color_key)
                final_color = manual_color
            else:
                final_color = preset_color

            st.markdown(f'<div style="background-color:{final_color}; padding:6px; border-radius:4px; text-align:center; color:{"white" if final_color < "#888888" else "black"}; font-weight:bold;">Selected color</div>', unsafe_allow_html=True)

            color = final_color
            # --------------------------------------------------------------

        col1, col2 = st.columns(2)
        with col1:
            df_cols_lower = {col: col.lower() for col in df_sample.columns}
            start_candidates = ['start', 'begin', 'from', 'начало']
            end_candidates = ['end', 'stop', 'to', 'конец']
            start_col_default = None
            end_col_default = None
            for col, lower in df_cols_lower.items():
                if lower in start_candidates:
                    start_col_default = col
                    break
            for col, lower in df_cols_lower.items():
                if lower in end_candidates:
                    end_col_default = col
                    break
            if start_col_default is None:
                start_col_default = df_sample.columns[0]
            if end_col_default is None and len(df_sample.columns) > 1:
                end_col_default = df_sample.columns[1]
            elif end_col_default is None:
                end_col_default = df_sample.columns[0]

            start_col = st.selectbox("Column START", options=df_sample.columns,
                                    index=list(df_sample.columns).index(start_col_default) if start_col_default in df_sample.columns else 0,
                                    key="start_select")
        with col2:
            end_col = st.selectbox("Column END", options=df_sample.columns,
                                  index=list(df_sample.columns).index(end_col_default) if end_col_default in df_sample.columns else 0,
                                  key="end_select")

        if st.button("➕ Add", key="add_button", use_container_width=True):
            st.session_state.files_data.append({
                "name": name,
                "file": uploaded_file,
                "start_col": start_col,
                "end_col": end_col,
                "color": color,
                "df": df_sample
            })
            st.success(f"Added: {name}")
            st.rerun()

    st.markdown("---")
    if st.session_state.files_data:
        st.subheader("📋 Files")
        for i, f in enumerate(st.session_state.files_data):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"🎨 **{f['name']}**")
                st.caption(f"{f['start_col']} – {f['end_col']}")
                st.markdown(f'<div style="background-color:{f["color"]}; height:10px; border-radius:3px; width:100%;"></div>', unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.files_data.pop(i)
                    st.rerun()
            st.divider()

col1, col2 = st.columns(2)
compact_clicked = col1.button("🔬 BUILD (compact packing)", type="primary", use_container_width=True)
full_clicked = col2.button("🔬 BUILD (each peptide separately)", type="secondary", use_container_width=True)

def add_gaps_between_intervals(intervals, gap=0.2):
    if not intervals:
        return []
    intervals_sorted = sorted(intervals, key=lambda x: x[0])
    new_intervals = []
    for i, (s, e) in enumerate(intervals_sorted):
        if i < len(intervals_sorted) - 1:
            next_s = intervals_sorted[i+1][0]
            if e == next_s:
                new_e = e - gap
                if new_e > s:
                    new_intervals.append((s, new_e))
                else:
                    new_intervals.append((s, e))
                continue
        new_intervals.append((s, e))
    return new_intervals

def build_plot(packing_mode, show_dist):
    seq_clean = sequence.replace("\n", "").replace(" ", "").replace("\r", "").upper().strip()
    if not seq_clean:
        st.error("❌ Please enter a protein sequence!")
        return
    if not st.session_state.files_data:
        st.error("❌ Please add at least one CSV file!")
        return

    with st.spinner("Generating map..."):
        protein_len = len(seq_clean)
        n_blocks = (protein_len + line_length - 1) // line_length

        cond_peptides = []
        for finfo in st.session_state.files_data:
            df = finfo["df"]
            uniq = set()
            for _, row in df.iterrows():
                s = row[finfo["start_col"]]
                e = row[finfo["end_col"]]
                if pd.notna(s) and pd.notna(e) and s > 0 and e > 0:
                    uniq.add((int(s), int(e)))
            cond_peptides.append((finfo["name"], finfo["color"], sorted(list(uniq))))

        block_info = []
        for blk in range(n_blocks):
            start = blk * line_length + 1
            end = min((blk + 1) * line_length, protein_len)
            blk_seq = seq_clean[start - 1:end]
            cond_levels = []
            for name, color, peps in cond_peptides:
                intervals = []
                for s, e in peps:
                    if e >= start and s <= end:
                        s_loc = max(s, start) - start
                        e_loc = min(e, end) - start + 1
                        intervals.append((s_loc, e_loc))
                if packing_mode == "compact":
                    assigned = assign_levels(intervals)
                    max_level = max([lvl for _, _, lvl in assigned], default=-1) + 1
                else:
                    assigned = [(s, e, idx) for idx, (s, e) in enumerate(intervals)]
                    max_level = len(intervals)
                cond_levels.append((name, color, assigned, max_level))
            block_info.append((blk_seq, start, end, cond_levels))

        # Count rows
        total_rows = 0
        for blk_idx, (_, _, _, cl) in enumerate(block_info):
            total_rows += 1
            for _, _, _, ml in cl:
                total_rows += ml
                if ml > 1 and gap_factor > 0:
                    total_rows += (ml - 1)
            n_cond = len(cond_peptides)
            if n_cond > 1:
                total_rows += (n_cond - 1) * n_blocks
            if blk_idx < n_blocks - 1 and block_gap > 0:
                total_rows += 1

        fig_width = max(12, line_length * 0.2)
        fig_height = max(3, total_rows * 0.28)
        fig, axes = plt.subplots(total_rows, 1, figsize=(fig_width, fig_height),
                                 gridspec_kw={'hspace': 0})
        if total_rows == 1:
            axes = [axes]

        row = 0
        pep_h = peptide_height
        actual_peptide_gap = pep_h * gap_factor if gap_factor > 0 else 0

        for blk_idx, (blk_seq, blk_start, blk_end, cond_levels) in enumerate(block_info):
            ax_len = line_length
            # sequence row
            ax_seq = axes[row]; row += 1
            # amino acid letters (lower position)
            for i, aa in enumerate(blk_seq):
                ax_seq.text(i + 0.5, 0.5, aa, ha='center', va='center', fontsize=14)
            # position numbers (above letters)
            for i in range(len(blk_seq)):
                global_pos = blk_start + i
                if global_pos % 10 == 0 or global_pos == protein_len:
                    ax_seq.text(i + 0.5, 1.4, str(global_pos), ha='center', va='center',
                                fontsize=12, fontweight='normal')
            # block start/end labels
            ax_seq.text(-1.2, 0.7, str(blk_start), ha='right', va='center', fontsize=10, fontweight='bold')
            ax_seq.text(ax_len + 1.2, 0.7, str(blk_end), ha='left', va='center', fontsize=10, fontweight='bold')
            ax_seq.set_xlim(-2, ax_len + 2)
            ax_seq.set_ylim(0, 1.3)  # enlarged to fit numbers above
            ax_seq.set_yticks([])
            for sp in ['top', 'left', 'right', 'bottom']:
                ax_seq.spines[sp].set_visible(False)
            ax_seq.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
            ax_seq.set_xticks([])


            # peptides
            for cond_idx, (cond_name, cond_color, assigned, max_lvl) in enumerate(cond_levels):
                levels_dict = {}
                for s, e, lvl in assigned:
                    levels_dict.setdefault(lvl, []).append((s, e))
                for lvl in range(max_lvl):
                    ax_pep = axes[row]; row += 1
                    ax_pep.set_ylim(0, pep_h + 0.02)
                    y_start = 0.01
                    intervals_lvl = sorted(levels_dict.get(lvl, []), key=lambda x: x[0])
                    intervals_lvl = add_gaps_between_intervals(intervals_lvl, gap=0.1)
                    for s, e in intervals_lvl:
                        if e - s > 0:
                            ax_pep.add_patch(patches.Rectangle(
                                (s, y_start), e - s, pep_h,
                                linewidth=linewidth, edgecolor=border_color, facecolor=cond_color
                            ))
                    if lvl == 0:
                        # larger font for condition names, shifted left
                        ax_pep.text(-1.5, y_start + pep_h/2, cond_name,
                                    ha='right', va='center', fontsize=12, fontweight='bold')
                    ax_pep.set_xlim(-2, ax_len + 2)
                    ax_pep.set_yticks([])
                    for sp in ['top', 'left', 'right', 'bottom']:
                        ax_pep.spines[sp].set_visible(False)
                    ax_pep.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
                    ax_pep.set_xticks([])

                    if lvl < max_lvl - 1 and actual_peptide_gap > 0:
                        ax_gap = axes[row]; row += 1
                        ax_gap.set_visible(False)
                        ax_gap.set_ylim(0, actual_peptide_gap)
                        ax_gap.set_yticks([])
                        ax_gap.set_xticks([])
                        for sp in ['top', 'left', 'right', 'bottom']:
                            ax_gap.spines[sp].set_visible(False)
                        ax_gap.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

                if cond_idx < len(cond_levels) - 1 and condition_gap > 0:
                    ax_gap_cond = axes[row]; row += 1
                    ax_gap_cond.set_visible(False)
                    ax_gap_cond.set_ylim(0, condition_gap)
                    ax_gap_cond.set_yticks([])
                    ax_gap_cond.set_xticks([])
                    for sp in ['top', 'left', 'right', 'bottom']:
                        ax_gap_cond.spines[sp].set_visible(False)
                    ax_gap_cond.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

            if blk_idx < n_blocks - 1 and block_gap > 0:
                ax_gap_block = axes[row]; row += 1
                ax_gap_block.set_visible(False)
                ax_gap_block.set_ylim(0, block_gap)
                ax_gap_block.set_yticks([])
                ax_gap_block.set_xticks([])
                for sp in ['top', 'left', 'right', 'bottom']:
                    ax_gap_block.spines[sp].set_visible(False)
                ax_gap_block.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

        while row < len(axes):
            fig.delaxes(axes[row])
            row += 1

        plt.subplots_adjust(hspace=0, left=0.08, right=0.98, top=0.95, bottom=0.02)

        # Statistics
        cov_stats = []
        len_distributions = []
        for name, color, peps in cond_peptides:
            covered = set()
            lengths = []
            for s, e in peps:
                covered.update(range(max(1, s), min(protein_len, e) + 1))
                lengths.append(e - s + 1)
            cov_pct = len(covered) / protein_len * 100
            avg_len = sum(lengths) / len(lengths) if lengths else 0
            len_counts = Counter(lengths)
            cov_stats.append((name, len(covered), cov_pct, len(peps), avg_len, len_counts))
            len_distributions.append((name, color, lengths))

        #fig.suptitle(f"Protein length: {protein_len} aa | " +
        #             " | ".join([f"{n}: {c:.1f}%" for n, _, c, _, _, _ in cov_stats]),
        #             fontsize=9, y=0.99)
        plt.tight_layout(rect=[0, 0, 1, 0.97])

        st.pyplot(fig, use_container_width=False)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches='tight')
        buf.seek(0)
        st.download_button("💾 Download PNG (coverage map)", data=buf, file_name=f"peptide_coverage_{packing_mode}.png",
                           mime="image/png")

        with st.expander("📊 Coverage statistics"):
            for name, cnt, pct, num_pep, avg_len, len_counts in cov_stats:
                st.markdown(f"**{name}**")
                st.metric("Coverage", f"{cnt}/{protein_len} aa", f"{pct:.1f}%")
                st.metric("Number of peptides", num_pep)
                st.metric("Average peptide length", f"{avg_len:.1f} aa")
                if len_counts:
                    st.write("**Distribution by length:**")
                    for length in sorted(len_counts.keys()):
                        st.write(f"  • length {length}: {len_counts[length]} peptide(s)")
                else:
                    st.write("No peptides")
                st.divider()

        if show_dist and len_distributions:
            st.subheader("📊 Peptide length distribution")
            all_lengths = [l for _, _, lens in len_distributions for l in lens]
            if all_lengths:
                max_len = max(all_lengths)
                min_len = min(all_lengths)
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                width = 0.8 / len(len_distributions)
                for i, (name, color, lengths) in enumerate(len_distributions):
                    counts = Counter(lengths)
                    x_vals = sorted(counts.keys())
                    y_vals = [counts[l] for l in x_vals]
                    x_pos = [x + (i - (len(len_distributions)-1)/2) * width for x in x_vals]
                    ax2.bar(x_pos, y_vals, width=width, label=name, color=color, edgecolor='black', alpha=0.7)
                ax2.set_xlabel("Peptide length (aa)", fontsize=10)
                ax2.set_ylabel("Number of peptides", fontsize=10)
                ax2.set_title("Peptide length distribution", fontsize=12)
                ax2.legend()
                ax2.set_xticks(range(min_len, max_len+1))
                plt.tight_layout()
                st.pyplot(fig2)
                buf2 = io.BytesIO()
                fig2.savefig(buf2, format="png", dpi=150, bbox_inches='tight')
                buf2.seek(0)
                st.download_button("💾 Download PNG (length distribution)", data=buf2,
                                   file_name=f"peptide_length_distribution_{packing_mode}.png", mime="image/png")
            else:
                st.info("No data for length distribution.")

        st.success(f"✅ Done! Mode: {'Compact' if packing_mode == 'compact' else 'Each peptide separately'}")

if compact_clicked:
    build_plot("compact", show_length_dist)
elif full_clicked:
    build_plot("full", show_length_dist)
else:
    st.info("👈 Upload files, adjust settings and click one of the build buttons.")