import os
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to True since we're using a static HTML folder.
_RELEASE = True

if not _RELEASE:
    # Not used, but standard for components in development
    _component_func = components.declare_component(
        "custom_chat",
        url="http://localhost:3001",
    )
else:
    # When releasing, we use the build/frontend dir
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend")
    _component_func = components.declare_component("custom_chat", path=build_dir)

def custom_chat(key=None):
    """
    Creates a new instance of the custom chat component.
    """
    component_value = _component_func(key=key, default=None)
    return component_value
