import pytest
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from pygments_shell_console import ShellConsoleLexer

EXAMPLES = [
    "$ echo hi\nhi\nthere\n$ git status\nOn branch main\n",
    "user@host:~ $ git lg\n* f853946 - (7 minutes ago) msg - Mar (main)\n|/\n",
    "$ git show\ncommit abc\n\ndiff --git a/x b/x\n+b\n",
]


def tokens_of(text):
    return list(ShellConsoleLexer().get_tokens(text))


@pytest.mark.parametrize("text", EXAMPLES)
def test_token_positions_match_text(text):
    for pos, _, value in ShellConsoleLexer().get_tokens_unprocessed(text):
        assert text[pos:pos + len(value)] == value


def test_root_prompt():
    assert tokens_of("root@host:/etc# ls\n")[:5] == [
        (Token.Generic.Prompt.UserHost, "root@host"),
        (Token.Generic.Prompt, ":"),
        (Token.Generic.Prompt.Directory, "/etc"),
        (Token.Generic.Prompt, "#"),
        (Token.Generic.Prompt.Whitespace, " "),
    ]


def test_command_containing_diff_is_not_a_diff():
    assert tokens_of("$ cat diffusion.txt\n+hello\n")[-1] == \
        (Token.Generic.Output, "+hello\n")


def test_diff_command():
    assert (Token.Generic.Inserted, "+hello") in tokens_of("$ diff a b\n+hello\n")


def test_git_global_options():
    tokens = tokens_of("$ git -C repo branch\n* main\n")
    assert (Token.Git.Refs.Branch, "main") in tokens


def test_heredoc_continuation():
    tokens = tokens_of("$ cat <<EOF\n> $HOME\n> EOF\nout\n")
    assert tokens.count((Token.Generic.Prompt, "> ")) == 2
    assert tokens[-1] == (Token.Generic.Output, "out\n")


def test_pipe_continuation():
    tokens = tokens_of("$ ls |\n> wc -l\n3\n")
    assert (Token.Generic.Prompt, "> ") in tokens
    assert tokens[-1] == (Token.Generic.Output, "3\n")


def test_git_log_patch():
    tokens = tokens_of(
        "$ git log -p\n"
        "commit abc\n"
        "\n"
        "diff --git a/x b/x\n"
        "+b\n"
        "commit def\n"
    )
    assert (Token.Generic.Inserted, "+b") in tokens
    assert tokens[-2] == (Token.Git.Show.Header, "commit def")


def test_git_log_oneline():
    assert tokens_of("$ git log --oneline\nf853946 (HEAD -> main, origin/main) Msg\n")[-15:] == [
        (Token.Git.CommitHash, "f853946"),
        (Token.Text.Whitespace, " "),
        (Token.Git.Show.Header, "("),
        (Token.Git.Refs.Head, "HEAD"),
        (Token.Text.Whitespace, " "),
        (Token.Git.Show.Header, "->"),
        (Token.Text.Whitespace, " "),
        (Token.Git.Refs.Branch, "main"),
        (Token.Git.Show.Header, ","),
        (Token.Text.Whitespace, " "),
        (Token.Git.Refs.RemoteBranch, "origin/main"),
        (Token.Git.Show.Header, ")"),
        (Token.Text.Whitespace, " "),
        (Token.Git.CommitMessage, "Msg"),
        (Token.Text.Whitespace, "\n"),
    ]


def test_git_short_status():
    tokens = tokens_of(
        "$ git status -sb\n"
        "## main...origin/main [ahead 1]\n"
        "MM a.txt\n"
        "UU b.txt\n"
        "?? c.txt\n"
    )
    assert (Token.Git.Refs.Branch, "main") in tokens
    assert (Token.Git.Refs.RemoteBranch, "origin/main") in tokens
    assert (Token.Git.Staged, "M") in tokens
    assert (Token.Git.Modified, "M") in tokens
    assert (Token.Git.Unmerged, "UU") in tokens
    assert (Token.Git.Untracked, "??") in tokens


@pytest.mark.parametrize("alias", [
    "git", "git-status", "git-short-status", "git-log", "git-pretty-log",
    "git-show", "git-branch", "git-merge",
])
def test_git_lexers_are_registered(alias):
    get_lexer_by_name(alias)
