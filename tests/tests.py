import sys
sys.path.append('../')
from customhotkey import Fzf


def test_fzf():

    fzf = Fzf()
    assert hasattr(fzf, '_fzf_version')