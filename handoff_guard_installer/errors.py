class InstallerError(RuntimeError):
    """Base error shown safely to installer users."""


class RepairRequiredError(InstallerError):
    """The managed block is malformed or duplicated."""


class ConfirmationRequiredError(InstallerError):
    """A local result was requested without confirming its preview."""
