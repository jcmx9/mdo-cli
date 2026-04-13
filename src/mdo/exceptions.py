"""Project-specific exceptions for mdo-cli."""


class MdoError(Exception):
    """Base exception for all mdo errors."""


class FontError(MdoError):
    """Raised when required fonts are missing."""


class ToolNotFoundError(MdoError):
    """Raised when an external tool (pandoc, typst, git) is not found."""


class FrontmatterError(MdoError):
    """Raised when letter frontmatter is invalid or missing."""


class CompileError(MdoError):
    """Raised when Typst compilation fails."""


class TemplateError(MdoError):
    """Raised when template download or installation fails."""
