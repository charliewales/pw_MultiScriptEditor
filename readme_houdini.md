## Houdini install

### Houdini 19+

  - extract module `multi_script_editor` to PYTHONPATH

    Example: `{HOME}/Documents/Houdini19.X/scripts/python/multi_script_editor`
  - create new tool on shelf

```python
import multi_script_editor
multi_script_editor.show()
```

Also you can use .pypanel file:
>/managers/houdini/multi_script_editor_16.pypanel (for Houdini 16+)
