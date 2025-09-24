import json
import os
from pathlib import Path

base = Path(r"c:\Users\Administrator\Documents\mcp_database")
errors = []
notes = []

files = {
    'buckets': base / 'configs' / 'personas' / 'karlach' / 'buckets.v1.json',
    'templates': base / 'configs' / 'personas' / 'karlach' / 'freeplay_templates.v1.json'
}

data = {}
for name, path in files.items():
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
            # strip possible leading/trailing non-json like backticks (defensive)
            text_stripped = text.strip()
            # If file starts with ``` try to remove code fence blocks
            if text_stripped.startswith('```'):
                # remove first and last fence
                parts = text_stripped.split('\n')
                # remove any ``` lines
                lines = [l for l in parts if not l.strip().startswith('```')]
                text_clean = '\n'.join(lines)
            else:
                text_clean = text
            data[name] = json.loads(text_clean)
    except Exception as e:
        errors.append(f"Failed to parse {path}: {e}")

if errors:
    print("SYNTAX ERRORS:\n")
    for e in errors:
        print(e)
    raise SystemExit(1)

# Basic cross-file validations
buckets = data['buckets']
templates = data['templates']

# 1) bucket names present in templates.templates
bucket_names = [b.get('name') for b in buckets.get('buckets', []) if 'name' in b]
template_keys = list(templates.get('templates', {}).keys())
missing_in_templates = [n for n in bucket_names if n not in template_keys]
extra_in_templates = [k for k in template_keys if k not in bucket_names]

if missing_in_templates:
    notes.append(f"Bucket names missing in freeplay_templates.templates: {missing_in_templates}")
if extra_in_templates:
    notes.append(f"Template keys without matching bucket in buckets.v1.json: {extra_in_templates}")

# 2) base_weights keys match bucket names
base_weights = buckets.get('base_weights', {})
bw_keys = list(base_weights.keys())
mismatch_bw = [k for k in bw_keys if k not in bucket_names]
if mismatch_bw:
    notes.append(f"base_weights contains keys not in bucket names: {mismatch_bw}")

# 3) situational_triggers references
situational_triggers = buckets.get('situational_triggers', [])
st_references = set()
for st in situational_triggers:
    situ = st.get('situational')
    if situ:
        st_references.add(situ)

situational_templates = templates.get('situational_templates', {})
missing_situ = [s for s in st_references if s not in situational_templates]
if missing_situ:
    notes.append(f"situational_triggers reference missing situational_templates: {missing_situ}")

# 4) meta.narrator_move existence and enforce flag
meta = templates.get('meta', {})
if 'narrator_move' not in meta:
    notes.append("freeplay_templates.meta missing 'narrator_move' runtime guidance")
else:
    nm = meta['narrator_move']
    enf = nm.get('enforce_three_line_format')
    if enf is not True:
        notes.append("freeplay_templates.meta.narrator_move.enforce_three_line_format is not True")

# 5) blacklist items not appearing verbatim in templates and buckets
blacklist = buckets.get('template_blacklist', [])
if not isinstance(blacklist, list):
    notes.append("buckets.template_blacklist is not a list")
else:
    # gather all textual templates
    all_texts = []
    # from freeplay_templates templates
    for k, arr in templates.get('templates', {}).items():
        for t in arr:
            if isinstance(t, str):
                all_texts.append(t)
    # situational templates
    for k, obj in templates.get('situational_templates', {}).items():
        for t in obj.get('templates', []):
            if isinstance(t, str):
                all_texts.append(t)
    # from buckets micro/macro
    for b in buckets.get('buckets', []):
        tpls = b.get('templates', {})
        for key in ['micro', 'macro']:
            if key in tpls:
                for item in tpls[key]:
                    if isinstance(item, str):
                        all_texts.append(item)
                    elif isinstance(item, dict):
                        all_texts.append(item.get('text',''))
    # check
    found = []
    for bl in blacklist:
        for txt in all_texts:
            if bl.strip() and bl in txt:
                found.append((bl, txt))
    if found:
        details = '\n'.join([f"BLACKLIST '{bl}' found in template: {txt}" for bl, txt in found])
        notes.append("Some blacklist items appear in templates (should be avoided):\n" + details)

# 6) Ensure narrator_move exists in situational_templates (already checked) and has reasonable template count
if 'narrator_move' in situational_templates:
    count = len(situational_templates['narrator_move'].get('templates', []))
    if count < 1:
        notes.append("narrator_move situational_templates exists but has no templates")

# 7) Report any obvious key typos: check for both 'situational_templates' presence
required_keys = ['templates', 'situational_templates', 'meta']
for k in required_keys:
    if k not in templates:
        notes.append(f"freeplay_templates.v1.json missing top-level key: {k}")

# Summary
print("STATIC VALIDATION REPORT:\n")
if notes:
    print("NOTES/ISSUES FOUND:\n")
    for n in notes:
        print("- "+n)
else:
    print("No issues found. All basic checks passed.")

# print short success
print('\nDone.')
