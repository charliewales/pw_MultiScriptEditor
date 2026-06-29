import ast
import re

class OutlineParser:
    @staticmethod
    def parse(code):
        try:
            tree = ast.parse(code)
        except Exception:
            return OutlineParser._parse_regex(code)

        symbols = []

        class OutlineVisitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                symbols.append({
                    'name': "class {0}".format(node.name),
                    'line': node.lineno,
                    'indent': 0,
                    'type': 'class'
                })
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                symbols.append({
                    'name': "def {0}()".format(node.name),
                    'line': node.lineno,
                    'indent': 1,
                    'type': 'function'
                })

        OutlineVisitor().visit(tree)
        symbols.sort(key=lambda x: x['line'])
        return symbols

    @staticmethod
    def _parse_regex(code):
        symbols = []
        lines = code.split('\n')
        for i, line in enumerate(lines):
            line_num = i + 1
            class_match = re.match(r'^(\s*)class\s+(\w+)', line)
            if class_match:
                indent = len(class_match.group(1)) // 4
                name = class_match.group(2)
                symbols.append({
                    'name': "class {0}".format(name),
                    'line': line_num,
                    'indent': indent,
                    'type': 'class'
                })
                continue
            def_match = re.match(r'^(\s*)def\s+(\w+)', line)
            if def_match:
                indent = len(def_match.group(1)) // 4
                name = def_match.group(2)
                symbols.append({
                    'name': "def {0}()".format(name),
                    'line': line_num,
                    'indent': indent,
                    'type': 'function'
                })
        return symbols
