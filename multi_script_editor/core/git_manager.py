import os
import tempfile
import subprocess


class GitManager(object):
    """
    Provides Git repository integration via system `git` CLI executions.
    Designed to operate without third-party python dependencies.
    """

    @staticmethod
    def _get_subprocess_flags():
        """Get flags to hide console window on Windows platform."""
        flags = 0
        if os.name == 'nt':
            flags |= getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        return flags

    @classmethod
    def run_git_cmd(cls, args, cwd=None):
        """
        Executes a git command and returns (returncode, stdout, stderr).
        Preserves leading whitespace in stdout (essential for `git status --porcelain`).
        """
        try:
            cmd = ['git'] + args
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=cls._get_subprocess_flags()
            )
            stdout_bytes, stderr_bytes = proc.communicate()
            stdout = stdout_bytes.decode('utf-8', errors='replace').rstrip('\r\n')
            stderr = stderr_bytes.decode('utf-8', errors='replace').strip()
            return proc.returncode, stdout, stderr
        except Exception as e:
            return -1, '', str(e)

    @classmethod
    def is_git_available(cls):
        """Checks if git CLI executable is accessible."""
        code, _, _ = cls.run_git_cmd(['--version'])
        return code == 0

    @classmethod
    def get_repo_root(cls, file_path):
        """
        Returns absolute path of the root directory of the git repo containing file_path,
        or None if not inside a git repo.
        """
        if not file_path or not os.path.exists(file_path):
            return None
        folder = os.path.dirname(os.path.abspath(file_path))
        code, stdout, _ = cls.run_git_cmd(['rev-parse', '--show-toplevel'], cwd=folder)
        if code == 0 and stdout:
            return os.path.normpath(stdout.strip())
        return None

    @classmethod
    def is_in_repo(cls, file_path):
        """Returns True if file_path is inside a git repository."""
        return cls.get_repo_root(file_path) is not None

    @classmethod
    def get_branch(cls, file_path):
        """
        Returns current branch name or HEAD commit hash for file's repo.
        """
        folder = os.path.dirname(os.path.abspath(file_path)) if file_path else None
        if not folder or not os.path.exists(folder):
            return ''
        code, stdout, _ = cls.run_git_cmd(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=folder)
        if code == 0 and stdout:
            return stdout.strip()
        return ''

    @classmethod
    def get_file_status(cls, file_path):
        """
        Returns status dictionary for file_path:
        {
            'in_repo': bool,
            'repo_root': str,
            'branch': str,
            'status_code': str ('M', 'U', 'A', 'S', 'M+', 'CLEAN', etc.),
            'status_text': str,
            'is_modified': bool,
            'is_staged': bool,
            'is_untracked': bool,
            'relative_path': str
        }
        """
        result = {
            'in_repo': False,
            'repo_root': None,
            'branch': '',
            'status_code': 'CLEAN',
            'status_text': 'Clean',
            'is_modified': False,
            'is_staged': False,
            'is_untracked': False,
            'relative_path': ''
        }

        if not file_path:
            return result

        abs_path = os.path.abspath(file_path)
        repo_root = cls.get_repo_root(abs_path)
        if not repo_root:
            return result

        result['in_repo'] = True
        result['repo_root'] = repo_root
        result['branch'] = cls.get_branch(abs_path)

        try:
            rel_path = os.path.relpath(abs_path, repo_root)
            result['relative_path'] = rel_path
        except Exception:
            rel_path = os.path.basename(abs_path)
            result['relative_path'] = rel_path

        # Run git status --porcelain for specific file
        code, stdout, _ = cls.run_git_cmd(['status', '--porcelain', rel_path], cwd=repo_root)
        if code == 0 and stdout:
            # Porcelain format: XY FILENAME
            # X = index (staged) status, Y = work tree (unstaged) status
            line = stdout.splitlines()[0]
            if len(line) >= 2:
                x, y = line[0], line[1]
                if x == '?' and y == '?':
                    result['status_code'] = 'U'
                    result['status_text'] = 'Untracked'
                    result['is_untracked'] = True
                else:
                    if x in ('M', 'A', 'R', 'C', 'D'):
                        result['is_staged'] = True
                    if y in ('M', 'D'):
                        result['is_modified'] = True

                    if result['is_staged'] and result['is_modified']:
                        result['status_code'] = 'M+'
                        result['status_text'] = 'Staged & Modified'
                    elif result['is_staged']:
                        if x == 'A':
                            result['status_code'] = 'A'
                            result['status_text'] = 'Added (Staged)'
                        else:
                            result['status_code'] = 'S'
                            result['status_text'] = 'Staged'
                    elif result['is_modified']:
                        result['status_code'] = 'M'
                        result['status_text'] = 'Modified'
                    elif x == 'D' or y == 'D':
                        result['status_code'] = 'D'
                        result['status_text'] = 'Deleted'
        return result

    @classmethod
    def stage_file(cls, file_path):
        """Runs `git add <file_path>`."""
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return False, "Not in a Git repository."
        rel_path = os.path.relpath(file_path, repo_root)
        code, stdout, stderr = cls.run_git_cmd(['add', rel_path], cwd=repo_root)
        if code == 0:
            return True, "File staged successfully."
        return False, stderr or "Failed to stage file."

    @classmethod
    def unstage_file(cls, file_path):
        """Runs `git restore --staged <file_path>` or `git reset HEAD <file_path>`."""
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return False, "Not in a Git repository."
        rel_path = os.path.relpath(file_path, repo_root)
        code, stdout, stderr = cls.run_git_cmd(['restore', '--staged', rel_path], cwd=repo_root)
        if code != 0:
            # Fallback for older git versions
            code, stdout, stderr = cls.run_git_cmd(['reset', 'HEAD', rel_path], cwd=repo_root)
        if code == 0:
            return True, "File unstaged successfully."
        return False, stderr or "Failed to unstage file."

    @classmethod
    def discard_changes(cls, file_path):
        """Discards working tree modifications for file (`git checkout -- <file_path>`)."""
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return False, "Not in a Git repository."
        rel_path = os.path.relpath(file_path, repo_root)
        code, stdout, stderr = cls.run_git_cmd(['checkout', '--', rel_path], cwd=repo_root)
        if code != 0:
            code, stdout, stderr = cls.run_git_cmd(['restore', rel_path], cwd=repo_root)
        if code == 0:
            return True, "Discarded changes successfully."
        return False, stderr or "Failed to discard changes."

    @classmethod
    def commit_file(cls, file_path, message):
        """
        Commits file with the specified commit message.
        """
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return False, "Not in a Git repository."
        if not message or not message.strip():
            return False, "Commit message cannot be empty."

        rel_path = os.path.relpath(file_path, repo_root)
        # Ensure file is staged or commit directly
        cls.stage_file(file_path)
        code, stdout, stderr = cls.run_git_cmd(['commit', '-m', message.strip(), '--', rel_path], cwd=repo_root)
        if code == 0:
            return True, stdout or "Committed successfully."
        return False, stderr or stdout or "Failed to commit."

    @classmethod
    def get_file_diff(cls, file_path, staged=False):
        """Returns unified diff string for file against HEAD (or index if staged=True)."""
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return ''
        rel_path = os.path.relpath(file_path, repo_root)
        args = ['diff']
        if staged:
            args.append('--cached')
        else:
            args.append('HEAD')
        args.extend(['--', rel_path])
        code, stdout, _ = cls.run_git_cmd(args, cwd=repo_root)
        return stdout if code == 0 else ''

    @classmethod
    def get_head_file_temp_path(cls, file_path):
        """
        Writes the HEAD version of file_path to a temporary file and returns its temp file path.
        Useful for running external diff tools against HEAD version.
        """
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return None
        rel_path = os.path.relpath(file_path, repo_root)
        # git show HEAD:rel_path (converting Windows backslashes to forward slashes for git object path)
        git_rel_path = rel_path.replace('\\', '/')
        code, stdout, _ = cls.run_git_cmd(['show', f'HEAD:{git_rel_path}'], cwd=repo_root)
        if code != 0:
            return None

        basename = os.path.basename(file_path)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"HEAD_{basename}")
        with open(temp_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(stdout)
        return temp_path

    @classmethod
    def get_commit_file_temp_path(cls, file_path, commit_hash):
        """
        Writes the version of file_path at commit_hash to a temporary file and returns its temp file path.
        """
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return None
        rel_path = os.path.relpath(file_path, repo_root)
        git_rel_path = rel_path.replace('\\', '/')
        code, stdout, _ = cls.run_git_cmd(['show', f'{commit_hash}:{git_rel_path}'], cwd=repo_root)
        if code != 0:
            return None

        basename = os.path.basename(file_path)
        temp_dir = tempfile.gettempdir()
        short_hash = commit_hash[:7]
        temp_path = os.path.join(temp_dir, f"{short_hash}_{basename}")
        with open(temp_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(stdout)
        return temp_path

    @classmethod
    def get_file_history(cls, file_path, max_count=50):
        """
        Returns list of commit dicts touching file_path:
        [{'hash': str, 'short_hash': str, 'author': str, 'date': str, 'subject': str}]
        """
        history = []
        repo_root = cls.get_repo_root(file_path)
        if not repo_root:
            return history
        rel_path = os.path.relpath(file_path, repo_root)

        # Format: %H|%h|%an|%ad|%s (%ad with short date)
        fmt = '%H|%h|%an|%ad|%s'
        code, stdout, _ = cls.run_git_cmd(
            ['log', f'-n{max_count}', f'--pretty=format:{fmt}', '--date=short', '--', rel_path],
            cwd=repo_root
        )
        if code == 0 and stdout:
            for line in stdout.splitlines():
                parts = line.split('|', 4)
                if len(parts) == 5:
                    history.append({
                        'hash': parts[0],
                        'short_hash': parts[1],
                        'author': parts[2],
                        'date': parts[3],
                        'subject': parts[4]
                    })
        return history
