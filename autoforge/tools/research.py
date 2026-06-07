from pydantic import BaseModel

from .common import GenericOutput, ListOutput, TextOutput
from .registry import register_tool


class QueryInput(BaseModel):
    query: str
    limit: int = 5


class PackageInput(BaseModel):
    package: str
    ecosystem: str = "python"


def _adapter(name: str, query: str, limit: int) -> GenericOutput:
    return GenericOutput(
        message=f"{name} adapter result",
        data={
            "query": query,
            "results": [
                {"title": f"{name} result {idx + 1}", "url": f"https://example.invalid/{name}/{idx + 1}"}
                for idx in range(limit)
            ],
            "note": "Wire this adapter to an approved provider in production.",
        },
    )


@register_tool("research", description="Search the web through a provider adapter")
def web_search(inp: QueryInput) -> GenericOutput:
    return _adapter("web_search", inp.query, inp.limit)


@register_tool("research", description="Look up dependency metadata")
def dependency_lookup(inp: PackageInput) -> GenericOutput:
    return GenericOutput(message="dependency lookup", data={"package": inp.package, "ecosystem": inp.ecosystem, "latest": "unknown"})


@register_tool("research", description="Search GitHub")
def github_search(inp: QueryInput) -> GenericOutput:
    return _adapter("github_search", inp.query, inp.limit)


@register_tool("research", description="Search Stack Overflow")
def stackoverflow_search(inp: QueryInput) -> GenericOutput:
    return _adapter("stackoverflow_search", inp.query, inp.limit)


@register_tool("research", description="Search package registries")
def package_search(inp: QueryInput) -> GenericOutput:
    return _adapter("package_search", inp.query, inp.limit)


@register_tool("research", description="Summarize documentation snippets")
def docs_summarize(inp: QueryInput) -> TextOutput:
    return TextOutput(text=f"Summary placeholder for {inp.query}", metadata={"limit": inp.limit})


@register_tool("research", description="Assess security advisory risk")
def security_advisory_lookup(inp: PackageInput) -> GenericOutput:
    return GenericOutput(message="security advisory lookup", data={"package": inp.package, "advisories": []})


@register_tool("research", description="Find code examples")
def code_example_search(inp: QueryInput) -> ListOutput:
    items = [f"example for {inp.query} #{idx + 1}" for idx in range(inp.limit)]
    return ListOutput(items=items, count=len(items))


@register_tool("research", description="Look up API compatibility notes")
def api_compatibility_lookup(inp: PackageInput) -> GenericOutput:
    return GenericOutput(message="compatibility lookup", data={"package": inp.package, "breaking_changes": []})

