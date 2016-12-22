init -999 python:
    ##################### Import Modules #####################
    import os
    import sys
    import re
    import pygame
    import time
    import string
    import logging
    import fnmatch
    import json
    import math
    from math import sin, cos, radians
    import random
    from random import randrange, randint, choice, shuffle
    import copy
    from copy import deepcopy, copy as shallowcopy
    import itertools
    from itertools import chain, izip_longest
    import operator
    from operator import attrgetter, itemgetter
    import collections
    from collections import OrderedDict
    import xml.etree.ElementTree as ET
    sys.path.append(renpy.loader.transfn("library")) # May fail if we ever post to Android, there is now a new python folder for imports in newer Ren'Py version that can be used instead. SimPy.__init__ may have to be adjusted.
    import simpy
    import cPickle as pickle
    import bisect
                
    ############## Settings and other useful stuff ###############
    # absolute path to the pytfall/game directory, which is formatted according
    # to the conventions of the local OS
    gamedir = os.path.normpath(config.gamedir)
    
    # Binding for easy access to major gfx folders.
    gfxpath = "content/gfx/"
    gfxframes = "content/gfx/frame/"
    gfximages = "content/gfx/images/"
    interfaceimages = "content/gfx/interface/images/"
    interfacebuttons = "content/gfx/interface/buttons/"
    
    def content_path(path):
        '''Returns proper path for a file in the content directory *To be used with os module.'''
        if os.pathsep+"conent"+os.pathsep in path:
            renpy.error("conent already in path: "+path)
        return renpy.loader.transfn('content/' + path)
    
    # enable logging via the 'logging' module
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(name)-15s %(message)s')
    devlog = logging.getLogger(" ".join([config.name, config.version]))
    devlogfile = logging.FileHandler(os.path.join(gamedir, "devlog.txt"))
    devlogfile.setLevel(logging.DEBUG)
    devlog.addHandler(devlogfile)
    devlog.critical("\n--- launch game ---")
    fm = logging.Formatter('%(levelname)-8s %(name)-15s %(message)s')
    devlogfile.setFormatter(fm)
    del fm
    devlog.info("game directory: %s" % str(gamedir)) # Added str() call to avoid cp850 encoding
    
    class TimeLog(_object):
        '''
        Uses Devlog log to time execustion time between the two points.
        Failed to use RenPy log, switching to dev.
        '''
        def __init__(self):
            self._log = []

        def timer(self, msg="default", nested=True):
            if config.developer:
                if not nested or self._log and msg == self._log[-1][0]:
                    (old_msg, timed) = self._log.pop()
                    devlog.info("%s took %s secs to run!"%(old_msg, time.time() - timed))
                    if old_msg == msg:
                        return
                else:
                    found = [i for i in range(0, len(self._log)) if self._log[i][0] == msg]
                    if found:
                        devlog.warn("timing of %s wasn't last on the stack, later timings were:\n%s"%(msg, str(self._log[found[0]:])))
                        (old_msg, timed) = self._log.pop(found[0])
                        devlog.info("%s took %s secs to run!"%(old_msg, time.time() - timed))

                self._log.append((msg, time.time()))
                devlog.info("Starting timer: %s"%msg)

    tl = TimeLog()
    tl.timer("Ren'Py User Init!")

    # setting the window on center
    # useful if game is launched in the window mode
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    # Best I can tell, does nothing, but looks kinda nice :)
    sys.setdefaultencoding('utf-8')
    
    # Getting rid of annoying saves before the menus
    def choice_for_skipping():
        """
        :doc: other
    
        Tells Ren'Py that a choice is coming up soon. This currently has
        two effects:
    
        * If Ren'Py is skipping, and the Skip After Choices preferences is set
          to stop skipping, skipping is terminated.
    
        * An auto-save is triggered. (No Longer!)
        """
    
        if renpy.config.skipping and not renpy.game.preferences.skip_after_choices:
            renpy.config.skipping = None

    def resolve_lib_file(badf, l=1):

        m = re.match(r'^(?:.*[\\/])?(library[\\/].*\.rpy)c?$', badf)
        if m:
            f = m.group(1).replace('\\','/')
            try:
                return (renpy.loader.transfn(f), l)

            except Exception: pass

    def get_screen_src(name):

        for n, f, l in renpy.dump.screens:

            if isinstance(name, basestring) and n == name or n == name+"_screen":

                return resolve_lib_file(f, l)

    def get_label_src(name):

        for n, r in renpy.game.script.namemap.iteritems():

            if isinstance(name, basestring) and n == name or n == name+"_label":

                return resolve_lib_file(r.filename, r.linenumber)

    def screen_link(name):

        r = get_screen_src(name) or get_label_src(name)

        if r:
            def clicked():
                renpy.exports.launch_editor([r[0]], r[1], transient=1)

            return ui.textbutton("{size=10}"+name+"{/size}", clicked=clicked,
                                 xpos=10, background="#00000033")

        return ui.text(name, xpos=10, size=10)

    # Object to specify a lack of value when None can be considered valid.
    # Use as "x is undefined".
    undefined = object()
    
    # Prepping a list to append all events for the registration.
    world_events = list()
    
    # Prepping a list to append all quests for the registration.
    world_quests = list()
    
    # Getting rid of Ren'Py's containers since we don't require rollback.
    dict = _dict
    set = _set
    list = _list
    # object = _object # We are not using Ren'Pys object anywhere but it will throw errors if initiated this early because layout cannot be built with Pythons one.
    _rollback = False
    
    # Registration of extra music channels:
    renpy.music.register_channel("events", "sfx", False, file_prefix="content/sfx/sound/")
    renpy.music.register_channel("events2", "sfx", False,  file_prefix="content/sfx/sound/")
    renpy.music.register_channel("world", "music", True, file_prefix="content/sfx/music/world/")
    renpy.music.register_channel("gamemusic", "music", True, file_prefix="content/sfx/music/")
    
    ######################## Classes/Functions ###################################
    # Auto Animation from a folder:
    def animate(path, delay=0.25, function=None, transition=None, loop=False):
        # Build a list of all images:
        files = os.listdir("".join([gamedir, path]))
        images = list("".join([path[1:], "/", fn]) for fn in files if fn.endswith(('.png', '.gif', ".jpg", ".jpeg")))
        # Build a list of arguments
        args = list()
        # for image in images:
            # args.extend([image, delay, transition])
        # return anim.TransitionAnimation(*args)
        for image in images:
            args.append([image, delay])
        return AnimateFromList(args, loop=loop)

    class Flags(_object):
        """Simple class to log all variables into a single namespace
        
        Now and count...
        """
        def __init__(self):
            self.flags = dict()
            
        def __iter__(self):
            return iter(self.flags)
        
        def set_flag(self, flag, value=True):
            self.flags[flag] = value
            
        def up_counter(self, flag, value=1, max=None, delete=False):
            """A more advanced version of a counter than mod_flag.
            
            This can keep track of max and min.
            """
            if flag in self.flags:
                f = self.flags[flag]
                new_value = f + value
                if (max is not None) and new_value >= max:
                    self.flags[flag] = max
                    if delete:
                        self.del_flag(flag)
                else:
                    self.flags[flag] = new_value
            else:
                self.flags[flag] = value
                
        def down_counter(self, flag, value=1, min=None, delete=False):
            """A more advanced version of a counter than mod_flag.
            
            This can keep track of max and min.
            """
            if flag in self.flags:
                f = self.flags[flag]
                new_value = f - value
                if (min is not None) and new_value <= min:
                    self.flags[flag] = min
                    if delete:
                        self.del_flag(flag)
                else:
                    self.flags[flag] = new_value
            else:
                self.flags[flag] = value
            
        def mod_flag(self, flag, value):
            """Can be used as a simple counter for integer based flags.
            
            Simply changes the value of the flag otherwise.
            """
            if not flag in self.flags:
                self.flags[flag] = value
                if config.debug and "next" not in last_label: # Not logged during last day for clearer logs.
                    devlog.warning("{} flag modded before setting it's value!".format(flag))
                return
                
            if isinstance(value, int):
                self.flags[flag] += value
            else:
                self.flags[flag] = value
                
        def set_union(self, flag, value):
            """Can be used to create sets.
            
            If a flag exists, expects it to be a set() and creates a union with it.
            """
            if not flag in self.flags:
                self.flags[flag] = set(value)
                if config.debug and "next" not in last_label: # Not logged during last day for clearer logs.
                    devlog.warning("{} flag modded before setting it's value!".format(flag))
                return
                
            if isinstance(value, (set, list, tuple)):
                self.flags[flag] = self.flags[flag].union(value)
            else:
                self.flags[flag] = self.flags[flag].union(set(value))
                
        def flag(self, flag):
            if flag in self.flags:
                return self.flags[flag]
            else:
                return False
                
        def del_flag(self, flag):
            if flag in self.flags:
                del(self.flags[flag])
                
        def has_flag(self, flag):
            """Check if flag exists at all (not just set to False).
            """
            return flag in self.flags
            
        
    def dice(percent_chance):
        """ returns randomly True with given % chance, or False """
        return random.random() * 100 <= percent_chance
    
    # "wrapper" around the notify
    def notify(message, style=False):
        if config.developer:
            if style:
                msg = "{=%s}%s"%(style, str(message))
                renpy.notify(u"%s"%msg) 
            else:
                renpy.notify(u"{size=+10}%s"%str(message))

    # Safe jump, if label doesn't exists, game will notify about it
    def jump(labelname):
        if renpy.has_label(labelname):
            notify("jump %s" % labelname)
            renpy.jump(labelname)
        else:
            notify(u"Label '%s' does not exist." % labelname)

    # Useful methods for path        
    def listdir(dir):
        return os.listdir(os.path.join(gamedir, dir))

    def exist(path):
        if isinstance(path, basestring):
            return os.path.exists(os.path.join(gamedir, path))

        return all(exist(x) for x in path)

    # Analizis of strings and turning them into int, float or bool.
    # Useful for importing data from xml.
    def parse(string):
        try:
            value = int(string)
        except TypeError:
            value = string
        except AttributeError:
            value = string
        except ValueError:
            try:
                value = float(string)
            except ValueError:
                if string.lower() in ['true', 'yes', 'on']:
                    value = True
                elif string.lower() in ['false', 'no', 'off', 'none']:
                    value = False
                else:
                    value = string
        return value

    # Returns the position of cursor if show cursorPosition is called
    # show cursorPosition on bottom
    def dd_cursor_position(st, at):
        x, y = renpy.get_mouse_pos()
        return Text("{size=-5}%d - %d"%(x, y)), .1

    class JsonSchemator(object):
        def __init__(self, action=None):
            self.action = action if action is not None else "skip" # the default: no validation.

        def configure(self, timelog=None):
            """ load schemas from schema directory """

            if self.action != "skip":

                import jsonschema
                self._err = []
                self._validator = {}
                self._schema = {}
                self._tl = timelog
                basefilename = renpy.loader.transfn("schema"+os.path.sep+"data_types.json")
                with open(basefilename) as base_data_file:
                    base = json.load(base_data_file)

                for concept in ["stat", "skill", "element", "attack", "defence", "magic"]:

                    base['definitions'][concept+"Object"] = {
                        "additionalProperties": False,
                        "properties": {
                            key: {} for key in base['definitions'][concept]['enum']
                        },
                        "type": "object"
                    }

                for fin in listdir("schema"):
                    if fin != "data_types.json":
                        filename = renpy.loader.transfn("schema"+os.path.sep+fin)
                        devlog.info(filename)

                        name = fin[:-5]
                        self._schema[name] = base.copy()
                        with open(filename) as data_file:
                            self._schema[name]['items'] = json.load(data_file)
                        self._validator[name] = jsonschema.Draft4Validator(self._schema[name])

        def err(self, err, file=None):
            devlog.warn(err)
            if file is not None:
                err = err + ":"+os.linesep+renpy.loader.transfn(file)
            self._err.append(err)

        def add(self, name, content, filename=""):

            if self.action == "validate" or self.action == "strict":

                if not name in self._validator:
                    self.err("No schema yet to validate a "+name+" json file")
                else:
                    file = filename.rsplit(os.path.sep+"game"+os.path.sep, 1)[1]
                    if self._tl:
                        time_msg = "Validating "+file
                        self._tl.timer(time_msg)

                    try:
                        self._validator[name].validate(content)
                    except Exception, e:
                        self.err("Did not validate as "+name, file)

                        errors = sorted(self._validator[name].iter_errors(content), key=lambda e: e.path)
                        for error in errors:
                            self.err(error.message)

                            for suberror in sorted(error.context, key=lambda e: e.schema_path):
                                self.err(filename+":"+str(suberror.message))
                        #renpy.error(os.linesep.join(self._err)+"\n"+json.dumps(self._schema[name], indent=4, sort_keys=True))

                    if self._tl:
                        self._tl.timer(time_msg)

        def finish(self):
            if self.action == "strict" and len(self._err) > 0:
                renpy.error(os.linesep.join(self._err))

    # set to False to update existing json files in schema directory, None skips validation and writing
    jsstor = JsonSchemator()

    # -------------------------------------------------------------------------------------------------------- Ends here

    ########################## Images ##########################
    # Colors are defined in colors.rpy to global namespace, prolly was not the best way but file was ready to be used.
    
    # Setting default town path to persistent:
    # if not persistent.town_path:
        # persistent.town_path = "content/gfx/bg/locations/map_buttons/dark/"
    # renpy.image("bg humans", "".join([persistent.town_path, "humans.jpg"]))
    renpy.image("bg humans", "content/gfx/bg/locations/map_buttons/gismo/humans.jpg")
    
    renpy.image('bg black', Solid((0, 0, 0, 255)))
    renpy.image('bg blood', Solid((150, 6, 7, 255)))
    
    ##################### Autoassociation #####################
    # Backrounds are automatically registered in the game and set to width/height of the default screen
    # displayed by "show bg <filename>" or similar commands
    # file name without the extention
    # for fname in os.listdir(gamedir + '/content/gfx/be/webm'):
        # if fname.endswith(".webm") and not "mask" in fname:
            # tag = fname[:-5]
            # image = 'content/gfx/bg/' + fname
            # renpy.image(tag, im.Scale(image, config.screen_width,
                        # config.screen_height))
    
    for fname in os.listdir(gamedir + '/content/gfx/bg'):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            tag = 'bg ' + fname.rsplit(".", 1)[0]
            image = 'content/gfx/bg/' + fname
            renpy.image(tag, im.Scale(image, config.screen_width,
                        config.screen_height))
    
    for fname in os.listdir(gamedir + '/content/gfx/bg/locations'):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            tag = 'bg ' + fname.rsplit(".", 1)[0]
            image = 'content/gfx/bg/locations/' + fname
            renpy.image(tag, im.Scale(image, config.screen_width,
                        config.screen_height))
            
    for fname in os.listdir(gamedir + '/content/gfx/bg/story'):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            tag = 'bg ' + 'story ' + fname.rsplit(".", 1)[0]
            image = 'content/gfx/bg/story/' + fname
            renpy.image(tag, im.Scale(image, config.screen_width,
                        config.screen_height))
           
    for fname in os.listdir(gamedir + '/content/gfx/bg/be'):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            tag = 'bg ' + fname.rsplit(".", 1)[0]
            image = 'content/gfx/bg/be/' + fname
            renpy.image(tag, im.Scale(image, config.screen_width,
                        config.screen_height))

    # Same thing for sprites and NPC        
    for fname in os.listdir(gamedir + '/content/gfx/sprites'):
        if fname.endswith('.png'):
            tag = fname[:-4]
            image = 'content/gfx/sprites/' + fname
            renpy.image(tag, image)
            
    for fname in os.listdir(gamedir + '/content/gfx/sprites/npc'):
        if fname.endswith('.png'):
            tag = 'npc ' + fname[:-4]
            image = 'content/gfx/sprites/npc/' + fname
            renpy.image(tag, ProportionalScale(image, 400,
                        600))
            tag = 'npc ' + fname[:-4] + '_novel'
            image = 'content/gfx/sprites/npc/' + fname
            renpy.image(tag, ProportionalScale(image, 600,
                        700))
            
    # We'll define same images again so multiple npcs could be placed on the screen at the same time.        
    for fname in os.listdir(gamedir + '/content/gfx/sprites/npc'):
        if fname.endswith('.png'):
            tag = 'npc2 ' + fname[:-4]
            image = 'content/gfx/sprites/npc/' + fname
            renpy.image(tag, ProportionalScale(image, 400,
                        600))
            tag = 'npc ' + fname[:-4] + '_novel'
            image = 'content/gfx/sprites/npc/' + fname
            renpy.image(tag, ProportionalScale(image, 600,
                        700))
            
    # Auto-Animations are last
    def load_frame_by_frame_animations_from_dir(folder):
        path = content_path(folder)
        for dir in os.listdir(path):
            split_dir = dir.split(" ")
            len_split = len(split_dir)
            
            folder_path = "/".join(["/content", folder, dir])
            img_name = split_dir[0]
            delay = float(split_dir[1]) if len_split > 1 else 0.25
            loop = bool(int(split_dir[2])) if len_split > 2 else False
            
            renpy.image(img_name, animate(folder_path, delay, loop=loop))
            
    load_frame_by_frame_animations_from_dir("gfx/animations")
    load_frame_by_frame_animations_from_dir("gfx/be/auto-animations")


# Additional 'constant' definements

# Adds a number of useful development tools to the left buttom corner
# X - Instant Exit
# R - Recompilation of the game
# Shows mouse coordinates
screen debug_tools():
    zorder 5
    vbox:
        align (0.02, 0.98)
        hbox:
            xalign 0
            button:
                text "X"
                action Quit(confirm=False)
            button:
                text "R"
                action ui.callsinnewcontext("_save_reload_game")

        add DynamicDisplayable(dd_cursor_position) xpos 10
        $ screen_link(last_label)


init -1 python: # Constants:
    # for f in renpy.list_files():
        # if f.endswith((".png", ".jpg")):
            # renpy.image(f, At(f, slide(so1=(600, 0), t1=0.7, eo2=(1300, 0), t2=0.7)))
    SLOTALIASES = {"smallweapon": "Left Hand", "weapon": "Right Hand", "amulet": "Neck", "feet": "Legs", "quest": "Special"}
    equipSlotsPositions = dict()
    equipSlotsPositions['head'] = [u'Head', 0.2, 0.1]
    equipSlotsPositions['body'] = [u'Body', 0.2, 0.3]
    equipSlotsPositions['amulet'] = [u'Amulet', 1.0, 0.3]
    equipSlotsPositions['cape'] = [u'Cape', 1.0, 0.1]
    equipSlotsPositions['weapon'] = [u'Weapon', 0.2, 0.5]
    equipSlotsPositions['smallweapon'] = [u'Small Weapon', 1.0, 0.5]
    equipSlotsPositions['feet'] = [u'Feet', 1.0, 0.7]
    equipSlotsPositions['misc'] = [u'Misc', 0.025, 0.41]
    equipSlotsPositions['wrist'] = [u'Wrist', 0.2, 0.7]
    equipSlotsPositions['ring'] = [u'Ring', 1.18, 0.2]
    equipSlotsPositions['ring1'] = [u'Ring', 1.18, 0.4]
    equipSlotsPositions['ring2'] = [u'Ring', 1.18, 0.6]
    
init:
    default SKILLS_MAX = {k:5000 for k in PytCharacter.SKILLS}
    default SKILLS_THRESHOLD = {k:2000 for k in PytCharacter.SKILLS} # Must be exceeded before skills becomes harder to gain.
    default just_view_next_day = False
    default char = None
    default char_equip = None
    default girls = None
    default reset_building_management = True
    
init 999 python:
    # ensure that all initialization debug messages have been written to disk
    devlogfile.flush()
    
    # Build Maps:
    # tilemap = TileMap("my_map.json")
    # map_image = tilemap.build_map()
    
    tl.timer("Ren'Py User Init!")
