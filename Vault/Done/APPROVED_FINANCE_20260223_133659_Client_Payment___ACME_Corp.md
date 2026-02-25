---
type: payment
action: payment
amount: 1200.00
recipient: Client Payment - ACME Corp
date: 2026-02-03
status: approved
priority: high
---

# ⚠️ Large Transaction Flagged

**Amount:** 1200.00
**Description:** Client Payment - ACME Corp
**Date:** 2026-02-03
**Balance After:** 6200.00

> This transaction exceeds the approval threshold of $500.00.

## Actions Required
- [ ] Verify this transaction is expected
- [x] Move to `/Approved` if OK, `/Rejected` if suspicious
- [ ] Contact bank if unrecognised

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.
