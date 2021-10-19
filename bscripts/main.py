from PyQt5                        import QtCore, QtGui, QtWidgets
from bscripts.database_stuff      import sqlite
from bscripts.tricks              import tech as t
from script_pack.preset_colors    import *
from script_pack.settings_widgets import DragDroper, GLOBALHighLight, GODLEPath
from script_pack.settings_widgets import GODLabel
import os
import pathlib
import shutil
import subprocess
import sys


class NXCIGui(QtWidgets.QMainWindow):
    def __init__(self, primary_screen):
        super().__init__()
        self.show()

        if 'dev_mode' in sys.argv:
            sqlite.dev_mode = True

        self.primary_screen = primary_screen
        self.type = 'main'
        screen_width = primary_screen.size().width()
        screen_height = primary_screen.size().height()
        t.pos(self, width=screen_width * 0.3)
        t.style(self)
        self.move(screen_width * 0.1, screen_height * 0.1)
        self.setWindowTitle(os.environ['PROGRAM_NAME'])

        self.create_essentials()
        self.post_init()
        self.start_button()

        signal = t.signals('_global')
        signal.highlight.emit('-')

    def post_init(self):
        def file_size():
            text = self.input_path.lineedit.text().strip()
            if os.path.exists(text):
                return os.path.getsize(text)
            else:
                return False

        def tmp_size():
            text = self.work_folder.lineedit.text().strip()
            if os.path.exists(text):
                total, used, free = shutil.disk_usage(text)
                return free
            else:
                return False

        def free_size():
            text = self.output_folder.lineedit.text().strip()
            if os.path.exists(text):
                total, used, free = shutil.disk_usage(text)
                return free
            else:
                return False

        self.file_size = file_size
        self.tmp_size = tmp_size
        self.free_size = free_size

        text = self.output_folder.lineedit.text()
        if not text or not os.path.exists(text):
            self.output_folder.lineedit.setText(t.tmp_folder(folder_of_interest="OUTPUT"))

        text = self.work_folder.lineedit.text()
        if not text or not os.path.exists(text):
            self.work_folder.lineedit.setText(t.tmp_folder(folder_of_interest="TMP"))

        text = self.program_path.lineedit.text()
        if not text or not os.path.exists(text):
            loc = t.separate_file_from_folder('./4nxci')
            if os.path.exists(loc.full_path):
                self.program_path.lineedit.setText(loc.full_path)

        text = self.keyfile_path.lineedit.text()
        if not text or not os.path.exists(text):
            loc = t.separate_file_from_folder('./keys.txt')
            if os.path.exists(loc.full_path):
                self.keyfile_path.lineedit.setText(loc.full_path)

        self.keyfile_path.lineedit.textChanged.connect(self.start_button)
        self.program_path.lineedit.textChanged.connect(self.start_button)
        self.input_path.lineedit.textChanged.connect(self.start_button)
        self.work_folder.lineedit.textChanged.connect(self.start_button)
        self.output_folder.lineedit.textChanged.connect(self.start_button)

    def start_button(self):
        for i in [
            self.keyfile_path.button,
            self.program_path.button,
            self.input_path.button,
            self.work_folder.button,
            self.output_folder.button,
            ]:
            if not i.activated:

                if 'start_job_button' in dir(self):
                    self.start_job_button.activation_toggle(force=False)
                    self.start_job_button.highlight_toggle(force=False)

                return


        class STARTJob(GLOBALHighLight, GODLabel):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.activation_toggle(force=False)
                self.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)
                self.setText('CONVERT XCI to NSP')
                self.setFrameShape(QtWidgets.QFrame.Box)
                self.setLineWidth(1)

            def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
                if ev.button() != 1 or not self.activated:
                    return

                nxci = self.parent.program_path.lineedit.text().strip()
                xci = self.parent.input_path.lineedit.text().strip()
                keys = self.parent.keyfile_path.lineedit.text().strip()
                workfolder = self.parent.work_folder.lineedit.text().strip()
                workfolder += '/' + t.md5_hash_string()
                tmp_loc = t.separate_file_from_folder(workfolder)
                if not os.path.exists(tmp_loc.full_path):
                    pathlib.Path(tmp_loc.full_path).mkdir(parents=True)

                outputfolder = self.parent.output_folder.lineedit.text().strip()

                for walk in os.walk(outputfolder):
                    pre_files = [walk[0] + '/' + x for x in walk[2]]
                    self.activation_toggle(force=False)
                    subprocess.call(f'"{nxci}" -k "{keys}" -t "{workfolder}" -o "{outputfolder}" "{xci}" -r', shell=True)
                    self.activation_toggle(force=True)
                    for walk in os.walk(outputfolder):
                        post_files = [walk[0] + '/' + x for x in walk[2] if walk[0] + '/' + x not in pre_files]

                        if post_files and post_files[0] not in pre_files:
                            loc = t.separate_file_from_folder(post_files[0])
                            self.parent.output_path.lineedit.setText(loc.full_path)

                            break

                    self.signal.highlight.emit('_')
                    break

        if 'start_job_button' not in dir(self):
            self.start_job_button = STARTJob(
                place=self,
                mouse=True,
                activated_on=dict(background='lightGray'),
                activated_off=dict(background='darkGray'),
                deactivated_on=dict(background=HIGH_RED),
                deactivated_off=dict(background=DEACTIVE_RED),
            )

            t.pos(self.start_job_button,
                  coat=self.program_path, top=0, bottom=dict(top=self.program_path), y_margin=4)

            t.correct_broken_font_size(self.start_job_button)

        cycle = [
            dict(activated_on=dict(background='orange')),
            dict(activated_off=dict(background='brown')),
            dict(deactivated_on=dict(background='orange')),
            dict(deactivated_off=dict(background='brown')),
        ]
        signal = t.signals('_global')

        if self.free_size() + 100 < self.file_size() or self.tmp_size() + 100 < self.file_size():

            if self.free_size() + 100 < self.file_size():
                t.style(self.output_folder.free_size_label, color=HIGH_RED)
                for d in cycle:
                    for k,v in d.items():
                        self.output_folder.button.swap_preset(variable=k, new_value=v)

            if self.tmp_size() + 100 < self.file_size():
                t.style(self.work_folder.free_size_label, color=HIGH_RED)

                for d in cycle:
                    for k,v in d.items():
                        self.work_folder.button.swap_preset(variable=k, new_value=v)

            self.start_job_button.activation_toggle(force=False)
            signal.highlight.emit('_global')
            return

        else:
            for i in [self.work_folder.button, self.output_folder.button]:
                for d in cycle:
                    for k, _ in d.items():
                        i.swap_preset(variable=k, restore=True)

            t.style(self.output_folder.free_size_label, color='darkMagenta')
            t.style(self.work_folder.free_size_label, color='darkMagenta')

        self.start_job_button.activation_toggle(force=True)
        signal.highlight.emit('_global')

    def create_indikator_lineedit(self,
                                  place,
                                  edge=1,
                                  button=False,
                                  lineedit=False,
                                  tiplabel=None,
                                  height=30,
                                  width=300,
                                  tipfont=None,
                                  tipwidth=None,
                                  tooltip=None,
                                  button_listen=False,
                                  type=None,
                                  post_init_signal=True,
                                  *args, **kwargs
                                  ):

        class Canvas(GODLabel):
            def __init__(self, edge, width, height, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.edge = edge
                t.pos(self, size=[height, width])

            def build_lineedit(self, lineedit_background=None, lineedit_color=None, immutable=False, **kwargs):
                self.lineedit = self.LineEdit(place=self, main=self.main, parent=self, **kwargs)
                if immutable:
                    self.lineedit.setReadOnly(True)

                if lineedit_background:
                    t.style(self.lineedit, background=lineedit_background)
                if lineedit_color:
                    t.style(self.lineedit, color=lineedit_color)

            def build_button(self, **kwargs):
                self.button = self.Button(place=self, main=self.main, parent=self, **kwargs)

            def build_tiplabel(self, text, fontsize=None, width=None):
                if not 'lineedit' in dir(self):
                    return

                self.tiplabel = t.pos(new=self.lineedit, inside=self.lineedit)
                self.tiplabel.width_size = width
                self.tiplabel.setText(text)
                if fontsize:
                    t.style(self.tiplabel, font=fontsize)
                    self.tiplabel.font_size = fontsize
                else:
                    self.tiplabel.font_size = t.correct_broken_font_size(self.tiplabel)

                t.style(self.tiplabel, color=TIPTEXT, background='transparent')

            def button_and_lineedit_reactions(self):
                if not 'button' in dir(self) or not 'lineedit' in dir(self):
                    return

                if not self.lineedit.signal:
                    return

                self.lineedit.signal.activated.connect(lambda: t.style(self.button, background=ACTIVE_GREEN))
                self.lineedit.signal.activated.connect(lambda: t.style(self.button.activation_toggle(force=True, save=False)))
                self.lineedit.signal.deactivated.connect(lambda: t.style(self.button, background=DEACTIVE_RED))
                self.lineedit.signal.deactivated.connect(lambda: t.style(self.button.activation_toggle(force=False, save=False)))

            def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
                if self.width() < 100:
                    return

                self.set_positions()

            def set_positions(self):
                if 'button' in dir(self):
                    t.pos(self.button, height=self, width=self.height(), left=0, top=0)

                if 'lineedit' in dir(self):
                    if 'button' in dir(self):
                        t.pos(self.lineedit, after=self.button, x_margin=self.edge, height=self)
                        t.pos(self.lineedit, left=self.lineedit, right=self.width())
                    else:
                        t.pos(self.lineedit, inside=self)

                    if 'tiplabel' in dir(self):
                        if self.tiplabel.width_size:
                            t.pos(self.tiplabel, width=self.tiplabel.width_size)
                        t.pos(self.tiplabel, height=self.lineedit, right=self.lineedit.width(), x_margin=self.edge)

            class LineEdit(DragDroper, GODLEPath):
                def __init__(self,
                            activated_on=None,
                            activated_off=None,
                            deactivated_on=None,
                            deactivated_off=None
                            ,*args, **kwargs
                            ):
                    super().__init__(
                                     activated_on=activated_on or dict(color=TEXT_ON),
                                     activated_off=activated_off or dict(color=TEXT_WHITE),
                                     deactivated_on=deactivated_on or dict(color=TEXT_ON),
                                     deactivated_off=deactivated_off or dict(color=TEXT_OFF),
                                     *args, **kwargs)

                    t.style(self, background='white', color='black', font=14)

            class Button(GODLabel, GLOBALHighLight):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    t.style(self, background=DEACTIVE_RED, color='black')
                    self.setFrameShape(QtWidgets.QFrame.Box)
                    self.setLineWidth(self.parent.edge)

        canvas = Canvas(place=place, edge=edge, width=width, height=height, type=type, *args, **kwargs)

        if lineedit:
            canvas.build_lineedit(**kwargs)
        if button:
            canvas.build_button(**kwargs)
        if tiplabel:
            canvas.build_tiplabel(text=tiplabel, fontsize=tipfont, width=tipwidth)
        if button_listen:
            canvas.button_and_lineedit_reactions()
        if tooltip:
            canvas.setToolTip(tooltip)
            t.style(canvas, tooltip=True, background='black', color='white', font=14)

        if post_init_signal and lineedit and canvas.lineedit.activated:
            canvas.lineedit.signal.activated.emit()

        return canvas

    def create_essentials(self):
        def ShowSize(widget):
            text = widget.lineedit.text().strip()

            if not 'size_label' in dir(widget):
                widget.size_label = t.pos(new=widget, height=widget.lineedit, width=0, background='transparent')
                widget.size_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

            if not os.path.exists(text):
                widget.size_label.setText('...')
                return

            size = os.path.getsize(text)
            size = round(size / 1000000, 2)
            widget.size_label.setText(f"{size} MB")
            t.style(widget.size_label, font=widget.tiplabel.font_size, color='darkCyan')
            t.pos(widget.size_label, width=widget.tiplabel, before=widget.tiplabel)

        def FreeSize(widget):
            text = widget.lineedit.text().strip()

            if not 'free_size_label' in dir(widget):
                widget.free_size_label = t.pos(new=widget, height=widget.lineedit, width=0, background='transparent')
                widget.free_size_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

            if not os.path.exists(text):
                widget.free_size_label.setText('...')
                return

            total, used, free = shutil.disk_usage(text)
            free = round(free / 1000000000, 2)
            widget.free_size_label.setText(f"{free} GB FREE")

            t.style(widget.free_size_label, font=widget.tiplabel.font_size, color='darkMagenta')
            t.pos(widget.free_size_label, width=widget.tiplabel, before=widget.tiplabel)

        self.program_path = self.create_indikator_lineedit(
            place=self,
            edge=2,
            autoinit=True,
            lineedit=True,
            button=True,
            button_listen=True,
            lineedit_background='black', lineedit_color='white',
            tiplabel='PATH TO 4NXCI      ',
            type='4nxci_path',
            tooltip='executable 4NXCI file',
            mouse=True, signal=True, drops=True
        )

        t.pos(self.program_path, width=self, height=40, sub=8, move=[4, 44])
        tipfont = self.program_path.tiplabel.font_size
        coatsize = self.program_path

        self.keyfile_path = self.create_indikator_lineedit(
            place=self,
            edge=2,
            autoinit=True,
            lineedit=True,
            button=True,
            button_listen=True,
            lineedit_background='black', lineedit_color='white',
            tiplabel='PATH TO KEYFILE',
            type='keyfile_path',
            tipfont=tipfont,
            tooltip='usually keys.prod, but whatever...',
            mouse=True, signal=True, drops=True
        )
        t.pos(self.keyfile_path, coat=coatsize, below=self.program_path, y_margin=2)

        self.input_path = self.create_indikator_lineedit(
            place=self,
            edge=2,
            autoinit=True,
            lineedit=True,
            button=True,
            button_listen=True,
            lineedit_background='black', lineedit_color='white',
            tiplabel='XCI INPUT FILE',
            type='input_path',
            tipfont=tipfont,
            tooltip='something from a pirate',
            mouse=True, signal=True, drops=True
        )

        t.pos(self.input_path, coat=coatsize, below=self.keyfile_path, y_margin=2)

        self.work_folder = self.create_indikator_lineedit(
            place=self,
            edge=2,
            lineedit=True,
            button=True,
            button_listen=True,
            lineedit_background='black', lineedit_color='white',
            tiplabel='WORK FOLDER',
            type='work_folder',
            tipfont=tipfont,
            tooltip='not so plesent place...',
            mouse=True, signal=True, drops=True
        )

        t.pos(self.work_folder, coat=coatsize, below=self.input_path, y_margin=2)

        self.output_folder = self.create_indikator_lineedit(
            place=self,
            edge=2,
            lineedit=True,
            button=True,
            button_listen=True,
            lineedit_background='black', lineedit_color='white',
            tiplabel='OUTPUT FOLDER',
            type='output_folder',
            tipfont=tipfont,
            tooltip='in the bucket with the other fish...',
            mouse=True, signal=True, drops=True
        )

        t.pos(self.output_folder, coat=coatsize, below=self.work_folder, y_margin=2)


        self.output_path = self.create_indikator_lineedit(
            place=self,
            edge=2,
            lineedit=True,
            button=True,
            button_listen=True,
            immutable=True,
            activated_on=dict(color='yellow'),
            activated_off=dict(color='lightBlue'),
            lineedit_background='black', lineedit_color='white',
            tiplabel='FINAL DESTINATION',
            tipfont=tipfont,
            tooltip='final destination folder + filename (immutable)',
            mouse=True, signal=True, drops=True
        )

        t.pos(self.output_path, coat=coatsize, below=self.output_folder, y_margin=2)

        def init_size_labels(self):
            def each_label(self, i, ShowSize):
                basewidget = getattr(self, i)
                lineedit = getattr(basewidget, 'lineedit')
                lineedit.textChanged.connect(lambda: ShowSize(basewidget))
                ShowSize(basewidget)
            for i in ['program_path', 'output_path', 'input_path', 'keyfile_path']:
                each_label(self, i, ShowSize)
        init_size_labels(self)

        def init_free_space_labels(self):
            def each_label(self, i, FreeSize):
                basewidget = getattr(self, i)
                lineedit = getattr(basewidget, 'lineedit')
                lineedit.textChanged.connect(lambda: FreeSize(basewidget))
                FreeSize(basewidget)
            for i in ['work_folder', 'output_folder']:
                each_label(self, i, FreeSize)
        init_free_space_labels(self)


        self.setFixedSize(self.width(), self.output_path.geometry().bottom() + 4)
