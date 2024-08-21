import pytest
from pygments.token import Token
from shellconsole_lexer import ShellConsoleLexer
from git_lexer import GitStatusLexer

def test_full_git_status():
    lexer = ShellConsoleLexer()
    text = (
        "user@host:~/directory (main) $ git status\n"
        "On branch main\n"
        "\n"
        "No commits yet\n"
        "\n"
        "Untracked files:\n"
        "  (use \"git add <file>...\" to include in what will be committed)\n"
        "        README.md\n"
        "\n"
        "Changes not staged for commit:\n"
        "  (use \"git add <file>...\" to update what will be committed)\n"
        "  (use \"git restore <file>...\" to discard changes in working directory)\n"
        "        deleted:    README.md\n"
        "        modified:   mkdocs.yml\n"
        "        modified:   requirements.txt\n"
        "\n"
        "Changes to be committed:\n"
        "  (use \"git rm --cached <file>...\" to unstage)\n"
        "        new file:   README.md\n"
)

    tokens = list(lexer.get_tokens(text))

    assert tokens == [
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
            (Token.Text, "status"),
            (Token.Text.Whitespace, "\n"),
            (Token.Generic.Output, "On branch main\n"),
            (Token.Text.Whitespace, "\n"),
            (Token.Generic.Output, "No commits yet\n"),
            (Token.Text.Whitespace, "\n"),
            (Token.Generic.Output, "Untracked files:\n"),
            (Token.Generic.Output, "  (use \"git add <file>...\" to include in what will be committed)\n"),
            (Token.Text.Whitespace, "        "),
            (Token.Git.Untracked, "README.md"),
            (Token.Text.Whitespace, "\n"),
            (Token.Text.Whitespace, "\n"),
            (Token.Generic.Output, "Changes not staged for commit:\n"),
            (Token.Generic.Output, "  (use \"git add <file>...\" to update what will be committed)\n"),
            (Token.Generic.Output, "  (use \"git restore <file>...\" to discard changes in working directory)\n"),
            (Token.Text.Whitespace, "        "),
            (Token.Git.Modified, "deleted:    README.md"),
            (Token.Text.Whitespace, "\n"),
            (Token.Text.Whitespace, "        "),
            (Token.Git.Modified, "modified:   mkdocs.yml"),
            (Token.Text.Whitespace, "\n"),
            (Token.Text.Whitespace, "        "),
            (Token.Git.Modified, "modified:   requirements.txt"),
            (Token.Text.Whitespace, "\n"),
            (Token.Text.Whitespace, "\n"),
            (Token.Generic.Output, "Changes to be committed:\n"),
            (Token.Generic.Output, "  (use \"git rm --cached <file>...\" to unstage)\n"),
            (Token.Text.Whitespace, "        "),
            (Token.Git.Staged, "new file:   README.md"),
            (Token.Text.Whitespace, "\n"),
    ]
