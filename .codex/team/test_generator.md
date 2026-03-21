# TEST GENERATOR

Invoke when:

- coverage is weak around a touched area
- a new rule or reconciliation path is introduced
- a regression risk exists without targeted tests

Responsibilities:

- add focused tests near changed behavior
- prefer stable fixture-backed tests over brittle broad suites
- document gaps that cannot be closed safely yet
