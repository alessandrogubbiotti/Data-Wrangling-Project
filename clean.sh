python3 << 'EOF'
import os
import re
import sys

tex_path = 'Report/report.tex'

if not os.path.exists(tex_path):
    print(f"❌ Errore: Non trovo {tex_path}")
    sys.exit(1)

with open(tex_path, "r", encoding="utf-8") as f:
    content = f.read()

# =========================
# PATTERN 1 (pipe-table)
# =========================
pattern1 = re.compile(
    r"Molti di questi file sono doppioni\. Ecco un esempio.*?"
    r"\\pandocbounded\{\\includegraphics\[.*?\]\{Images/([^}]+)\}\}.*?"
    r"\\pandocbounded\{\\includegraphics\[.*?\]\{Images/([^}]+)\}\}.*?\\textbar\{\}",
    re.DOTALL
)

def repl1(match):
    img1 = match.group(1)
    img2 = match.group(2)
    return rf"""Molti di questi file sono doppioni. Ecco un esempio:

\begin{{table}}[htbp]
\centering
\begin{{tabular}}{{cc}}
\textbf{{DOJ Released}} & \textbf{{House Released}} \\
\includegraphics[width=0.47\textwidth]{{Images/{img1}}} & \includegraphics[width=0.43\textwidth]{{Images/{img2}}} \\
\end{{tabular}}
\caption{{Confronto tra i documenti rilasciati dal DOJ e dalla House.}}
\label{{tab:doppioni}}
\end{{table}}"""

# =========================
# PATTERN 2 (longtable)
# =========================
pattern2 = re.compile(
    r"\\begin\{longtable\}.*?"
    r"DOJ Released.*?House Released.*?"
    r"\\pandocbounded\{\\includegraphics\[.*?\]\{Images/([^}]+)\}\}.*?&.*?"
    r"\\pandocbounded\{\\includegraphics\[.*?\]\{Images/([^}]+)\}\}.*?"
    r"\\end\{longtable\}",
    re.DOTALL
)

def repl2(match):
    img1 = match.group(1)
    img2 = match.group(2)
    return rf"""\begin{{table}}[htbp]
\centering
\begin{{tabular}}{{cc}}
\textbf{{DOJ Released}} & \textbf{{House Released}} \\
\includegraphics[width=0.45\textwidth]{{Images/{img1}}} & \includegraphics[width=0.45\textwidth]{{Images/{img2}}} \\
\end{{tabular}}
\caption{{Confronto tra i documenti rilasciati dal DOJ e dalla House.}}
\label{{tab:doppioni}}
\end{{table}}"""

# =========================
# APPLY REPLACEMENTS
# =========================
content, count1 = pattern1.subn(repl1, content)
content, count2 = pattern2.subn(repl2, content)

# =========================
# WRITE BACK
# =========================
with open(tex_path, "w", encoding="utf-8") as f:
    f.write(content)

# =========================
# REPORT
# =========================
if count1 > 0 or count2 > 0:
    print(f"✅ Sostituzioni completate:")
    print(f"   - Tabelle tipo 1 sostituite: {count1}")
    print(f"   - Tabelle tipo 2 sostituite: {count2}")
else:
    print("⚠️ Nessuna sostituzione effettuata (pattern non trovati)")

EOF

