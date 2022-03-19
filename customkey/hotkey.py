#!/usr/bin/python3
from evdev import InputDevice, categorize, ecodes
import evdev
import subprocess
import logging
import sys
import os
import pathlib
import yaml
import getpass


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
            self._fzf = False

        else:
            self._fzf = True
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
        self.__version__ = '0.1'
        self.logger.setLevel('DEBUG')
        self.user = getpass.getuser()
        self.configdir = pathlib.Path(f'/home/{self.user}/.config/customhotkey')
        self.init()
        self.input = pathlib.Path(f'/dev/input/by-id/{self.input}').resolve()
        self.device = f'{self.input}'

    def setup(self):
        devices = {evdev.InputDevice(path).name:
                   {'device': evdev.InputDevice(path)} for path in evdev.list_devices()}
        self.logger.info(f'Found {len(devices)}')
        selected = Fzf().prompt(devices)
        device = devices[selected[0]]['device']
        dev = evdev.InputDevice(device)
        detections = []
        try:
            print('Press each key on your Custom keyboard...')
            print('Hit CTRL + C when finished')
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY:
                    event = categorize(event)
                    if event.key_down == 1:
                        print(f'Key Pressed: {event.keycode}')
                    detections.append(event.keycode)
        except KeyboardInterrupt:
            print('Finished')
        detections = sorted(list(set(detections)))
        dump = {'meta':
                {'input': device.path}, 'keys': {key: "" for key in detections}
                }
        with open(str(self.configdir) + '/config.yaml', "w") as file:
            yaml.dump(dump, file)

    def init(self):
        self.logger.debug(f'Configdir -> {self.configdir}')
        if pathlib.Path(self.configdir).exists():
            self.read_config()
            return
        else:
            self.logger.debug('No config for any user found...')
            self.input = 'dummy'
            print('No config found, please run ck --init')

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

    def read_config(self):
        with open(str(self.configdir) + '/config.yaml', 'r') as stream:
            try:
                self.config = yaml.safe_load(stream)
                self.logger.debug(f'Config read: {self.config}')
                self.input = self.config['meta']['input']
                self.config = self.config['keys']
            except yaml.YAMLError as e:
                self.logger.info(e)

    def add_command(self):
        print('Currently added commands:')
        for i, key in enumerate(self.config.keys(), 1):
            print(f'[i]: {key} -> {self.config[key]}')
        print(f'For which Key would you add a cmd? [1-{len(self.config.keys())}]')
        inp = int(input())
        key = self.config.keys()[inp]
        print(key)

    def detect_device(self):
        try:
            os.stat(self.device)
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
