from customhotkey import CustomHotkey
from customhotkey import Fzf


def test_fzf():
    fzf = Fzf()
    assert hasattr(fzf, '_fzf_version')