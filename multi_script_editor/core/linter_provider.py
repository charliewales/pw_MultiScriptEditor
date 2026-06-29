class LinterProvider:
    def check_syntax(self, code):
        """
        Validates the python syntax using compile().
        Returns a dictionary of errors: {line_number: error_message}
        """
        syntax_errors = {}
        if code.strip():
            try:
                compile(code.encode('utf-8'), '<string>', 'exec')
            except SyntaxError as e:
                syntax_errors[e.lineno] = e.msg
            except Exception:
                pass
        return syntax_errors
