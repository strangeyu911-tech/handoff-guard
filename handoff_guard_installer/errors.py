class InstallerError(RuntimeError):
    """Base error shown safely to installer users."""


class SettingsUnavailableError(InstallerError):
    """ChatGPT settings could not be reached."""


class UnsafeReadError(InstallerError):
    """Existing Custom Instructions could not be read safely."""


class RepairRequiredError(InstallerError):
    """The managed block is malformed or duplicated."""


class ConfirmationRequiredError(InstallerError):
    """A write was attempted without confirming its preview."""


class VerificationError(InstallerError):
    """The saved value could not be verified."""
