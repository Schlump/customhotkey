from customhotkey import hotkey

dir(hotkey)
def test_fzf():

    fzf = hotkey.Fzf()
    assert hasattr(fzf, '_fzf_version')
