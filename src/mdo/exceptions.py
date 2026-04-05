class MdoError(Exception):
    """Base exception for mdo-cli."""


class ProfileExistsError(MdoError):
    """profile.yaml already exists."""


class ProfileNotFoundError(MdoError):
    """profile.yaml not found in current directory."""


class FontMissingError(MdoError):
    """Required system fonts are missing."""


class TypstNotFoundError(MdoError):
    """typst CLI not found."""


class SignatureNotFoundError(MdoError):
    """Signature image file not found."""


class CompileError(MdoError):
    """typst compile failed."""


class InvalidLetterError(MdoError):
    """Letter .md file has invalid or missing frontmatter."""
