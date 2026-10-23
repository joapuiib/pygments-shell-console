"""Lexers for the output of git commands."""

import re

from pygments.lexer import Lexer, RegexLexer, bygroups, default, line_re, \
    using
from pygments.lexers.diff import DiffLexer
from pygments.token import STANDARD_TYPES, Comment, Generic, Token, Whitespace

__all__ = [
    'GitLexer',
    'GitStatusLexer',
    'GitShortStatusLexer',
    'GitLogLexer',
    'GitPrettyLogLexer',
    'GitShowLexer',
    'GitBranchLexer',
    'GitMergeLexer',
]

STANDARD_TYPES.update({
    Token.Git: 'git',
    Token.Git.BranchLine: 'git-bl',
    Token.Git.CommitHash: 'git-ch',
    Token.Git.CommitDate: 'git-cd',
    Token.Git.CommitMessage: 'git-cm',
    Token.Git.CommitAuthor: 'git-ca',
    Token.Git.Hint: 'git-hint',
    Token.Git.Warning: 'git-warning',
    Token.Git.Error: 'git-error',
    Token.Git.Fatal: 'git-fatal',
    Token.Git.Refs: 'git-r',
    Token.Git.Untracked: 'git-untr',
    Token.Git.Modified: 'git-mod',
    Token.Git.Unmerged: 'git-unm',
    Token.Git.Staged: 'git-stg',
    Token.Git.Show: 'git-show',
    Token.Git.Show.Header: 'git-show-h',
    Token.Git.Refs.RemoteHead: 'git-rh',
    Token.Git.Refs.Head: 'git-h',
    Token.Git.Refs.Tag: 'git-t',
    Token.Git.Refs.RemoteBranch: 'git-rb',
    Token.Git.Refs.Branch: 'git-b',
})

# Remote names recognised in ref decorations, e.g. "origin/main".
_REMOTES = r'(?:origin|upstream)'


class GitLexer(RegexLexer):
    """Generic git output: highlights error, fatal, hint and warning lines."""

    name = 'Git'
    aliases = ['git']
    filenames = ['*.git']
    version_added = '1.0'

    tokens = {
        'root': [
            (r'\n', Whitespace),
            (r'^error:.*\n', Token.Git.Error),
            (r'^fatal:.*\n', Token.Git.Fatal),
            (r'^hint:.*\n', Token.Git.Hint),
            (r'^warning:.*\n', Token.Git.Warning),
            (r'^.*\n', Generic.Output),
            (r'[^\n]+', Generic.Output),
        ],
    }


def _status_section(token):
    """Rules for a `git status` file list, colouring each entry with `token`."""
    return [
        (r'^\s*\n', Whitespace, '#pop'),
        (r'^\s+\(.*\)\n', Generic.Output),
        (r'^(\s*)([^\n]+)(\n)', bygroups(Whitespace, token, Whitespace)),
    ]


class GitStatusLexer(RegexLexer):
    """Output of `git status`."""

    name = 'Git Status'
    aliases = ['git-status']
    version_added = '1.0'

    tokens = {
        'root': [
            (r'^\n', Whitespace),
            (r'\s*Untracked files:\n', Generic.Output, 'untracked'),
            (r'\s*Changes not staged for commit:\n', Generic.Output, 'modified'),
            (r'\s*Changes to be committed:\n', Generic.Output, 'staged'),
            (r'\s*Unmerged paths:\n', Generic.Output, 'unmerged'),
            (r'^.*\n', using(GitLexer)),
        ],
        'untracked': _status_section(Token.Git.Untracked),
        'modified': _status_section(Token.Git.Modified),
        'staged': _status_section(Token.Git.Staged),
        'unmerged': _status_section(Token.Git.Unmerged),
    }


class GitShortStatusLexer(RegexLexer):
    """Output of `git status --short` / `--porcelain`."""

    name = 'Git Short Status'
    aliases = ['git-short-status']
    version_added = '1.0'

    tokens = {
        'root': [
            (r'^\n', Whitespace),
            (r'^(## )(No commits yet on )(\S+)(.*\n)', bygroups(
                Generic.Output, Generic.Output,
                Token.Git.Refs.Branch, Generic.Output,
            )),
            (r'^(## )(\S+?)(?:(\.\.\.)(\S+))?(\s.*\n|\n)', bygroups(
                Generic.Output, Token.Git.Refs.Branch,
                Generic.Output, Token.Git.Refs.RemoteBranch, Generic.Output,
            )),
            (r'^(\?\?)( )(.*)(\n)', bygroups(
                Token.Git.Untracked, Whitespace, Generic.Output, Whitespace,
            )),
            (r'^(DD|AU|UD|UA|DU|AA|UU)( )(.*)(\n)', bygroups(
                Token.Git.Unmerged, Whitespace, Generic.Output, Whitespace,
            )),
            (r'^([MTADRC ])([MTADRC ])( )(.*)(\n)', bygroups(
                Token.Git.Staged, Token.Git.Modified,
                Whitespace, Generic.Output, Whitespace,
            )),
            (r'^.*\n', using(GitLexer)),
        ],
    }


class GitLogLexer(RegexLexer):
    """Output of `git log`, including `--oneline` and `-p`."""

    name = 'Git Log'
    aliases = ['git-log']
    version_added = '1.0'

    tokens = {
        'root': [
            (r'^\n', Whitespace),
            (r'^commit [0-9a-f]+', Token.Git.Show.Header, 'header'),
            (r'^[0-9a-f]{7,40}(?= )', Token.Git.CommitHash, 'oneline'),
            (r'^diff .*\n', using(DiffLexer), 'diff'),
            (r'^.*\n', using(GitLexer)),
        ],
        'header': [
            (r' +', Whitespace),
            (r'\(', Token.Git.Show.Header, 'refs'),
            (r'\n', Whitespace, '#pop'),
        ],
        'oneline': [
            (r'( )(\()', bygroups(Whitespace, Token.Git.Show.Header), 'refs'),
            (r'( )(.*)(\n)', bygroups(
                Whitespace, Token.Git.CommitMessage, Whitespace,
            ), '#pop'),
            (r'\n', Whitespace, '#pop'),
        ],
        'refs': [
            (r' +', Whitespace),
            (r'->|,', Token.Git.Show.Header),
            (r'\)', Token.Git.Show.Header, '#pop'),
            (_REMOTES + r'/HEAD\b', Token.Git.Refs.RemoteHead),
            (r'HEAD\b', Token.Git.Refs.Head),
            (r'tag: [^\s,()]+', Token.Git.Refs.Tag),
            (_REMOTES + r'/[^\s,()]+', Token.Git.Refs.RemoteBranch),
            (r'[^\s,()]+', Token.Git.Refs.Branch),
        ],
        # Patch output (`git show`, `git log -p`) lasts until the next commit.
        'diff': [
            (r'^(?!commit [0-9a-f]+).*\n', using(DiffLexer)),
            default('#pop'),
        ],
    }


class GitShowLexer(GitLogLexer):
    """Output of `git show`. Same format as `git log -p`."""

    name = 'Git Show'
    aliases = ['git-show']


class GitPrettyLogLexer(Lexer):
    """Output of `git log --graph` using the format described in the README."""

    name = 'Git Pretty Log'
    aliases = ['git-pretty-log']
    version_added = '1.0'

    _branch_line = r'([\|\\\/ _]*)'
    _letters = r'0-9A-Za-zÀ-ÖØ-öø-ÿ'
    _log_re = re.compile(''.join([
        _branch_line,                           # 1. Branch line
        r'(\*)',                                # 2. Commit asterisk
        _branch_line,                           # 3. Branch line
        r'( +)',                                # 4. Space
        r'([a-f0-9]+)',                         # 5. Commit hash
        r'( +)',                                # 6. Space
        r'(-)',                                 # 7. Commit separator
        r'( +)',                                # 8. Space
        rf'(\([{_letters} ]+\))',               # 9. Date
        r'(\s+)',                               # 10. Space
        r'([^\n]+)',                            # 11. Commit message
        r'( +)',                                # 12. Space
        r'(-)',                                 # 13. Commit separator
        r'( +)',                                # 14. Space
        rf'([{_letters} ]*[{_letters}]+)',      # 15. Author
        r'( *)',                                # 16. Space
        r'(\([\w ->,:/.]+\))?',                 # 17. Refs
        r'( *)',                                # 18. Space
        r'(#[^\n]*)?',                          # 19. Comment
        r'\n',
    ]))
    _branch_line_re = re.compile(_branch_line + r'\n?$')

    _log_tokens = {
        1: Token.Git.BranchLine,
        3: Token.Git.BranchLine,
        4: Whitespace,
        5: Token.Git.CommitHash,
        6: Whitespace,
        8: Whitespace,
        9: Token.Git.CommitDate,
        10: Whitespace,
        11: Token.Git.CommitMessage,
        12: Whitespace,
        14: Whitespace,
        15: Token.Git.CommitAuthor,
        16: Whitespace,
        17: Token.Git.Refs,
        18: Whitespace,
        19: Comment,
    }

    def get_tokens_unprocessed(self, text):
        for match in line_re.finditer(text):
            line = match.group()
            start = match.start()

            match_log = self._log_re.match(line)
            if match_log:
                for i in range(1, self._log_re.groups + 1):
                    if match_log.group(i):
                        token = self._log_tokens.get(i, Generic.Output)
                        yield start + match_log.start(i), token, match_log.group(i)
                yield start + match_log.end() - 1, Whitespace, '\n'
            elif self._branch_line_re.match(line):
                yield start, Token.Git.BranchLine, line
            else:
                yield start, Generic.Output, line


class GitBranchLexer(RegexLexer):
    """Output of `git branch`: highlights the current branch."""

    name = 'Git Branch'
    aliases = ['git-branch']
    version_added = '1.0'

    tokens = {
        'root': [
            (r'^\n', Whitespace),
            (r'^(\* )(.*?)(\n)', bygroups(
                using(GitLexer), Token.Git.Refs.Branch, Whitespace,
            )),
            (r'^.*\n', using(GitLexer)),
        ],
    }


class GitMergeLexer(RegexLexer):
    """Diffstat output, as printed by `git merge`, `git pull`, `--stat`..."""

    name = 'Git Merge'
    aliases = ['git-merge', 'git-stat']
    version_added = '1.0'

    tokens = {
        'root': [
            (r'^\n', Whitespace),
            (r'^( \S+ +\| +\d+ )(\+*)(\-*)(\n)', bygroups(
                Generic.Output, Generic.Inserted, Generic.Deleted, Whitespace,
            )),
            (r'^.*\n', using(GitLexer)),
        ],
    }
