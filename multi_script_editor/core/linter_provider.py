import ast


class LinterProvider:
    def __init__(self):
        self._last_code = None
        self._last_tree = None

    def check_syntax(self, code):
        """
        Validates the python syntax using compile().
        Returns a dictionary of errors: {line_number: error_message}
        """
        self._last_code = code
        self._last_tree = None
        syntax_errors = {}
        if code.strip():
            try:
                tree = compile(
                    code.encode('utf-8'),
                    '<string>',
                    'exec',
                    flags=ast.PyCF_ONLY_AST,
                )
                compile(tree, '<string>', 'exec')
                self._last_tree = tree
            except SyntaxError as e:
                syntax_errors[e.lineno] = e.msg
            except Exception:
                pass
        return syntax_errors

    def syntax_tree_for(self, code):
        if code == self._last_code:
            return self._last_tree
        return None
