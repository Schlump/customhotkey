#!/usr/bin/python3
from evdev import InputDevice, categorize, ecodes
import argparse
import subprocess
import logging
import sys
import os
import pwd
import pathlib
import yaml
import time
import shlex


def exit(f):
    """[Decorator for handling Keyboard interrupts]

    Args:
        f ([type]): [description]
    """

    def wrapper(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
        except KeyboardInterrupt:
            sys.exit(0)
        return result

    return wrapper


class Fzf:
    def __init__(self, log_lvl="INFO"):
        logging.basicConfig(
            format="[%(asctime)s - %(levelname)s" + " - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_lvl.upper())
        self._check_available()

    def _check_available(self):
        """[Check if FZF is availabe]"""
        result = subprocess.run(
            ["fzf", "--version"], stdout=subprocess.PIPE, check=True
        )
        if result.returncode != 0:
            print("Please install fzf")
            print("https://github.com/junegunn/fzf#installation")
            self.logger.error("FZF not found")

        else:
            self._fzf_version = result.stdout.decode("utf-8").replace("\n", "")
            self.logger.debug(f"FZF version: {self._fzf_version}")

    @exit
    def prompt(self, _list: list, fzf_options: str = None) -> list:
        """[Generic function to call fzf with a list]

        Args:
            _list (list): [description]
            fzf_options (str, optional): [description]. Defaults to None.

        Returns:
            list: [description]
        """
        cmd = ["fzf"]
        if fzf_options:
            self.logger.debug(f"FZF options: {fzf_options}")
            cmd.extend([f"--{i}".strip() for i in fzf_options.split("--") if i])
        self.logger.debug(f"list: {_list}")
        _list = "\n".join(map(str, _list))
        self.logger.debug(f"list: {_list}")
        self.logger.debug(f"CMD: {cmd}")
        try:
            result = subprocess.check_output(cmd, input=_list, text=True)
            return [item for item in result.split("\n") if item]
        except subprocess.CalledProcessError as e:
            if e.returncode == 130:
                self.logger.debug("CTRL+C")
                self.logger.info("exited")
                sys.exit(0)
            else:
                print(e.output)
                self.logger.error(str(e))
                self.logger.error(str(e.output))


class CustomHotkey:

    def __init__(self):
        logging.basicConfig(
                stream=sys.stdout,
                format="%(asctime)s : %(message)s",
            )
        self.logger = logging.getLogger('CustomHotkey')
        self.logger.setLevel('DEBUG')
        self.init()
        self.input = pathlib.Path(f'/dev/input/by-id/{self.input}').resolve()
        self.device = f'{self.input}'

    def init(self):
        self._check_root()
        if self.root:
            for path in pathlib.Path('/home').iterdir():
                self.user = path.stem
                self.configdir = pathlib.Path(f'/home/{self.user}/.config/customhotkey')
                self.logger.debug(f'Configdir -> {self.configdir}')
                if pathlib.Path(self.configdir).exists():
                    #self.user_data = pwd.getpwnam(self.user)
                    self.read_config()
                    #self.source_env()
                    break

            else:
                self.logger.debug('No config for any user found...')

        else:
            self.logger.info('Script needs to run with superuser priviliges')
            sys.exit(1)
    
    def edit_config(self):
        """[Use systems default editor to open config file]"""
        editor = os.getenv("VISUAL")
        if not editor:
            editor = os.getenv("EDITOR")
        if not editor:
            editor = pathlib.Path("/usr/bin/editor").exists()
            if editor:
                editor = "/usr/bin/editor"
        if editor:
            subprocess.call(f"{editor} {self.configdir}/config.yaml", shell=True)

        if not editor:
            print("No editor found")

    def write_config(self, config):
        yaml.dump(config, f'{self.configdir}/config.yaml',
                          default_flow_style=False)

    # def source_env(self):
    #     command = shlex.split(f'sudo -Hiu {self.user} env')
        
    #     proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    #     for line in proc.stdout:
    #         foo = line.decode('utf-8').replace('\n', '').split('=')
    #         os.environ[foo[0]] = foo[1]


    def read_config(self):
        with open(str(self.configdir) + '/config.yaml', 'r') as stream:
            try:
                self.config = yaml.safe_load(stream)
                self.logger.debug(f'Config read: {self.config}')
                self.input = self.config['meta']['input']
                self.config = self.config['keys']
            except yaml.YAMLError as e:
                self.logger.info(e)

    # def generate_config(self):
    #     pass

    def add_command(self):
        print('Currently added commands:')
        for i, key in enumerate(self.config.keys(), 1):
            print(f'[i]: {key} -> {self.config[key]}')
        print(f'For which Key would you add a cmd? [1-{len(self.config.keys())}]')
        inp = int(input())
        key = self.config.keys()[inp]
        print(key)

    def detect_device(self):
        path = '/dev/input/by-id/usb-BlackC_Sayobot.cn_Sayobot_8K_00D158A069D7-event-kbd'
        try:
            os.stat(path)
        except OSError:
            return False
        return True

    def enter_loop(self):
        self.logger.debug('Entering infinite loop')
        try:
            self.dev = InputDevice(self.device)
            self.dev.grab()
        except OSError as e:
            self.logger.error(e)

        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY:
                cat = categorize(event)
                if cat.keystate == cat.key_down:
                    self.logger.debug(f'Key pressed: {cat.keycode}')
                    try:
                        cmd = self.config[cat.keycode]
                    except KeyError:
                        self.logger.debug(f'No cmd for {cat.keycode} found in config')
                        cmd = None
                        pass
                    if cmd:
                        self.logger.debug(f'Executing {cmd}')
                        subprocess.Popen(["/bin/bash", "-i", "-c", cmd])

    def _check_root(self):
        user = os.getenv("SUDO_USER")
        self.logger.debug(f'Sudo user: {user}')
        self.root = True
        if user:
            self.root = True
            self.user = user
        else:
            self.root = False
        if os.getuid() == 0:
            self.root = True
