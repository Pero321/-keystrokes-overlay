"""Checks block entity renderers for stale VertexConsumer writes.

VertexConsumerProvider.Immediate keeps exactly one active layer. Asking it for a
different layer calls draw() on the current buffer, which ends it -- so a
VertexConsumer fetched earlier and written to afterwards throws

    java.lang.IllegalStateException: Not building!

and takes the game down with "Rendering Block Entity". The compiler cannot see
this, and neither can a geometry preview, so it gets its own check.

The rule enforced here: within a render method, every write to a VertexConsumer
must target the most recently fetched one.

    python3 tools/check_render_buffers.py
"""
import os, re, sys

JAVA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "src", "main", "java")

# calls that emit vertices. The consumer is not always the first argument, so
# the whole argument list is scanned for a known consumer name rather than
# assuming a position.
WRITE_CALL = re.compile(r"\b(cylinder|disc|quad|put|vertex)\s*\(")
ACQUIRE = re.compile(r"VertexConsumer\s+(\w+)\s*=\s*\w+\.getBuffer\s*\(")
IDENT = re.compile(r"\b\w+\b")

def call_args(text, open_paren):
    """Returns the argument text of a call whose '(' is at open_paren."""
    depth, i = 0, open_paren
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:i]
        i += 1
    return ""

def check_file(path):
    src = open(path).read()
    if "BlockEntityRenderer" not in src:
        return []
    problems = []
    # only look inside render(...) bodies
    for m in re.finditer(r"public void render\s*\([^)]*\)\s*\{", src):
        depth, i = 0, m.end() - 1
        while i < len(src):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = src[m.end():i]

        consumers = set(ACQUIRE.findall(body))
        if not consumers:
            continue
        events = []
        for a in ACQUIRE.finditer(body):
            events.append((a.start(), "acquire", a.group(1)))
        for w in WRITE_CALL.finditer(body):
            args = call_args(body, w.end() - 1)
            for name in IDENT.findall(args):
                if name in consumers:
                    events.append((w.start(), "write", name))
                    break
        events.sort()

        active = None
        for pos, kind, name in events:
            if kind == "acquire":
                active = name
            elif name != active:
                line = body[:pos].count("\n") + body[:m.end()].count("\n") + 1
                problems.append(
                    f"{os.path.basename(path)}: writes to '{name}' after fetching "
                    f"'{active}' (line ~{line}) -- '{name}' has already been flushed")
    return problems

found = []
scanned = 0
for dirpath, _, files in os.walk(JAVA):
    for f in files:
        if f.endswith(".java"):
            p = os.path.join(dirpath, f)
            if "BlockEntityRenderer" in open(p).read():
                scanned += 1
                found += check_file(p)

print(f"scanned {scanned} block entity renderer(s)")
if found:
    print("\nPROBLEMS:")
    for p in found:
        print("  -", p)
    sys.exit(1)
print("buffer discipline OK: every write targets the most recently fetched buffer")
