import ast
import re
import sys

import managers


PYTHON_COMPLETION_EXTENSIONS = frozenset(('.py', '.pyw', '.pyx'))


class CompletionItem:
    def __init__(
        self,
        name,
        complete,
        comp_type,
        docstring_val="",
        prefix_length=0,
        docstring_loader=None,
        end_char=None,
    ):
        self.name = name
        self.complete = complete
        self.type = comp_type
        self._docstring = docstring_val
        self._docstring_loader = docstring_loader
        self.prefix_length = prefix_length
        self.end_char = end_char

    def get_completion_prefix_length(self):
        return self.prefix_length

    def docstring(self):
        if self._docstring_loader is not None:
            loader = self._docstring_loader
            self._docstring_loader = None
            try:
                self._docstring = loader()
            except Exception:
                self._docstring = ""
        return self._docstring


class AutocompleteProvider:
    def __init__(self):
        # Lazy load jedi to avoid heavy startup overhead if possible
        self._jedi = None

    def _get_jedi(self):
        if self._jedi is None:
            import jedi
            self._jedi = jedi
        return self._jedi

    @staticmethod
    def _completion_namespace(text, line, namespace):
        resolved = dict(namespace or {})
        source = '\n'.join(text.splitlines()[:max(line - 1, 0)])
        if not source.strip():
            return resolved

        try:
            statements = ast.parse(source).body
        except SyntaxError:
            return resolved

        missing = object()
        for statement in statements:
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    value = sys.modules.get(alias.name, missing)
                    if value is missing:
                        continue
                    if alias.asname:
                        resolved[alias.asname] = value
                    else:
                        root_name = alias.name.partition('.')[0]
                        root = sys.modules.get(root_name, missing)
                        if root is not missing:
                            resolved[root_name] = root
                continue

            if (
                not isinstance(statement, ast.ImportFrom)
                or statement.level
                or not statement.module
            ):
                continue

            parent = sys.modules.get(statement.module)
            for alias in statement.names:
                if alias.name == '*':
                    continue
                value = sys.modules.get(
                    statement.module + '.' + alias.name,
                    missing,
                )
                if value is missing and parent is not None:
                    value = vars(parent).get(alias.name, missing)
                if value is not missing:
                    resolved[alias.asname or alias.name] = value

        return resolved

    @staticmethod
    def _runtime_completions(text, line, column, namespace):
        lines = text.splitlines()
        if line < 1 or line > len(lines):
            return []

        missing = object()
        current_line = lines[line - 1][:column]
        from_import = re.match(
            r'^\s*from\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)'
            r'\s+import\s*([A-Za-z_]\w*)?$',
            current_line,
        )
        if from_import:
            module_name, prefix = from_import.groups()
            value = sys.modules.get(module_name, missing)
        else:
            member = re.search(
                r'\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.'
                r'([A-Za-z_]\w*)?$',
                current_line,
            )
            if not member:
                return []
            path, prefix = member.groups()
            parts = path.split('.')
            value = namespace.get(parts[0], missing)
            try:
                for part in parts[1:]:
                    value = getattr(value, part)
            except Exception:
                return []

        if value is missing:
            return []
        try:
            names = dir(value)
        except Exception:
            return []

        members = getattr(value, '__dict__', {})
        items = []
        prefix = prefix or ''
        for name in names:
            if not name.startswith(prefix):
                continue
            member = members.get(name, missing)
            comp_type = (
                'class' if isinstance(member, type)
                else 'function' if callable(member)
                else 'statement'
            )
            items.append(CompletionItem(
                name=name,
                complete=name[len(prefix):],
                comp_type=comp_type,
                prefix_length=len(prefix),
                docstring_loader=(
                    lambda obj=value, attr=name:
                    getattr(obj, attr).__doc__ or ''
                ),
            ))
        return items

    def get_completions(self, text, line, column, namespace=None, fuzzy=True, context=None, prefer_single_quotes=False):
        """
        Returns a list of CompletionItem objects.
        """
        comp_items = []
        context_completer = False

        preferred_quote = "'" if prefer_single_quotes else '"'
        other_quote = '"' if prefer_single_quotes else "'"
        namespace = self._completion_namespace(text, line, namespace)

        def format_quotes(name, complete, comp_type):
            if comp_type == 'string' or (len(name) >= 2 and name[0] in ('"', "'") and name[-1] in ('"', "'")):
                # Convert quotes in name
                if len(name) >= 2 and name[0] == other_quote and name[-1] == other_quote:
                    name = preferred_quote + name[1:-1] + preferred_quote
                # Convert quotes in complete
                if complete:
                    if len(complete) >= 2 and complete[0] == other_quote and complete[-1] == other_quote:
                        complete = preferred_quote + complete[1:-1] + preferred_quote
                    elif complete[0] == other_quote:
                        complete = preferred_quote + complete[1:]
                    elif complete[-1] == other_quote:
                        complete = complete[:-1] + preferred_quote
            return name, complete

        # 1. Try Context-Specific Completers (e.g., Maya, Nuke specific cmds)
        if context and context in managers.contextCompleters:
            current_line_text = text.split('\n')[line - 1] if text else ''
            # We don't have exact cursor offset here easily, but managers used it roughly
            # The original code passed `line` string to contextCompleters.
            comp, extra = managers.contextCompleters[context](current_line_text, namespace)
            if comp or extra:
                context_completer = True
                for name, complete, end_char in (comp or []) + (extra or []):
                    name, complete = format_quotes(
                        name,
                        complete,
                        'statement',
                    )
                    comp_items.append(CompletionItem(
                        name,
                        complete,
                        'statement',
                        end_char=end_char,
                    ))
                
                if comp_items:
                    return comp_items

        runtime_items = self._runtime_completions(
            text,
            line,
            column,
            namespace,
        )
        if runtime_items:
            return runtime_items

        # 2. Fallback to Jedi Autocompletion
        if not context_completer:
            jedi = self._get_jedi()
            project = None
            
            # Prepend autoImports if necessary
            offs = 0
            if context and context in managers.autoImport:
                autoImp = managers.autoImport.get(context, '')
                text = autoImp + text
                offs = len(autoImp.split('\n')) - 1
            
            # Shift the line number due to autoImports
            jedi_line = line + offs
            
            try:
                if namespace:
                    script = jedi.Interpreter(
                        text,
                        namespaces=[namespace],
                        project=project,
                    )
                else:
                    script = jedi.Script(code=text, project=project)
                    
                jedi_comps = script.complete(line=jedi_line, column=column, fuzzy=fuzzy)
                
                for c in jedi_comps:
                    # Filter out 'mro' as original code did
                    if c.name == 'mro':
                        continue
                    
                    prefix_len = 0
                    if hasattr(c, 'get_completion_prefix_length'):
                        prefix_len = c.get_completion_prefix_length()

                    name, complete = format_quotes(c.name, c.complete, c.type)

                    comp_items.append(CompletionItem(
                        name=name,
                        complete=complete,
                        comp_type=c.type,
                        prefix_length=prefix_len,
                        docstring_loader=c.docstring,
                    ))
            except Exception:
                pass

        # Filter completions for dictionary keys if inside brackets
        current_line_text = text.split('\n')[line - 1] if text else ''
        prefix = current_line_text[:column]
        if re.search(r'\w+\s*\[\s*[\'"]?\s*\w*$', prefix):
            string_comps = [c for c in comp_items if c.type == 'string' or (len(c.name) >= 2 and c.name[0] in ('"', "'") and c.name[-1] in ('"', "'"))]
            if string_comps:
                comp_items = string_comps

        return comp_items
