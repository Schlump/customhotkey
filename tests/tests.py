import sys
from customhotkey.hotkey import Fzf


def test_fzf():

    fzf = Fzf()
    assert hasattr(fzf, '_fzf_version')