#!/bin/bash
# sync-github-issues.sh
# Documents 4 known extraction accuracy issues
# Uncomment gh commands to create issues (requires gh CLI authenticated)

echo "=== ACM-AI Extraction Accuracy — Known Missing Records ==="
echo ""
echo "Current accuracy: 87% (27/31 test records passing)"
echo "Target: 100%"
echo ""
echo "The following 4 records are not yet extracted by the pipeline:"
echo ""

echo "1. Fuse cartridge — Auto Battery Charger, Switch Room (L1)"
echo "   Category: Product type not in training data"
# gh issue create \
#   --title "Extraction: Missing fuse cartridge record — Auto Battery Charger, Switch Room (L1)" \
#   --body "The pipeline does not extract the 'Fuse cartridge' ACM record from the Auto Battery Charger location in Switch Room, Level 1. This product type may not be in the training data." \
#   --label "extraction,accuracy,E18"

echo ""
echo "2. Flange joints — East Ductwork, Roof (G)"
echo "   Category: Unusual product description"
# gh issue create \
#   --title "Extraction: Missing flange joints record — East Ductwork, Roof (G)" \
#   --body "The pipeline does not extract the 'Flange joints' ACM record from East Ductwork on the Roof (Ground level). The product description may be too unusual for the current extraction model." \
#   --label "extraction,accuracy,E18"

echo ""
echo "3. No-access: Internal lining — Lift, Lift Foyer (G)"
echo "   Category: No-access area (may be intentionally excluded)"
# gh issue create \
#   --title "Extraction: Missing internal lining record — Lift, Lift Foyer (G)" \
#   --body "No-access area record for 'Internal lining' in Lift/Lift Foyer at Ground level. This may be intentionally excluded due to no-access classification but should still appear in the BAR register." \
#   --label "extraction,accuracy,E18,no-access"

echo ""
echo "4. No-access: Unknown — Room adj. Disabled Toilet, Main Foyer (G)"
echo "   Category: No-access area with unknown ACM type"
# gh issue create \
#   --title "Extraction: Missing unknown ACM record — Room adj. Disabled Toilet, Main Foyer (G)" \
#   --body "No-access area with unknown ACM type in Room adjacent to Disabled Toilet, Main Foyer at Ground level. Record exists in source PDF but is not captured by extraction pipeline." \
#   --label "extraction,accuracy,E18,no-access"

echo ""
echo "=== To create GitHub issues, uncomment the 'gh issue create' commands above ==="
echo "=== Requires: gh auth login ==="
