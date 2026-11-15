"""PDD — Proposition-Driven Development, shipped as bundled Hermes skills.

Each directory under ``skills/`` that contains a ``SKILL.md`` is registered with
``ctx.register_skill()``, which makes it loadable as ``skill_view("pdd:<name>")``.
Registered skills are read-only: they are never copied into ``~/.hermes/skills/``
and cannot be edited (or curated) there.
"""

from pathlib import Path

_SKILLS_DIR = Path(__file__).parent / "skills"


def register(ctx):
    """Register every bundled skill directory with the plugin's namespace."""
    if not _SKILLS_DIR.is_dir():
        return
    for child in sorted(_SKILLS_DIR.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            # The name becomes "<plugin>:<child.name>"; the frontmatter supplies
            # the description the model sees in <available_skills>.
            ctx.register_skill(child.name, skill_md)
