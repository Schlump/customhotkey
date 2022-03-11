from customkey.hotkey import CustomHotkey
from customkey.hotkey import Fzf
import sys
sys.path.append('.')


def test_fzf():

    fzf = Fzf()
    assert hasattr(fzf, '_fzf_version')


def test_class():
    ck = CustomHotkey()
    assert hasattr(ck, '__version__')