import ast
import re


class OutlineParser:
    @staticmethod
    def parse(code, ext='.py', tree=None):
        if ext == '.py':
            try:
                if tree is None:
                    tree = ast.parse(code)
                symbols = OutlineParser._parse_ast(tree)
                if symbols:
                    return symbols
                return OutlineParser._parse_regex(code, ext)
            except Exception:
                return OutlineParser._parse_regex(code, ext)
        else:
            return OutlineParser._parse_regex(code, ext)

    @staticmethod
    def _parse_ast(tree):
        def _process_body(body_nodes, parent_type=None):
            node_symbols = []
            for node in body_nodes:
                if isinstance(node, ast.ClassDef):
                    class_item = {
                        'name': "class {0}".format(node.name),
                        'raw_name': node.name,
                        'line': node.lineno,
                        'indent': getattr(node, 'col_offset', 0) // 4,
                        'type': 'class',
                        'children': _process_body(node.body, parent_type='class')
                    }
                    node_symbols.append(class_item)

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                    is_method = (parent_type == 'class')
                    sym_type = 'method' if is_method else 'function'
                    func_item = {
                        'name': "{0} {1}()".format(prefix, node.name),
                        'raw_name': node.name,
                        'line': node.lineno,
                        'indent': getattr(node, 'col_offset', 0) // 4,
                        'type': sym_type,
                        'children': _process_body(node.body, parent_type=sym_type)
                    }
                    node_symbols.append(func_item)

                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        var_name = OutlineParser._get_target_name(target)
                        if var_name:
                            is_const = var_name.isupper() and len(var_name) > 1
                            sym_type = 'constant' if is_const else 'variable'
                            node_symbols.append({
                                'name': "{0} =".format(var_name),
                                'raw_name': var_name,
                                'line': node.lineno,
                                'indent': getattr(node, 'col_offset', 0) // 4,
                                'type': sym_type,
                                'children': []
                            })

                elif isinstance(node, ast.AnnAssign):
                    var_name = OutlineParser._get_target_name(node.target)
                    if var_name:
                        is_const = var_name.isupper() and len(var_name) > 1
                        sym_type = 'constant' if is_const else 'variable'
                        node_symbols.append({
                            'name': "{0} :".format(var_name),
                            'raw_name': var_name,
                            'line': node.lineno,
                            'indent': getattr(node, 'col_offset', 0) // 4,
                            'type': sym_type,
                            'children': []
                        })

            return node_symbols

        symbols = _process_body(tree.body, parent_type=None)
        symbols.sort(key=lambda x: x['line'])
        return symbols

    @staticmethod
    def _get_target_name(target):
        if isinstance(target, ast.Name):
            name = target.id
            if name.startswith('__') and name.endswith('__') and name not in ['__all__', '__version__', '__author__']:
                return None
            return name
        return None

    @staticmethod
    def flatten_symbols(symbols):
        """
        Recursively flattens a tree of symbols into a list sorted by line number.
        """
        flat = []
        for sym in symbols:
            # Create a copy without 'children' key for flat representations
            sym_copy = dict(sym)
            children = sym_copy.pop('children', [])
            flat.append(sym_copy)
            if children:
                flat.extend(OutlineParser.flatten_symbols(children))
        return flat

    @staticmethod
    def build_tree_from_indent(flat_symbols):
        """
        Converts a list of flat symbols with 'indent' attributes into a nested tree structure.
        """
        if not flat_symbols:
            return []

        root_symbols = []
        stack = []  # tuple of (indent_level, symbol_dict)

        for sym in flat_symbols:
            sym_item = dict(sym)
            sym_item['children'] = []
            indent = sym_item.get('indent', 0)

            while stack and stack[-1][0] >= indent:
                stack.pop()

            if stack:
                stack[-1][1]['children'].append(sym_item)
            else:
                root_symbols.append(sym_item)

            stack.append((indent, sym_item))

        return root_symbols

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
                    symbols.append({'name': "class {0}".format(name), 'raw_name': name, 'line': line_num, 'indent': indent, 'type': 'class'})
                    continue
                def_match = re.match(r'^(\s*)(?:async\s+)?def\s+(\w+)', line)
                if def_match:
                    indent = len(def_match.group(1)) // 4
                    name = def_match.group(2)
                    sym_type = 'method' if indent > 0 else 'function'
                    symbols.append({'name': "def {0}()".format(name), 'raw_name': name, 'line': line_num, 'indent': indent, 'type': sym_type})
                    continue
                var_match = re.match(r'^([A-Z_][A-Z0-9_]+)\s*=', line)
                if var_match:
                    name = var_match.group(1)
                    symbols.append({'name': "{0} =".format(name), 'raw_name': name, 'line': line_num, 'indent': 0, 'type': 'constant'})
                    continue

            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                class_match = re.search(r'^(\s*)class\s+(\w+)', line)
                if class_match:
                    symbols.append({'name': "class {0}".format(class_match.group(2)), 'raw_name': class_match.group(2), 'line': line_num, 'indent': len(class_match.group(1)) // 4, 'type': 'class'})
                    continue
                func_match = re.search(r'^(\s*)(?:async\s+)?function\s+(\w+)', line)
                if func_match:
                    symbols.append({'name': "function {0}()".format(func_match.group(2)), 'raw_name': func_match.group(2), 'line': line_num, 'indent': len(func_match.group(1)) // 4, 'type': 'function'})
                    continue
                arrow_match = re.search(r'^(\s*)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>', line)
                if arrow_match:
                    symbols.append({'name': "{0}()".format(arrow_match.group(2)), 'raw_name': arrow_match.group(2), 'line': line_num, 'indent': len(arrow_match.group(1)) // 4, 'type': 'function'})
                    continue

            elif ext in ['.cpp', '.c', '.h', '.hpp', '.vex']:
                class_match = re.search(r'^(\s*)(?:class|struct)\s+(\w+)', line)
                if class_match:
                    symbols.append({'name': "{0} {1}".format("class" if "class" in line else "struct", class_match.group(2)), 'raw_name': class_match.group(2), 'line': line_num, 'indent': len(class_match.group(1)) // 4, 'type': 'class'})
                    continue
                func_match = re.search(r'^(\s*)[\w\:]+\s+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{', line)
                if func_match:
                    name = func_match.group(2)
                    if name not in ['if', 'while', 'for', 'switch', 'catch']:
                        symbols.append({'name': "{0}()".format(name), 'raw_name': name, 'line': line_num, 'indent': len(func_match.group(1)) // 4, 'type': 'function'})
                    continue

            elif ext == '.mel':
                proc_match = re.search(r'^(\s*)(?:global\s+)?proc\s+(?:[\w\[\]]+\s+)?(\w+)\s*\(', line)
                if proc_match:
                    symbols.append({'name': "proc {0}()".format(proc_match.group(2)), 'raw_name': proc_match.group(2), 'line': line_num, 'indent': len(proc_match.group(1)) // 4, 'type': 'function'})
                    continue

            elif ext in ['.html', '.htm']:
                tag_match = re.search(r'^\s*<([a-zA-Z0-9\-]+)(?:[^>]*)id=["\']([^"\']+)["\']', line)
                if tag_match:
                    symbols.append({'name': "<{0}> #{1}".format(tag_match.group(1), tag_match.group(2)), 'raw_name': tag_match.group(2), 'line': line_num, 'indent': 0, 'type': 'class'})
                    continue

            elif ext in ['.css', '.scss', '.less']:
                rule_match = re.search(r'^\s*([\.#a-zA-Z0-9\-_:,\s]+)\s*\{', line)
                if rule_match:
                    name = rule_match.group(1).strip()
                    symbols.append({'name': name, 'raw_name': name, 'line': line_num, 'indent': 0, 'type': 'function'})
                    continue

            elif ext in ['.md', '.markdown']:
                md_match = re.search(r'^(#{1,6})\s+(.*)', line)
                if md_match:
                    level = len(md_match.group(1)) - 1
                    name = md_match.group(2).strip()
                    symbols.append({'name': name, 'raw_name': name, 'line': line_num, 'indent': level, 'type': 'class'})
                    continue

            elif ext in ['.yaml', '.yml']:
                yaml_match = re.match(r'^(\s*)([a-zA-Z0-9_\-]+)\s*:', line)
                if yaml_match:
                    indent_str = yaml_match.group(1)
                    indent = len(indent_str) // 2
                    name = yaml_match.group(2)
                    symbols.append({'name': name, 'raw_name': name, 'line': line_num, 'indent': indent, 'type': 'yaml'})
                    continue

            elif ext in ['.usd', '.usda']:
                usd_match = re.match(r'^(\s*)(def|class|over)\s+([^{]+)', line)
                if usd_match:
                    indent_str = usd_match.group(1)
                    indent = len(indent_str) // 4
                    keyword = usd_match.group(2)
                    decl = usd_match.group(3).strip()
                    symbols.append({'name': "{0} {1}".format(keyword, decl), 'raw_name': decl, 'line': line_num, 'indent': indent, 'type': 'usd'})
                    continue

            elif ext == '.json':
                json_match = re.match(r'^(\s*)"([^"\\]*(?:\\.[^"\\]*)*)"\s*:', line)
                if json_match:
                    indent_str = json_match.group(1)
                    indent = len(indent_str) // 2
                    name = json_match.group(2)
                    symbols.append({'name': name, 'raw_name': name, 'line': line_num, 'indent': indent, 'type': 'json'})
                    continue

            elif ext == '.xml':
                tag_match = re.match(r'^(\s*)<([a-zA-Z0-9_\-\.:]+)', line)
                if tag_match:
                    indent_str = tag_match.group(1)
                    indent = len(indent_str) // 4
                    name = "<{0}>".format(tag_match.group(2))
                    symbols.append({'name': name, 'raw_name': tag_match.group(2), 'line': line_num, 'indent': indent, 'type': 'xml'})
                    continue

            elif ext == '.ini':
                section_match = re.match(r'^(\s*)\[([^\]]+)\]', line)
                if section_match:
                    indent_str = section_match.group(1)
                    indent = len(indent_str) // 4
                    name = "[{0}]".format(section_match.group(2))
                    symbols.append({'name': name, 'raw_name': section_match.group(2), 'line': line_num, 'indent': indent, 'type': 'ini_section'})
                    continue
                key_match = re.match(r'^(\s*)([^=;#\[\]]+?)\s*=', line)
                if key_match:
                    indent_str = key_match.group(1)
                    indent = (len(indent_str) // 4) + 1
                    name = key_match.group(2).strip()
                    symbols.append({'name': name, 'raw_name': name, 'line': line_num, 'indent': indent, 'type': 'ini_key'})
                    continue

        return OutlineParser.build_tree_from_indent(symbols)


