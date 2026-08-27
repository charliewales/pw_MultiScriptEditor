import sys
import traceback

from vendor.Qt.QtCore import QCoreApplication


class StdoutProxy:
    def __init__(self, write_func):
        self.write_func = write_func
        self.skip = False

    def write(self, text):
        if not self.skip:
            stripped_text = text.rstrip('\n')
            self.write_func(stripped_text)
            # Process events so UI doesn't freeze entirely if output is heavy
            QCoreApplication.processEvents()
        self.skip = not self.skip

    def flush(self):
        pass


class ExecutionManager:
    def __init__(self):
        # We can store execution context or state here
        pass

    def run_command(self, command, namespace, output_callback, close_callback):
        """
        Executes a python command within the given namespace.
        Output is redirected to output_callback.
        If a SystemExit is raised, close_callback is called.
        """
        if not command:
            return

        tmp_stdout = sys.stdout
        sys.stdout = StdoutProxy(output_callback)

        try:
            try:
                # Try evaluating first to see if it's an expression that returns a value
                result = eval(command, namespace, namespace)
                if result is not None:
                    output_callback(repr(result))
            except SyntaxError:
                # If it's a statement, exec it
                exec(command, namespace)
        except SystemExit:
            close_callback()
        except Exception:
            traceback_lines = traceback.format_exc().split('\n')
            # Remove eval/exec internal traceback lines for cleaner output
            try:
                for i in (3, 2, 1, -1):
                    traceback_lines.pop(i)
            except IndexError:
                pass
            output_callback('\n'.join(traceback_lines))
        finally:
            sys.stdout = tmp_stdout
