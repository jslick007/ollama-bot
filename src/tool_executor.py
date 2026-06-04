import inspect
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, create_model


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class Tool:
    def __init__(
        self,
        fn: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.fn = fn
        self.name = name or fn.__name__
        self.description = description or (fn.__doc__ or "").strip()
        sig = inspect.signature(fn)
        fields = {}
        for p_name, p_param in sig.parameters.items():
            annotation = (
                p_param.annotation
                if p_param.annotation is not inspect.Parameter.empty
                else str
            )
            default = (
                ... if p_param.default is inspect.Parameter.empty else p_param.default
            )
            fields[p_name] = (annotation, default)
        self.InputModel = create_model(f"{self.name}_input", **fields)
        self.definition = self._build_definition()

    def _build_definition(self) -> ToolDefinition:
        properties = {}
        for f_name, f_field in self.InputModel.model_fields.items():
            prop = {
                "type": getattr(
                    self.InputModel.model_fields[f_name].annotation,
                    "__name__",
                    "string",
                )
            }
            if not f_field.is_required():
                prop["default"] = f_field.default
            properties[f_name] = prop
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={"type": "object", "properties": properties},
        )

    def execute(self, **kwargs) -> Any:
        validated = self.InputModel(**kwargs)
        return self.fn(**validated.model_dump())


class ToolRegistry:
    def __init__(self, allowlist: Optional[List[str]] = None):
        self._tools: Dict[str, Tool] = {}
        self.allowlist = allowlist

    def register(
        self,
        fn: Callable = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        def wrapper(f):
            tool = Tool(f, name=name, description=description)
            self._tools[tool.name] = tool
            return tool

        return wrapper(fn) if fn else wrapper

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def definitions(self) -> List[ToolDefinition]:
        return [t.definition for t in self._tools.values()]

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def execute(self, name: str, **kwargs) -> Any:
        if self.allowlist and name not in self.allowlist:
            raise PermissionError(f"Tool '{name}' is not in the allowlist")
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return tool.execute(**kwargs)


def tool(name: Optional[str] = None, description: Optional[str] = None):
    return ToolRegistry().register(name=name, description=description)
