"""Resolve merge conflicts in sprint-status.yaml"""

import re

path = "docs/sprint-artifacts/sprint-status.yaml"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()


# Use regex to find and replace all conflict blocks
def resolve_conflict(match):
    head = match.group(1)
    theirs = match.group(2)
    head = head.strip("\n")
    theirs = theirs.strip("\n")

    # Conflict 1: Epic ordering block
    if "epic-19" in head and "epic-18" in theirs:
        # Keep E18 from theirs (updated to done) + E19+E20 from head
        theirs_updated = (
            theirs.replace("# 1/4 stories complete", "# 6/6 stories complete")
            .replace("epic-18: in-progress", "epic-18: done")
            .replace(
                "e18-s4-demo-validation: in-progress", "e18-s4-demo-validation: done"
            )
            .replace(
                "e18-s5-extraction-quality-fuse-cartridge-no-access: review",
                "e18-s5-extraction-quality-fuse-cartridge-no-access: done",
            )
            .replace(
                "e18-s6-browser-demo-validation: drafted",
                "e18-s6-browser-demo-validation: done",
            )
            .replace("pending live E2E validation", "improvements done")
        )
        head_fixed = head.replace("# 1/1 stories complete", "# 1/1 stories complete")
        return theirs_updated + "\n\n" + head_fixed

    # Conflict 2: Summary counts
    if "Total Epics" in head and "Total Epics" in theirs:
        return (
            "# Total Epics: 20 (19 done, 0 in-progress, 0 backlog, 1 archived)\n"
            "# Total Stories: 131\n"
            "# Stories Done: 131 (100%)"
        )

    # Conflict 3: Last Updated and completed epics
    if "Last Updated" in head and "Last Updated" in theirs:
        return (
            "# Last Updated: 2026-02-23  # E18 production hardening + E19 marketing + E20 cross-site navigation/domain cutover complete.\n"
            "#\n"
            "# COMPLETED EPICS: E1, E2, E3, E4, E5, E6, E7, E9, E10, E11, E12, E13, E14, E15, E16, E17, E18, E19, E20\n"
            "# IN-PROGRESS EPICS: (none)"
        )

    # Fallback: prefer HEAD
    return head


pattern = re.compile(
    r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> origin/release", re.DOTALL
)
matches = list(pattern.finditer(content))
print(f"Found {len(matches)} conflicts")
for i, m in enumerate(matches):
    print(f"  Conflict {i + 1}: head starts with: {m.group(1)[:60]!r}")

new_content = pattern.sub(resolve_conflict, content)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)

# Verify no conflicts remain
remaining = re.findall(r"<<<<<<<?", new_content)
print(f"Remaining conflict markers: {len(remaining)}")
print("Done!")
