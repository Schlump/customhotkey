from customhotkey import hotkey


def test_fzf():

    fzf = hotkey.Fzf()
    assert hasattr(fzf, '_fzf_version')
