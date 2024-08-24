import pytest
from pygments.token import Token
from shellconsole_lexer import ShellConsoleLexer
from git_lexer import GitStatusLexer

def test_git_command_whit_hint():
    lexer = ShellConsoleLexer()
    text = (
        "user@host:~/directory (main) $ git branch -d desc\n"
        "error: the branch 'desc' is not fully merged.\n"
        "hint: If you are sure you want to delete it, run 'git branch -D desc'.\n"
        "hint: Disable this message with \"git config advice.forceDeleteBranch false\".\n"
    )

    tokens = list(lexer.get_tokens(text))

    assert tokens == [
        # Prompt
        (Token.Generic.Prompt.UserHost, "user@host"),
        (Token.Generic.Prompt, ":"),
        (Token.Generic.Prompt.Directory, "~/directory"),
        (Token.Text.Whitespace, " "),
        (Token.Generic.Prompt.GitBranch, "(main)"),
        (Token.Text.Whitespace, " "),
        (Token.Generic.Prompt, "$"),
        (Token.Text.Whitespace, " "),
        (Token.Text, "git"),
        (Token.Text.Whitespace, " "),
        (Token.Text, "branch"),
        (Token.Text.Whitespace, " "),
        (Token.Text, "-d"),
        (Token.Text.Whitespace, " "),
        (Token.Text, "desc"),
        (Token.Text.Whitespace, "\n"),
        # Output
        (Token.Generic.Output, "error: the branch 'desc' is not fully merged.\n"),
        (Token.Git.Hint, "hint: If you are sure you want to delete it, run 'git branch -D desc'.\n"),
        (Token.Git.Hint, "hint: Disable this message with \"git config advice.forceDeleteBranch false\".\n"),
    ]
