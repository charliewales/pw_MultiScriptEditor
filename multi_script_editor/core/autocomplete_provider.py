import re
import managers

class CompletionItem:
    def __init__(self, name, complete, comp_type, docstring_val="", prefix_length=0):
        self.name = name
        self.complete = complete
        self.type = comp_type
        self._docstring = docstring_val
        self.prefix_length = prefix_length

    def get_completion_prefix_length(self):
        return self.prefix_length

    def docstring(self):
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

    def get_completions(self, text, line, column, namespace=None, fuzzy=True, context=None, prefer_single_quotes=False):
        """
        Returns a list of CompletionItem objects.
        """
        comp_items = []
        context_completer = False

        preferred_quote = "'" if prefer_single_quotes else '"'
        other_quote = '"' if prefer_single_quotes else "'"

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
                # Format them as CompletionItem
                if comp:
                    for c in comp:
                        name, complete = format_quotes(c.name, getattr(c, 'complete', ''), getattr(c, 'type', 'statement'))
                        comp_items.append(CompletionItem(name, complete, getattr(c, 'type', 'statement'), c.docstring() if hasattr(c, 'docstring') else ''))
                if extra:
                    for c in extra:
                        name, complete = format_quotes(c.name, getattr(c, 'complete', ''), getattr(c, 'type', 'statement'))
                        comp_items.append(CompletionItem(name, complete, getattr(c, 'type', 'statement'), c.docstring() if hasattr(c, 'docstring') else ''))
                
                if comp_items:
                    return comp_items

        # 2. Fallback to Jedi Autocompletion
        if not context_completer:
            jedi = self._get_jedi()
            
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
                    script = jedi.Interpreter(text, namespaces=[namespace])
                else:
                    script = jedi.Script(code=text)
                    
                jedi_comps = script.complete(line=jedi_line, column=column, fuzzy=fuzzy)
                
                for c in jedi_comps:
                    # Filter out 'mro' as original code did
                    if c.name == 'mro':
                        continue
                    
                    doc = ''
                    try:
                        doc = c.docstring()
                    except Exception:
                        pass
                        
                    prefix_len = 0
                    if hasattr(c, 'get_completion_prefix_length'):
                        prefix_len = c.get_completion_prefix_length()

                    name, complete = format_quotes(c.name, c.complete, c.type)

                    comp_items.append(CompletionItem(
                        name=name,
                        complete=complete,
                        comp_type=c.type,
                        docstring_val=doc,
                        prefix_length=prefix_len
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
