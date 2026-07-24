import ast
import re


class OutlineParser:
    @staticmethod
    def parse(code, ext='.py'):
        if ext == '.py':
            try:
                tree = ast.parse(code)
                symbols = []

                class OutlineVisitor(ast.NodeVisitor):
                    def visit_ClassDef(self, node):
                        symbols.append({
                            'name': "class {0}".format(node.name),
                            'line': node.lineno,
                            'indent': getattr(node, 'col_offset', 0) // 4,
                            'type': 'class'
                        })
                        self.generic_visit(node)

                    def visit_FunctionDef(self, node):
                        symbols.append({
                            'name': "def {0}()".format(node.name),
                            'line': node.lineno,
                            'indent': getattr(node, 'col_offset', 0) // 4,
                            'type': 'function'
                        })
                        self.generic_visit(node)

                OutlineVisitor().visit(tree)
                symbols.sort(key=lambda x: x['line'])
                return symbols
            except Exception:
                return OutlineParser._parse_regex(code, ext)
        else:
            return OutlineParser._parse_regex(code, ext)

    @staticmethod
    def _parse_regex(code, ext):
        symbols = []
        lines = code.split('\n')
        for i, line in enumerate(lines):
            line_num = i + 1
            
            if ext == '.py':
                class_match = re.match(r'^(\s*)class\s+(\w+)', line)
                if class_match:
                    indent = len(class_match.group(1)) // 4
                    name = class_match.group(2)
                    symbols.append({'name': "class {0}".format(name), 'line': line_num, 'indent': indent, 'type': 'class'})
                    continue
                def_match = re.match(r'^(\s*)def\s+(\w+)', line)
                if def_match:
                    indent = len(def_match.group(1)) // 4
                    name = def_match.group(2)
                    symbols.append({'name': "def {0}()".format(name), 'line': line_num, 'indent': indent, 'type': 'function'})
                    continue
            
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                class_match = re.search(r'^(\s*)class\s+(\w+)', line)
                if class_match:
                    symbols.append({'name': "class {0}".format(class_match.group(2)), 'line': line_num, 'indent': len(class_match.group(1)) // 4, 'type': 'class'})
                    continue
                func_match = re.search(r'^(\s*)(?:async\s+)?function\s+(\w+)', line)
                if func_match:
                    symbols.append({'name': "function {0}()".format(func_match.group(2)), 'line': line_num, 'indent': len(func_match.group(1)) // 4, 'type': 'function'})
                    continue
                arrow_match = re.search(r'^(\s*)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>', line)
                if arrow_match:
                    symbols.append({'name': "{0}()".format(arrow_match.group(2)), 'line': line_num, 'indent': len(arrow_match.group(1)) // 4, 'type': 'function'})
                    continue

            elif ext in ['.cpp', '.c', '.h', '.hpp', '.vex']:
                class_match = re.search(r'^(\s*)(?:class|struct)\s+(\w+)', line)
                if class_match:
                    symbols.append({'name': "{0} {1}".format("class" if "class" in line else "struct", class_match.group(2)), 'line': line_num, 'indent': len(class_match.group(1)) // 4, 'type': 'class'})
                    continue
                func_match = re.search(r'^(\s*)[\w\:]+\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{', line)
                if func_match:
                    name = func_match.group(2)
                    if name not in ['if', 'while', 'for', 'switch', 'catch']:
                        symbols.append({'name': "{0}()".format(name), 'line': line_num, 'indent': len(func_match.group(1)) // 4, 'type': 'function'})
                    continue
            
            elif ext == '.mel':
                proc_match = re.search(r'^(\s*)(?:global\s+)?proc\s+(?:[\w\[\]]+\s+)?(\w+)\s*\(', line)
                if proc_match:
                    symbols.append({'name': "proc {0}()".format(proc_match.group(2)), 'line': line_num, 'indent': len(proc_match.group(1)) // 4, 'type': 'function'})
                    continue
            
            elif ext in ['.html', '.htm']:
                tag_match = re.search(r'^\s*<([a-zA-Z0-9\-]+)(?:[^>]*)id=["\']([^"\']+)["\']', line)
                if tag_match:
                    symbols.append({'name': "<{0}> #{1}".format(tag_match.group(1), tag_match.group(2)), 'line': line_num, 'indent': 0, 'type': 'class'})
                    continue
            
            elif ext in ['.css', '.scss', '.less']:
                rule_match = re.search(r'^\s*([\.#a-zA-Z0-9\-_:,\s]+)\s*\{', line)
                if rule_match:
                    symbols.append({'name': rule_match.group(1).strip(), 'line': line_num, 'indent': 0, 'type': 'function'})
                    continue
            
            elif ext in ['.md', '.markdown']:
                md_match = re.search(r'^(#{1,6})\s+(.*)', line)
                if md_match:
                    level = len(md_match.group(1)) - 1
                    symbols.append({'name': md_match.group(2).strip(), 'line': line_num, 'indent': level, 'type': 'class'})
                    continue
            
            elif ext in ['.yaml', '.yml']:
                yaml_match = re.match(r'^(\s*)([a-zA-Z0-9_\-]+)\s*:', line)
                if yaml_match:
                    indent_str = yaml_match.group(1)
                    indent = len(indent_str) // 2
                    name = yaml_match.group(2)
                    symbols.append({'name': name, 'line': line_num, 'indent': indent, 'type': 'yaml'})
                    continue
                    
            elif ext in ['.usd', '.usda']:
                usd_match = re.match(r'^(\s*)(def|class|over)\s+([^{]+)', line)
                if usd_match:
                    indent_str = usd_match.group(1)
                    indent = len(indent_str) // 4
                    keyword = usd_match.group(2)
                    decl = usd_match.group(3).strip()
                    symbols.append({'name': "{0} {1}".format(keyword, decl), 'line': line_num, 'indent': indent, 'type': 'usd'})
                    continue

            elif ext == '.json':
                json_match = re.match(r'^(\s*)"([^"\\]*(?:\\.[^"\\]*)*)"\s*:', line)
                if json_match:
                    indent_str = json_match.group(1)
                    indent = len(indent_str) // 2
                    name = json_match.group(2)
                    symbols.append({'name': name, 'line': line_num, 'indent': indent, 'type': 'json'})
                    continue

        return symbols
