import sys
from customhotkey import hotkey as hk


def test_fzf():

    fzf = hk.Fzf()
    assert hasattr(fzf, '_fzf_version')