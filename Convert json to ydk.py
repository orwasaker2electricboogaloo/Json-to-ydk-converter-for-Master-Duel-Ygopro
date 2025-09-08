# -*- coding: utf-8 -*-
"""
Drag & drop a WCS-style deck JSON onto this script (or run with a path):
- Extracts m.ids (main) and e.ids (extra)
- Maps IDs using 'cardnumber_map.txt' (format: "<id1> <id2>" per line; id1→id2)
- Writes a .ydk with the same base name as the dropped file

Usage:
  python make_ydk_from_json.py PATH/TO/deck.txt
or just drop the file on the script in Explorer.

Notes:
- If a source ID has no mapping, it is kept as-is and listed in console output.
- The input file may include comments like //...; we don't fully parse JSON,
  we just extract the arrays with regex, so comments are fine.
"""

import io
import os
import re
import sys

MAP_FILE = "cardnumber_map.txt"

# Regexes to capture the number lists right after m.ids and e.ids (robust to whitespace/newlines)
RE_MAIN = re.compile(r'"m"\s*:\s*\{\s*"ids"\s*:\s*\[([0-9,\s]+)\]', re.IGNORECASE | re.DOTALL)
RE_EXTRA = re.compile(r'"e"\s*:\s*\{\s*"ids"\s*:\s*\[([0-9,\s]+)\]', re.IGNORECASE | re.DOTALL)

def read_text(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()

def parse_num_list(s):
    """Turn '1,2,  3' into ['1','2','3'] (ignore empties)."""
    return [tok.strip() for tok in s.split(",") if tok.strip()]

def load_map(path):
    """Load id1→id2 map from cardnumber_map.txt (two tokens per line)."""
    m = {}
    if not os.path.exists(path):
        raise IOError("Mapping file not found: {}".format(path))
    with io.open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            parts = line.split()
            if len(parts) < 2:
                # skip malformed lines silently
                continue
            src, dst = parts[0], parts[1]
            if src not in m:
                m[src] = dst
    return m

def extract_ids(label, regex, text):
    m = regex.search(text)
    if not m:
        return []
    return parse_num_list(m.group(1))

def map_ids(ids, idmap):
    out, missing = [], []
    for x in ids:
        if x in idmap:
            out.append(idmap[x])
        else:
            out.append(x)  # keep original if missing
            missing.append(x)
    return out, missing

def write_ydk(out_path, main_ids, extra_ids, side_ids=None):
    # side deck optional; user example leaves it empty but includes !side
    lines = []
    lines.append("#created by Player")
    lines.append("#main")
    lines.extend(main_ids)
    lines.append("#extra")
    lines.extend(extra_ids)
    lines.append("!side")
    if side_ids:
        lines.extend(side_ids)
    with io.open(out_path, "w", encoding="utf-8") as f:
        f.write(u"\n".join(lines) + u"\n")

def main():
    if len(sys.argv) < 2:
        print("Drag a deck file onto this script, or run:\n  python {} <input_file>".format(os.path.basename(sys.argv[0])))
        sys.exit(1)

    in_path = sys.argv[1]
    if not os.path.exists(in_path):
        print("Input not found:", in_path)
        sys.exit(1)

    folder = os.path.dirname(os.path.abspath(in_path))
    map_path = os.path.join(folder, MAP_FILE)

    try:
        idmap = load_map(map_path)
    except Exception as e:
        print("Error loading map '{}': {}".format(map_path, e))
        sys.exit(1)

    text = read_text(in_path)

    main_src = extract_ids("main", RE_MAIN, text)
    extra_src = extract_ids("extra", RE_EXTRA, text)

    if not main_src and not extra_src:
        print("Could not find m.ids or e.ids in the input file.")
        sys.exit(1)

    main_mapped, miss_main = map_ids(main_src, idmap)
    extra_mapped, miss_extra = map_ids(extra_src, idmap)

    base = os.path.splitext(os.path.basename(in_path))[0]
    out_path = os.path.join(folder, base + ".ydk")
    write_ydk(out_path, main_mapped, extra_mapped)

    print("Wrote:", out_path)
    if miss_main or miss_extra:
        print("Unmapped IDs kept as-is:")
        if miss_main:
            print("  Main:", ", ".join(miss_main))
        if miss_extra:
            print("  Extra:", ", ".join(miss_extra))
    else:
        print("All IDs mapped successfully.")

if __name__ == "__main__":
    main()
