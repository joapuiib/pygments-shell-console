"""Lexer for interactive shell sessions with highlighted prompts and output."""

import re

from pygments.lexer import Lexer, do_insertions, line_re
from pygments.lexers.diff import DiffLexer
from pygments.lexers.shell import BashLexer
from pygments.token import STANDARD_TYPES, Generic, Token

from .git import GitBranchLexer, GitLexer, GitLogLexer, GitMergeLexer, \
    GitPrettyLogLexer, GitShortStatusLexer, GitShowLexer, GitStatusLexer

__all__ = ['ShellConsoleLexer']

STANDARD_TYPES.update({
    Token.Generic.Prompt.Whitespace: 'gp-w',
    Token.Generic.Prompt.UserHost: 'gp-uh',
    Token.Generic.Prompt.Directory: 'gp-d',
    Token.Generic.Prompt.GitBranch: 'gp-gb',
    Token.Generic.Prompt.VirtualEnv: 'gp-ve',
})

# Git global options that take a separate value, e.g. `git -C repo status`.
_GIT_OPTIONS_WITH_VALUE = {'-C', '-c', '--git-dir', '--work-tree', '--namespace'}

# Unterminated here-document, e.g. `cat <<EOF` (but not `<<<` here-strings).
_HEREDOC_RE = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_]\w*)\1")

# Line ending in a pipe or a list operator, so bash keeps reading.
_TRAILING_OPERATOR_RE = re.compile(r'(?:\|\|?|&&)\s*\n\Z')


def _git_args(words):
    """Return the arguments after `git` and its global options."""
    args = words[1:]
    while args and args[0].startswith('-'):
        option = args.pop(0)
        if option in _GIT_OPTIONS_WITH_VALUE and args:
            args.pop(0)
    return args


def _output_lexer_class(command):
    """Choose the lexer for the output of `command`, or None for plain output."""
    words = command.split()
    if words and words[0] == 'sudo':
        words = words[1:]
    if not words:
        return None

    if words[0] in ('diff', 'colordiff'):
        return DiffLexer
    if words[0] == 'cat' and any(w.endswith(('.diff', '.patch')) for w in words):
        return DiffLexer
    if words[0] != 'git':
        return None

    args = _git_args(words)
    if not args:
        return GitLexer
    subcommand, options = args[0], args[1:]

    if subcommand == 'diff':
        return GitMergeLexer if '--stat' in options else DiffLexer
    if subcommand == 'show':
        return GitShowLexer
    if subcommand.startswith('lg') or (subcommand == 'log' and '--graph' in options):
        return GitPrettyLogLexer
    if subcommand == 'log':
        return GitLogLexer
    if subcommand == 'status':
        short = any(o in ('--short', '--porcelain') or re.fullmatch(r'-[a-z]*s[a-z]*', o)
                    for o in options)
        return GitShortStatusLexer if short else GitStatusLexer
    if subcommand == 'stash' and options:
        if options[0] in ('apply', 'pop'):
            return GitStatusLexer
        if options[0] == 'show':
            return DiffLexer if {'-p', '--patch'} & set(options) else GitMergeLexer
    if subcommand == 'branch':
        return GitBranchLexer
    if subcommand in ('merge', 'pull'):
        return GitMergeLexer
    return GitLexer


def _continues(code):
    """Whether bash would print PS2 and keep reading after `code`."""
    if code.endswith('\\\n') or _TRAILING_OPERATOR_RE.search(code):
        return True

    pending = []
    for line in code.splitlines():
        if pending:
            if line.strip() == pending[0]:
                pending.pop(0)
        else:
            pending.extend(m.group(2) for m in _HEREDOC_RE.finditer(line))
    return bool(pending)


class ShellConsoleLexer(Lexer):
    """
    Shell session where prompts are split into their parts (virtualenv,
    user@host, directory, git branch) and the output of known commands
    (diff, git) is highlighted.
    """

    name = 'Shell Console'
    aliases = ['shellconsole', 'shell-console']
    filenames = ['*.sh-session', '*.shell-session']
    mimetypes = ['application/x-shell-session', 'application/x-sh-session']
    url = 'https://en.wikipedia.org/wiki/Unix_shell'
    version_added = '1.0'

    _ps1_re = re.compile(r'''
        (?P<venv>\([^)]*\))?
        (?P<ws1>\s*)
        (?P<open>\[)?
        (?:
            (?P<user_host>[^\n$%\#]+@[^\s$%\#]+?)
            (?:(?P<ws2>\s*)(?P<colon>:)(?P<ws3>\s*)|(?P<ws4>\s+))
            (?P<current_dir>[^\s\]:$%\#]+)
        )?
        (?:(?P<ws5>\s+)(?P<git_branch>\([^)]+\)))?
        (?P<close>\])?
        (?P<ws6>\s*)
        # `#` (root) is only accepted after user@host, so comments aren't prompts.
        (?P<sigil>(?:[$%]|(?(user_host)\#|(?!)))\n?)
        (?P<ws7>\s*)
        (?P<command>.*\n?)
    ''', re.VERBOSE)

    _ps1_tokens = {
        'venv': Generic.Prompt.VirtualEnv,
        'user_host': Generic.Prompt.UserHost,
        'current_dir': Generic.Prompt.Directory,
        'git_branch': Generic.Prompt.GitBranch,
        'open': Generic.Prompt,
        'close': Generic.Prompt,
        'colon': Generic.Prompt,
        'sigil': Generic.Prompt,
    }

    _ps2 = '> '

    def get_tokens_unprocessed(self, text):
        innerlexer = BashLexer(**self.options)
        output_lexers = {}

        # Command being collected: start position, code and prompt insertions.
        command_pos = 0
        curcode = ''
        insertions = []
        # Output of the last command: start position, text and lexer class.
        output_pos = 0
        output = ''
        output_lexer_cls = None

        def flush_command():
            for i, t, v in do_insertions(
                    insertions, innerlexer.get_tokens_unprocessed(curcode)):
                yield command_pos + i, t, v

        def flush_output():
            if output_lexer_cls is None:
                yield output_pos, Generic.Output, output
                return
            if output_lexer_cls not in output_lexers:
                output_lexers[output_lexer_cls] = output_lexer_cls()
            lexer = output_lexers[output_lexer_cls]
            for i, t, v in lexer.get_tokens_unprocessed(output):
                yield output_pos + i, t, v

        for match in line_re.finditer(text):
            line = match.group()

            # Continuation of a multi-line command (backslash, heredoc...)
            if insertions and _continues(curcode):
                if line.startswith(self._ps2):
                    insertions.append((len(curcode),
                                       [(0, Generic.Prompt, self._ps2)]))
                    line = line[len(self._ps2):]
                curcode += line

            elif m := self._ps1_re.match(line):
                if output:
                    yield from flush_output()
                    output = ''

                command_pos = match.start()
                curcode = m.group('command')
                prompt = [
                    (0, self._ps1_tokens.get(name, Generic.Prompt.Whitespace), value)
                    for name, value in m.groupdict().items()
                    if value and name != 'command'
                ]
                insertions = [(0, prompt)]

            else:
                if not output:
                    output_pos = match.start()
                    output_lexer_cls = _output_lexer_class(curcode)
                output += line

            if insertions and not _continues(curcode):
                yield from flush_command()
                insertions = []

        if insertions:
            yield from flush_command()
        if output:
            yield from flush_output()
