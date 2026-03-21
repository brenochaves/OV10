# QUALITY GATES

Quality gates must be adapted to the actual repository stack.

## Default gates

1. do not knowingly break buildable paths
2. prefer smallest trustworthy validation set for each change
3. document validation gaps honestly
4. do not claim full coverage unless evidence exists
5. do not merge architectural changes silently
6. update operator-facing docs if behavior changes materially

## Validation guidance

Prefer this order:
- targeted tests near the changed code
- lints or static checks already used by the repository
- smoke validation for affected entry points
- broader suites only when risk justifies cost
