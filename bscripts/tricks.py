from PyQt5                   import QtWidgets
from PyQt5.Qt                import QObject
from PyQt5.QtCore            import pyqtSignal
from bscripts.database_stuff import DB, sqlite
import hashlib
import os
import pathlib
import pickle
import platform
import shutil
import tempfile
import time
import uuid

default_dict = dict(
    settings=dict(
    ),
    stylesheets=dict(
        main=dict(active=True, value='background-color: rgb(30,30,30) ; color: (200,200,250)')
    ),
    images=dict(
    ),
)

class DIRECTPOSITION:
    @staticmethod
    def digit(value):
        if type(value) == int or type(value) == float:
            return True

    @staticmethod
    def set_hw(widget, w, h):
        widget.resize(int(w), int(h))

    @staticmethod
    def set_geo(widget, x, y, w, h):
        widget.setGeometry(int(x), int(y), int(w), int(h))

    @staticmethod
    def extra(**kwargs):
        """
        ie: extra(dict(y_margin=kwgs))
        returns y_margin if such key are present
        :param kwargs: dictionary[key] = all_kwargs_from_parent
        :return: the value or 0
        """
        if not kwargs:
            return 0

        for master_key, slave_list in kwargs.items():

            for orders in slave_list:

                for k,v in orders.items():

                    if k == master_key:
                        return v

        return 0

    @staticmethod
    def width(widget, args, kwgs):

        if POS.digit(args):
            w = args
            h = widget.height()
        else:
            w = args.width()
            h = widget.height()

        POS.set_hw(widget, w + POS.extra(add=kwgs), h)

    @staticmethod
    def height(widget, args, kwgs):

        if POS.digit(args):
            w = widget.width()
            h = args
        else:
            w = widget.width()
            h = args.height()

        POS.set_hw(widget, w, h + POS.extra(add=kwgs))

    @staticmethod
    def size(widget, args, kwgs):
        """
        :param args: list/tuple with len(2) or widget
        """
        if type(args) == list or type(args) == tuple:
            w = args[0]
            h = args[1]

        else:
            w = args.width()
            h = args.height()

        POS.set_hw(widget, w + POS.extra(add=kwgs), h + POS.extra(add=kwgs))

    @staticmethod
    def inside(working_widget, parent, kwgs):
        """
        you can "coat" a widget that resides within its parent and
        using margins while doing so, but you cannot "coat" parent
        :param parent: must be a widget
        """
        margin = POS.extra(margin=kwgs)
        x, y = 0 + margin, 0 + margin
        w = parent.width() - margin * 2
        h = parent.height() - margin * 2
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def coat(working_widget, sister_widget, kwgs):
        """
        for two widgets that share the same parent you can coat one ontop
        the other to get their exact cordinates, this is very suitable.
        """
        margin = POS.extra(margin=kwgs)
        x = sister_widget.geometry().left() + margin
        y = sister_widget.geometry().top() + margin
        w = sister_widget.width() - margin * 2
        h = sister_widget.height() - margin * 2
        POS.set_geo(working_widget, x, y, w, h)

    @staticmethod
    def top(widget, args, kwgs):
        """
        read fn:left for same logic, basically if bottom is represented in kwgs its performed
        here as well meaning widget at will can stretch or shrink to reach bottom-destination
        """
        if not POS.digit(args):
            if type(args) == dict:
                if next(iter(args)) == 'top':
                    args = args['top'].geometry().top()
                else:
                    args = args['bottom'].geometry().bottom() + 1
            else:
                args = args.geometry().top()

        y_margin = POS.extra(y_margin=kwgs)

        x = widget.geometry().left()
        y = args + y_margin
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y ,w, h)

        bottom = POS.extra(bottom=kwgs)

        if bottom:

            if not POS.digit(bottom):

                if type(bottom) == dict:
                    if next(iter(bottom)) == 'bottom':
                        bottom = bottom['bottom'].geometry().bottom()
                    else:
                        bottom = bottom['top'].geometry().top() - 1
                else:
                    bottom = bottom.geometry().bottom()

            fill = bottom - widget.geometry().bottom() - y_margin
            POS.set_hw(widget, widget.width(), widget.height() + fill)

    @staticmethod
    def bottom(widget, args, kwgs):
        """ read fn:top """

        top = POS.extra(top=kwgs)

        if top: # rights task performed in fn:left
            return

        if not POS.digit(args):
            if type(args) == dict:
                if next(iter(args)) == 'bottom':
                    args = args['bottom'].geometry().bottom() + 1
                else:
                    args = args['top'].geometry().top()
            else:
                args = args.geometry().bottom() + 1

        y_margin = POS.extra(y_margin=kwgs)

        x = widget.geometry().left()
        y = args - widget.height() - y_margin
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y ,w, h)

    @staticmethod
    def left(widget, args, kwgs):
        """
        if argument is int moves widget to start from the argument pixel, if its an object
        then using that objects leftest pixel. if arguemnt is a dictionary(left=sister_widget)
        her's leftest pixel is used, however if dictionary(right=sister_widget) then it will
        be that rightest pixel plus one, assuming we want to start NEXT TO sisters widget.

        if right is somewhere within kwgs, right is dealt with within
        here and no changes will occur when it actually reaches fn:right

        x_margin simply moves the widget forward for that amount of pixels
        but if both left and right changes occurs simultaniously here, x_margin
        will actually shrink the finished position to honor both side margin-symetry

        :param args: int, dictionary or widget
        """
        if not POS.digit(args):

            if type(args) == dict:
                if next(iter(args)) == 'left':
                    args = args['left'].geometry().left() # assume left to left means sharing same pixel
                else:
                    args = args['right'].geometry().right() + 1 # assume left want to position NEXT to right position
            else:
                args = args.geometry().left()

        x_margin = POS.extra(x_margin=kwgs)

        x = args + x_margin
        y = widget.geometry().top()
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y, w, h)

        right = POS.extra(right=kwgs)

        if right:

            if not POS.digit(right):

                if type(right) == dict:
                    if next(iter(right)) == 'left':
                        right = right['left'].geometry().left() - 1 # assume right want to position BEFORE left position
                    else:
                        right = right['right'].geometry().right() # assume right to right means sharing same pixel
                else:
                    right = right.geometry().right()

            fill = right - widget.geometry().right() - x_margin
            POS.set_hw(widget, widget.width() + fill, widget.height())

    @staticmethod
    def right(widget, args, kwgs):
        """ read fn:left """
        left = POS.extra(left=kwgs)

        if left: # rights task performed in fn:left
            return

        if not POS.digit(args):

            if type(args) == dict:
                if next(iter(args)) == 'left':
                    args = args['left'].geometry().left() - 1  # assume right want to position BEFORE left position
                else:
                    args = args['right'].geometry().right()  # assume right to right means sharing same pixel
            else:
                args = args.geometry().right()

        x_margin = POS.extra(x_margin=kwgs)

        x = args - widget.width() + 1 - x_margin # because we count start (zero) as first pixel
        y = widget.geometry().top()
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y, w, h)

    @staticmethod
    def after(working_widget, preceeding_widget, kwgs):
        """
        position widget after preceeding_widget,
        y cordinates will be honored
        :param preceeding_widget: must be a widget
        """
        x_margin = POS.extra(x_margin=kwgs)
        x = preceeding_widget.geometry().right() + 1 + x_margin # because we count start (zero) as first pixel
        y = preceeding_widget.geometry().top()
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def before(working_widget, following_widget, kwgs):
        """
        position widget before following_widget,
        y cordinates will be honored
        :param preceeding_widget: must be a widget
        """
        x_margin = POS.extra(x_margin=kwgs)
        x = following_widget.geometry().left() - working_widget.width() - 1 - x_margin  # subtracting first pixel
        y = following_widget.geometry().top()
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def above(working_widget, widget_under, kwgs):
        """
        position widget above the widget under it, honoring x cordinates
        :param widget_above: must be a widget
        """
        y_margin = POS.extra(y_margin=kwgs)
        x = widget_under.geometry().left()
        y = widget_under.geometry().top() - working_widget.height() - y_margin
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def below(working_widget, widget_above, kwgs):
        """
        position widget below the widget above it, honoring x cordinates
        :param widget_above: must be a widget
        """
        y_margin = POS.extra(y_margin=kwgs)
        x = widget_above.geometry().left()
        y = widget_above.geometry().bottom() + 1 + y_margin # not sharing same pixel
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def under(*args):
        POS.below(*args)

    @staticmethod
    def center(widget, args, kwgs):
        pointa = args[0]
        pointb = args[1]

        if not POS.digit(pointa):
            if type(pointa) == dict:
                if next(iter(pointa)) == 'left':
                    pointa = pointa['left'].geometry().left()
                else:
                    pointa = pointa['right'].geometry().right()
            else:
                pointa = pointa.geometry().right()

        if not POS.digit(pointb):
            if type(pointb) == dict:
                if next(iter(pointb)) == 'left':
                    pointb = pointb['left'].geometry().left()
                else:
                    pointb = pointb['right'].geometry().right()
            else:
                pointb = pointb.geometry().left()

        rest = pointb - pointa - widget.width()
        rest = rest * 0.5

        x = pointa + rest
        y = widget.geometry().top()
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x,y,w,h)

    @staticmethod
    def between(widget, list_with_two_widgets, kwgs):
        """
        if third index == True or 'x' widget is inserted between 0 and 1 in the row
        if third index == False or 'y' widget is put between 0 and 1 stacked on top of each others
        :param list_with_two_widgets: object, object, string/bool (defaults to True, honoring x)
        """
        if list_with_two_widgets[-1] in {False, 'y'}:
            pointa = list_with_two_widgets[0].geometry().bottom() + 1 # else same pixel
            pointb = list_with_two_widgets[1].geometry().top()

            rest = (pointb - pointa) - widget.height()

            if rest > 1:
                x = widget.geometry().left()
                y = pointa + (rest * 0.5)
                POS.set_geo(widget, x, y, widget.width(), widget.height())

        else:
            pointa = list_with_two_widgets[0].geometry().right()
            pointb = list_with_two_widgets[1].geometry().left() + 1 # else same pixel

            rest = (pointb - pointa) - widget.width()

            if rest > 1:
                x = pointa + (rest * 0.5)
                y = widget.geometry().top()
                POS.set_geo(widget, x, y, widget.width(), widget.height())

    @staticmethod
    def move(widget, args, kwgs):
        """
        moving cordinates will be calculated from current position
        :param args: list or tuple
        """
        x = widget.geometry().left() + args[0]
        y = widget.geometry().top() + args[1]
        w = widget.width()
        h = widget.height()
        POS.set_geo(widget, x,y,w,h)

    @staticmethod
    def background(widget, args, kwgs):
        tech.style(widget, background=args)

    @staticmethod
    def color(widget, args, kwgs):
        tech.style(widget, color=args)

    @staticmethod
    def font(widget, args, kwgs):
        if POS.digit(args):
            args = str(args) + 'pt'
        tech.style(widget, font=args)

POS = DIRECTPOSITION()

class ViktorinoxTechClass:
    def __init__(self):
        self.techdict = {}

    @staticmethod
    def pos(widget=None, kwgs=None, new=False, **kwargs):
        def subraction_to_addition():
            """
            if 'sub' in kwargs it will make sub into add and makes sure the value
            is negative due human logic, yeah this can become buggy later on
            """
            if 'sub' in kwargs:
                if kwargs['sub'] > 0:
                    kwargs['add'] = -kwargs['sub']
                else:
                    kwargs['add'] = kwargs['sub']

        subraction_to_addition()

        if not kwgs:
            kwgs = [kwargs]

        if new:
            widget = QtWidgets.QLabel(new, lineWidth=0, midLineWidth=0)
            widget.show()

        for args in kwgs:
            for k, v in args.items():
                fn = getattr(POS, k, False)

                if not fn:
                    continue

                fn(widget, v, kwgs)

        return widget

    @staticmethod
    def separate_file_from_folder(local_path):
        """
        local_path can already be THIS object
        :param local_path must be full path including filename
        :return: object.string: full_path, db_folder, filename, naked_filename, sep (separator)
        """
        if type(local_path) != str:
            return local_path

        local_path = os.path.abspath(os.path.expanduser(local_path))

        class LOCATIONS:
            full_path = local_path
            subfolder = None
            parent = None

            if platform.system() != "Windows":
                sep = '/'
            else:
                sep = '\\'

            _tmp = local_path.split(sep)

            if os.path.isfile(full_path) or not os.path.exists(full_path):
                filename = _tmp[-1]
                _tmp.pop(-1)
                if _tmp:
                    subfolder = _tmp[-1]

                folder = sep.join(_tmp)

                _tmp = filename.split('.')

                if len(_tmp) > 1:
                    ext = _tmp[-1]
                    naked_filename = filename[0:-len(ext)-1]
                else:
                    ext = ""
                    naked_filename = filename

            else:
                folder = full_path
                subfolder = _tmp[-1]
                if len(_tmp) > 1:
                    parent = sep.join(_tmp[0:-1])


        return LOCATIONS

    @staticmethod
    def correct_broken_font_size(object, presize=True, maxsize=24, minsize=5, x_margin=10, y_margin=0, shorten=False):
        if presize:
            tech.style(object, font=str(maxsize) + 'pt')

        if shorten:
            for count in range(100):
                object.show()
                if object.fontMetrics().boundingRect(object.text()).width() + x_margin > object.width():
                    text = object.text()
                    object.setText(text[0:-3] + '..')
                else:
                    return

        for count in range(maxsize,minsize,-1):
            object.show()
            if object.fontMetrics().boundingRect(object.text()).width() + x_margin > object.width():
                tech.style(object, font=str(count) + 'pt')
            elif object.fontMetrics().boundingRect(object.text()).height() + y_margin > object.height():
                tech.style(object, font=str(count) + 'pt')
            else:
                return count + 1

    @staticmethod
    def style(widget, set=True, save=False, name=None, background=None, color=None, font=None, delete=False, border=None, tooltip=False):
        """
        if save is True, the set part wont happen
        if name is given, will request, save or set 'stylesheet_name'
        if name isnt given looks into widget.type and requests 'stylesheet_type'
        if any background,color,font thoes are set but not saved: background='green' font='8pt'
        :param widget: object
        :param set: bool
        :param save: bool
        :param name: string
        :return: bool or string.styleSheet()
        """
        if font: # lazy fix
            if type(font) == int or font.lower().find('pt') == -1:
                font = str(font) + 'pt'

        def make_stylesheet(widget):

            if widget.styleSheet() and widget.styleSheet().find('{') > -1: # meaning we've processed this before
                dictstyle = make_dictstylesheet(widget.styleSheet())
                return dictstyle

            elif widget.styleSheet(): # meaning it should only be one stylesheet
                if tooltip:
                    stylesheet = make_string_stylesheet([])
                    stylesheet = 'QToolTip{' + stylesheet + '}'
                    stylesheet += widget.metaObject().className() + '{' + widget.styleSheet() + '}'
                else:
                    stylelist = widget.styleSheet().split(';')
                    stylesheet = make_string_stylesheet(stylelist)
                    stylesheet = widget.metaObject().className() + '{' + stylesheet + '}'
            else:
                stylesheet = make_string_stylesheet([])
                if tooltip:
                    stylesheet = 'QToolTip{' + stylesheet + '}'
                else:
                    stylesheet = widget.metaObject().className() + '{' + stylesheet + '}'
            return stylesheet

        def make_dictstylesheet(old_stylesheet):
            stylesdict = {}
            parts = old_stylesheet.split('}')
            for part in parts:
                head_tail = part.split('{')

                head_tail = [x for x in head_tail if len(x) > 0]
                if not head_tail:
                    continue

                head = head_tail[0]
                head.strip()
                tail = head_tail[1]
                tail.strip()

                if tooltip and head != 'QToolTip': # no change to 'base' stylesheet
                    stylesdict[head] = '{' + tail + '}'

                elif not tooltip: # makes new as if nothing happened
                    stylelist = tail.split(';')
                    newtail = make_string_stylesheet(stylelist)
                    stylesdict[head] = '{' + newtail + '}'

            if tooltip and 'QToolTip' not in stylesdict:
                stylesdict['QToolTip'] = '{' + make_string_stylesheet([]) + '}'

            stylesheet = ""
            for k,v in stylesdict.items():
                stylesheet += k + v

            return stylesheet

        def make_string_stylesheet(stylelist):
            final = {
                'background-color:': background,
                'color:': color,
                'font:': font,
                'border:': border,
            }

            for i in stylelist:
                parts = i.split(':')
                parts = [x for x in parts if len(x) > 0]

                key = parts[0] + ':'.strip()
                value = parts[1].strip()

                if key in final and not final[key]:
                    final[key] = value

            rv = ""
            for k,v in final.items():
                if not v:
                    continue
                else:
                    rv += k + v + ';'

            return rv.rstrip(';')

        # <<======ABOVE:ME=======<{ [                TOP              ] ==============================<<
        # >>======================= [               FLOOR             ] }>============BELOW:ME========>>

        if not name:
            if 'type' in dir(widget) and type(widget.type) == str:
                name = widget.type

        if delete and name:
            tech.save_config(name, None, delete, stylesheet=True)

        elif save:
            stylesheet = widget.styleSheet()
            if not stylesheet:
                stylesheet = make_stylesheet(widget)

            if name and stylesheet:
                tech.save_config(name, stylesheet, stylesheet=True)
                return True
            else:
                return False
        elif set:
            if background or color or font:
                new = make_stylesheet(widget)
                widget.setStyleSheet(new)
                return new

            if name:
                stylesheet = tech.config(name, stylesheet=True)
                if stylesheet:
                    widget.setStyleSheet(stylesheet)
                    return stylesheet
                else:
                    return False

    @staticmethod
    def md5_hash_string(string=None, random=False, upper=False):
        if random or not string and not random:
            salt = 'how_much_is_the_fi2H'
            string = str(uuid.uuid4()) + str(time.time()) + salt + (string or "")

        hash_object = hashlib.md5(string.encode())
        rv = hash_object.hexdigest()

        if upper:
            rv = rv.upper()

        return rv

    def save_config(self, setting, value, delete=False, stylesheet=False, image=False, total_reset=False):
        """
        :param delete: pops the key before storing
        :param setting: string
        :param stylesheet: bool, if True point to dict['stylesheets'] else dict['settings']
        :param value: string, int, whatever fits a dictionary
        :return: value or False (instead of None)
        """
        if setting[0] == '_': # we dont save under/dunder types
            return False
        elif stylesheet:
            subkey = 'stylesheets'
        elif image:
            subkey = 'images'
        else:
            subkey = 'settings'

        tech.config('dummy') # activates self.techdict['config']
        theme = self.techdict['config']['current_theme']

        if setting in self.techdict['config'][theme][subkey]:
            savedict = self.techdict['config'][theme][subkey][setting]
        else:
            savedict = dict(active=True, value=None)

        if type(value) == bool:
            savedict['active'] = value
        else:
            savedict['value'] = value

        self.techdict['config'][theme][subkey][setting] = savedict

        if delete:
            self.techdict['config'][theme][subkey].pop(setting)

        data = pickle.dumps(self.techdict['config'])

        if total_reset:
            sqlite.execute('update settings set config = null where id is 1')
        else:
            sqlite.execute('update settings set config = (?) where id is 1', values=data)

    def config(self, setting, theme=None, stylesheet=False, image=False, curious=False):
        """
        if theme=None the logic is to ask dictionary['default_theme'] for theme
        if not found it falls back to 'default' theme. settings are stored in
        dictionary['theme']['settings'] for pure settings and stylesheets inside
        dictionary['theme']['stylesheets']
        :param setting: string
        :param theme: string or anything that can be a dict.key()
        :param curious: if True, will return value even if active == False
        :return: value or False (instead of None)
        """
        def default_values(setting, stylesheet=False, image=False):
            """
            default values are given here
            :param setting: string
            :return: value or False
            """
            if stylesheet:
                if setting in default_dict['stylesheets']:
                    return default_dict['stylesheets'][setting]
            elif image:
                if setting in default_dict['images']:
                    return default_dict['images'][setting]
            else:
                if setting in default_dict['settings']:
                    return default_dict['settings'][setting]
            return False

        if 'config' in self.techdict:
            data = self.techdict['config']
        else:
            config = tech.retrieve_setting(DB.settings.config)
            if not config:
                data = {}
            elif config:
                data = pickle.loads(config)
                if type(data) != dict:
                    data = {}

                self.techdict.update(dict(config=data))

        c = dict(current_theme='default', default=default_dict)
        for key,val in c.items():
            if key not in data:
                data.update({key:val})

        if not theme:
            theme = data['current_theme']

        c = dict(
            settings=default_dict['settings'],
            stylesheets=default_dict['stylesheets'],
            images=default_dict['images'],
        )

        for key,val in c.items():
            if key not in data[theme]:
                data[theme].update({key:val})

        self.techdict['config'] = data

        if stylesheet:
            if setting in data[theme]['stylesheets']:
                rv = data[theme]['stylesheets'][setting]
            else:
                rv = default_values(setting, stylesheet=True)

        elif image:
            if setting in data[theme]['images']:
                rv = data[theme]['images'][setting]
            else:
                rv = default_values(setting, image=True)

        else:
            if setting in data[theme]['settings']:
                rv = data[theme]['settings'][setting]
            else:
                rv = default_values(setting)

        if rv:
            if rv['active']:
                if rv['value']:
                    return rv['value']
                else:
                    return rv['active']
            elif curious:
                return rv['value']
            else:
                return rv['active']

    @staticmethod
    def zero_prefiller(value, lenght=5):
        string = str(value)
        string = ('0' * (lenght - len(string))) + string
        return string

    @staticmethod
    def retrieve_setting(index):
        """
        :param index: integer
        :return: column
        """
        data = sqlite.execute('select * from settings where id is 1', one=True)
        if data:
            return data[index]

    def signals(self, name=None, reset=False, delete_afterwards=False, delete=False):
        if 'signals' not in self.techdict:
            self.techdict.update(dict(signals={ }))

        if name == None:
            name = 0
            while name in self.techdict['signals']:
                name += 1

        if name not in self.techdict['signals']:
            newsignal = WorkerSignals()
            newsignal.name = name
            self.techdict['signals'][name] = [newsignal]

        elif name in self.techdict['signals'] and reset or delete or delete_afterwards:
            newsignal = WorkerSignals()
            newsignal.name = name
            self.techdict['signals'][name].append(newsignal)
            if delete_afterwards:
                return self.techdict['signals'][name][-2]

        return self.techdict['signals'][name][-1]

    @staticmethod
    def tmp_folder(
            folder_of_interest=None,
            reuse=False,
            delete=False,
            hash=False,
            create_dir=True,
            return_base=False,
        ):
        """
        generates a temporary folder for user
        i prefer to keep my trash inside /mnt/ramdisk
        if conflict, 0,1,2,3 + _ can be added to the END of the file
        :param folder_of_interest: string or none
        :param reuse: bool -> doesnt delete folder if its present, uses cache
        :param delete: bool -> will rmtree the folder before treating
        :param hash: bool -> md5 hashing folder_or_interest for clean dirs
        :return: full path (string)
        """
        if not folder_of_interest:
            md5 = tech.md5_hash_string() # uuid + random + hash
            folder_of_interest = md5.upper()

        elif folder_of_interest and hash:
            md5 = tech.md5_hash_string(folder_of_interest)
            folder_of_interest = md5.upper()

        if os.path.exists(os.environ['TMP_DIR']):
            base_dir = os.environ['TMP_DIR']
        else:
            base_dir = tempfile.gettempdir()

        complete_dir = base_dir + '/' + os.environ['PROGRAM_NAME'] + '/' + folder_of_interest
        complete_dir = os.path.abspath(os.path.expanduser(complete_dir))

        if os.path.exists(complete_dir) and not reuse:
            try:
                if delete:
                    shutil.rmtree(complete_dir)
            except PermissionError:
                pass
            except NotADirectoryError:
                pass
            finally:
                counter = 0
                while os.path.exists(complete_dir):
                    counter += 1
                    tmp = complete_dir + '_' + str(counter)
                    if not os.path.exists(tmp):
                        complete_dir = tmp

        if not os.path.exists(complete_dir) and create_dir:
            pathlib.Path(complete_dir).mkdir(parents=True)

        if return_base:
            return base_dir
        else:
            return complete_dir


    @staticmethod
    def tmp_file(
            file_of_interest=None,
            hash=False,
            reuse=False,
            days=False,
            delete=False,
            new=False,
            extension=None,
            tmp_folder=None,
            part1=None, part2=None
        ):
        """
        :param file_of_interest: string can be anything fuck_a_duck.txt
        :param reuse, doesnt delete file if its present, uses cache
        :param days int, file is no more than x days to reuse
        :param part1, part2 becomes part1_0004_part2.webp with new=True
        :param new, keeps old files and puts a counter on/in new filename
        :param if extension, its added AFTER hashing
        :return: full path (string)
        """
        if not tmp_folder:
            tmp_folder = tech.tmp_folder(folder_of_interest='tmp_files', reuse=True)

        if part1 and part2:
            if file_of_interest:
                file_of_interest += part1 + part2
            else:
                file_of_interest = part1 + part2

        if not file_of_interest:
            md5 = tech.md5_hash_string() # uuid + random + hash
            file_of_interest = md5.upper()

        if hash:
            file_of_interest = tech.md5_hash_string(file_of_interest)

        if extension and extension[0] != '.':
            extension = '.' + extension

        if extension:
            file_of_interest += extension

        complete_path = tmp_folder + '/' + file_of_interest
        complete_path = os.path.abspath(os.path.expanduser(complete_path))

        def delete_file_checker(complete_path):
            if os.path.exists(complete_path):
                if days:
                    if os.path.getmtime(complete_path) < time.time() - (days * 86400):
                        os.remove(complete_path)
                        return

                if delete:
                    os.remove(complete_path)
                    return

        delete_file_checker(complete_path) # deletes first

        if reuse:
            return complete_path

        if os.path.exists(complete_path):
            if os.path.isfile(complete_path):
                try:
                    if not new:
                        os.remove(complete_path)
                except PermissionError:
                    pass
                except IsADirectoryError:
                    pass
                finally:

                    def zero_prefiller(value, lenght=4):
                        string = str(value)
                        string = ('0' * (lenght - len(string))) + string
                        return string

                    counter = 0
                    while os.path.exists(complete_path):
                        counter += 1
                        if part1 and part2:
                            _tmp_path = tmp_folder + '/' + part1 + zero_prefiller(counter) + part2
                            _tmp_path = os.path.abspath(os.path.expanduser(_tmp_path))
                        else:
                            _tmp_path = complete_path + '_' + zero_prefiller(counter)

                        if extension:
                            _tmp_path += extension

                        if not os.path.exists(_tmp_path):
                            complete_path = _tmp_path

        return complete_path


tech = ViktorinoxTechClass()

class WorkerSignals(QObject):
    highlight = pyqtSignal(str)
    activated = pyqtSignal()
    deactivated = pyqtSignal()
