from PyQt5                     import QtGui, QtWidgets
from bscripts.tricks           import tech as t
from script_pack.preset_colors import *
import os

class GOD:
    def __init__(self,
                 place=None,
                 main=None,
                 type=None,
                 signal=False,
                 reset=True,
                 parent=None,
                 *args, **kwargs
                 ):

        self.activated = False
        self.main = main or False
        self.parent = parent or place or False
        self.determine_type(place, type)
        self.setup_signal(signal, reset)

    def setup_signal(self, signal, reset):
        if signal:
            if signal == True:
                self.signal = t.signals(self.type, reset=reset)
            else:
                self.signal = t.signals(signal, reset=reset)
        else:
            self.signal = False

    def determine_type(self, place, type):
        if type:
            self.type = type
        elif place and 'type' in dir(place) and place.type not in ['main']: # blacklist
            self.type = place.type
        else:
            self.type = '_' + t.md5_hash_string()

    def save(self, type=None, data=None):
        if data:
            if type:
                t.save_config(type, data)
            else:
                t.save_config(self.type, data)

    def activation_toggle(self, force=None, save=True):
        if force == False:
            self.activated = False
        elif force == True:
            self.activated = True
        else:
            if self.activated:
                self.activated = False
            else:
                self.activated = True

        if save:
            t.save_config(self.type, self.activated)

class DragDroper(GOD):
    def __init__(self, drops=False, mouse=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(drops)
        self.setMouseTracking(mouse)

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent) -> None:
        if a0.mimeData().hasUrls() and a0.mimeData().urls() and len(a0.mimeData().urls()) == 1:
            file = a0.mimeData().urls()[0]
            file = file.path()
            if os.path.isfile(file):
                splitter = file.split('.')
                if splitter[-1].lower() in {'xci', 'zip', 'rar', 'jpg', 'jpeg', 'webp', 'png', 'bmp', 'keys', 'nsp'}:
                    a0.accept()
        return

    def dropEvent(self, a0: QtGui.QDropEvent) -> None:
        if a0.mimeData().hasUrls() and a0.mimeData().urls()[0].isLocalFile():

            if len(a0.mimeData().urls()) == 1:
                a0.accept()

                files = [x.path() for x in a0.mimeData().urls()]
                self.filesdropped(files)

class GODLabel(QtWidgets.QLabel, GOD):
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs['place'], *args, **kwargs)
        self.show()

    def filesdropped(self, files):
        pass

class GODLE(QtWidgets.QLineEdit, GOD):
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs['place'], *args, **kwargs)
        self.textChanged.connect(self.text_changed)
        self.show()

    def text_changed(self):
        text = self.text().strip()
        if not text:
            return

class GODLEPath(GODLE):
    def __init__(self, autoinit=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if autoinit:
            self.set_saved_path()

    def filesdropped(self, files):
        if not files:
            return

        self.setText(files[0])

    def text_changed(self):
        text = self.text().strip()

        if text and os.path.exists(text):
            self.save(data=text)
            if not self.activated:
                t.style(self, color='white')
                self.activation_toggle(force=True, save=False) # already saved
                if self.signal:
                    self.signal.activated.emit()
        else:
            if self.activated:
                t.style(self, color='gray')
                self.activation_toggle(force=False, save=False)
                if self.signal:
                    self.signal.deactivated.emit()

    def set_saved_path(self):
        rv = t.config(self.type)
        if rv:
            self.setText(rv)
            self.activation_toggle(force=True, save=False)
            self.signal.activated.emit()

class GLOBALHighLight(DragDroper, GOD):
    def __init__(self,
                 signal=True,
                 reset=False,
                 activated_on=None,
                 activated_off=None,
                 deactivated_on=None,
                 deactivated_off=None,
                 *args, **kwargs
                 ):

        if signal == True:
            signal = '_global'

        super().__init__(signal=signal, reset=reset, *args, **kwargs)
        self.signal.highlight.connect(self.highlight_toggle)

        self.activated_on = activated_on or dict(background=HIGH_GREEN)
        self.activated_off = activated_off or dict(background=ACTIVE_GREEN)
        self.deactivated_on = deactivated_on or dict(background=HIGH_RED)
        self.deactivated_off = deactivated_off or dict(background=DEACTIVE_RED)

    def swap_preset(self, variable, new_value=None, restore=False):
        if not getattr(self, variable):
            return

        if 'swap_presets_backup' not in dir(self):
            self.swap_presets_backup = {}

        if variable not in self.swap_presets_backup: # makes a backup
            self.swap_presets_backup[variable] = getattr(self, variable)

        if new_value and new_value != getattr(self, variable):
            setattr(self, variable, new_value)

        if restore and getattr(self, variable) != self.swap_presets_backup[variable]:
            setattr(self, variable, self.swap_presets_backup[variable])

    def highlight_toggle(self, string=None, force=None):
        if force:
            string = self.type
        elif force == False:
            string = '_' + t.md5_hash_string()

        if string == self.type:
            if self.activated:
                t.style(self, **self.activated_on)
            else:
                t.style(self, **self.deactivated_on)
        else:
            if self.activated:
                t.style(self, **self.activated_off)
            else:
                t.style(self, **self.deactivated_off)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.signal.highlight.emit(self.type)
