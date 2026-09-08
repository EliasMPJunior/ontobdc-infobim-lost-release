class TestManifestError(Exception):
    """A manifest is structurally or semantically invalid.

    Raised while loading or validating a catalog. Must propagate to the CLI
    boundary so `test validate`/`test run` exit with a non-zero status.
    """


class TestExecutionError(Exception):
    """An observer or executor could not run its target as configured.

    Caught internally and turned into `ObservationStatus.ERROR` or
    `ActionOutcomeStatus.ERROR` (semantic-test-orchestrator.md, 8.4): a
    configuration or runtime error is not the same as an unsatisfied state.
    """
