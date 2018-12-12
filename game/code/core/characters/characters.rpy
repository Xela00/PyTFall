# Characters classes and methods:
init -9 python:
    ###### Character Classes ######
    class PytCharacter(Flags, Tier, JobsLogger, Pronouns):
        STATS = set()
        SKILLS = set(["vaginal", "anal", "oral", "sex", "strip", "service",
                      "refinement", "group", "bdsm", "dancing",
                      "bartending", "cleaning", "waiting", "management",
                      "exploration", "teaching", "swimming", "fishing",
                      "security"])
        # Used to access true, final, adjusted skill values through direct access to class, like: char.swimmingskill
        FULLSKILLS = set(skill + "skill" for skill in SKILLS)
        GEN_OCCS = set(["SIW", "Combatant", "Server", "Specialist"])
        STATUS = set(["slave", "free"])

        MOOD_TAGS = set(["angry", "confident", "defiant", "ecstatic", "happy",
                         "indifferent", "provocative", "sad", "scared", "shy",
                         "tired", "uncertain"])
        UNIQUE_SAY_SCREEN_PORTRAIT_OVERLAYS = ["zoom_fast", "zoom_slow", "test_case"]
        """Base Character class for PyTFall.
        """
        def __init__(self, arena=False, inventory=False, effects=False, is_worker=True):
            super(PytCharacter, self).__init__()
            self.img = ""
            self.portrait = ""
            self.gold = 0

            self.name = ""
            self.fullname = ""
            self.nickname = ""

            self._mc_ref = None # This is how characters refer to MC (hero). May depend on case per case basis and is accessed through obj.mc_ref property.
            self.height = "average"
            self.gender = "female"
            self.origin = ""
            self.status = "free"
            self.race = ""
            self.full_race = ""

            self.AP = 3
            self.baseAP = 3
            self.reservedAP = 0
            self.setAP = 1 # This is set to the AP calculated for that day.
            self.jobpoints = 0


            # Locations and actions, most are properties with setters and getters.
            self._location = None # Present Location.
            self._workplace = None  # Place of work.
            self._home = None # Living location.
            self._action = None

            # Traits:
            self.upkeep = 0 # Required for some traits...
            self.stored_upkeep = 0 # Recalculated every day and used in the gameworld.

            self.traits = Traits(self)
            self.resist = SmartTracker(self, be_skill=False)  # A set of any effects this character resists. Usually it's stuff like poison and other status effects.

            # Relationships:
            self.friends = set()
            self.lovers = set()

            # Preferences:
            self.likes = set() # These are simple sets containing objects and possibly strings of what this character likes or dislikes...
            self.dislikes = set() # ... more often than not, this is used to compliment same params based of traits. Also (for example) to set up client preferences.

            # Arena relared:
            if arena:
                self.fighting_days = list() # Days of fights taking place
                self.arena_willing = False # Indicates the desire to fight in the Arena
                self.arena_permit = False # Has a permit to fight in main events of the arena.
                self.arena_active = False # Indicates that girl fights at Arena at the time.
                self._arena_rep = 0 # Arena reputation
                self.arena_stats = dict()
                self.combat_stats = dict()

            # Items
            if inventory:
                self.inventory = Inventory(15)
                self.eqslots = {
                    'head': False,
                    'body': False,
                    'cape': False,
                    'feet': False,
                    'amulet': False,
                    'wrist': False,
                    'weapon': False,
                    'smallweapon': False,
                    'ring': False,
                    'ring1': False,
                    'ring2': False,
                    'misc': False,
                    'consumable': None,
                }
                self.consblock = dict()  # Dict (Counter) of blocked consumable items.
                self.constemp = dict()  # Dict of consumables with temp effects.
                self.miscitems = dict()  # Counter for misc items.
                self.miscblock = list()  # List of blocked misc items.
                self.eqsave = [self.eqslots.copy(), self.eqslots.copy(), self.eqslots.copy()] # saved equipment states
                self.last_known_aeq_purpose = "" # We don't want to aeq needlessly, it's an expensive operation.
                # List to keep track of temporary effect
                # consumables that failed to activate on cmax **We are not using this or at least I can't find this in code!
                # self.maxouts = list()

            # For workers (like we may not want to run this for mobs :) )
            if is_worker:
                Tier.__init__(self)
                JobsLogger.__init__(self)

            # Stat support Dicts:
            stats = {
                'charisma': [5, 0, 50, 60],          # means [stat, min, max, lvl_max]
                'constitution': [5, 0, 50, 60],
                'joy': [50, 0, 100, 200],
                'character': [5, 0, 50, 60],
                'reputation': [0, 0, 100, 100],
                'health': [100, 0, 100, 200],
                'fame': [0, 0, 100, 100],
                'mood': [0, 0, 1000, 1000], # not used...
                'disposition': [0, -1000, 1000, 1000],
                'vitality': [100, 0, 100, 200],
                'intelligence': [5, 0, 50, 60],

                'luck': [0, -50, 50, 50],

                'attack': [5, 0, 50, 60],
                'magic': [5, 0, 50, 60],
                'defence': [5, 0, 50, 60],
                'agility': [5, 0, 50, 60],
                'mp': [30, 0, 30, 50]
            }
            self.stats = Stats(self, stats=stats)
            self.STATS = set(self.stats.stats.keys())

            if effects:
                # Effects assets:
                self.effects = _dict()

            # BE Bridge assets: @Review: Note: Maybe move this to a separate class/dict?
            self.besprite = None # Used to keep track of sprite displayable in the BE.
            self.beinx = 0 # Passes index from logical execution to SFX setup.
            self.beteampos = None # This manages team position bound to target (left or right on the screen).
            self.row = 1 # row on the battlefield, used to calculate range of weapons.
            self.front_row = True # 1 for front row and 0 for back row.
            self.betag = None # Tag to keep track of the sprite.
            self.dpos = None # Default position based on row + team.
            self.sopos = () # Status underlay position, which should be fixed.
            self.cpos = None # Current position of a sprite.
            self.besk = None # BE Show **Kwargs!
            # self.besprite_size = None # Sprite size in pixels. THIS IS NOW A PROPERTY!
            self.allegiance = None # BE will default this to the team name.
            self.controller = "player"
            self.beeffects = []
            self.can_die = False
            self.dmg_font = "red"
            self.status_overlay = [] # This is something I wanted to test out, trying to add tiny status icons somehow.

            self.attack_skills = SmartTracker(self)  # Attack Skills
            self.magic_skills = SmartTracker(self)  # Magic Skills
            self.default_attack_skill = battle_skills["Fist Attack"] # This can be overwritten on character creation!

            # Game world status:
            self.alive = True
            self._available = True

            # Action tracking (AutoRest job for instance):
            self.previousaction = ''

            self.clear_img_cache()

            # Say style properties:
            self.say_style = {"color": ivory}

            # We add Neutral element here to all classes to be replaced later:
            self.apply_trait(traits["Neutral"])

            self.say = None # Speaker...

        def __getattr__(self, key):
            if key == "defense":
                key = "defence"

            stats = self.__dict__.get("stats", {})
            if key in self.STATS:
                return stats._get_stat(key)
            elif key.lower() in self.SKILLS:
                return stats._raw_skill(key)
            elif key in self.FULLSKILLS:
                return self.stats.get_skill(key[:-5])
            raise AttributeError("Object of %r class has no attribute %r" %
                                          (self.__class__, key))

        def __setattr__(self, key, value):
            if key == "defense":
                key = "defence"

            if key in self.STATS:
                # Primary stat dict modifier...
                value = value - self.stats._get_stat(key)
                self.stats._mod_base_stat(key, int(round(value)))
            elif key.lower() in self.SKILLS:
                self.__dict__["stats"]._mod_raw_skill(key, value)
            else:
                super(PytCharacter, self).__setattr__(key, value)

        # Money:
        def take_money(self, value, reason="Other"):
            if hasattr(self, "fin"):
                return self.fin.take_money(value, reason)
            else:
                if value <= self.gold:
                    self.gold -= value
                    return True
                else:
                    return False

        def add_money(self, value, reason="Other"):
            if hasattr(self, "fin"):
                self.fin.add_money(value, reason)
            else:
                self.gold += value

        # Game assist methods:
        def set_status(self, s):
            if s not in ["slave", "free"]:
                raise Exception("{} status is not valid for {} with an id: {}".format(s, self.__class__, self.id))
            self.status = s

        def update_sayer(self):
            self.say = Character(self.nickname, show_two_window=True, show_side_image=self.show("portrait", resize=(120, 120)), **self.say_style)

        # Properties:
        @property
        def is_available(self):
            # False if we cannot reach the character.
            if not self.alive:
                return False
            if self.action == "Exploring":
                return False
            if self in pytfall.ra:
                return False
            return self._available

        @property
        def basetraits(self):
            return self.traits.basetraits

        @property
        def gen_occs(self):
            # returns a list of general occupation from Base Traits only.
            return self.traits.gen_occs

        @property
        def occupations(self):
            """
            Formerly "occupation", will return a set of jobs that a worker may be willing to do based of her basetraits.
            Not decided if this should be strings, Trait objects of a combination of both.
            """
            allowed = set()
            for t in self.traits:
                if t.basetrait:
                    allowed.add(t)
                    allowed = allowed.union(t.occupations)
            return allowed

        @property
        def arena_rep(self):
            return self._arena_rep
        @arena_rep.setter
        def arena_rep(self, value):
            if value <= -500:
                self._arena_rep = -500
            else:
                self._arena_rep = value

        # Locations related ====================>
        @property
        def location(self):
            # Physical location at the moment, this is not used a lot right now.
            # if all([self._location == hero, isinstance(self, Char), self.status == "free"]):
                # return "Own Dwelling"
            # elif self._location == hero: # We set location to MC in most cases, this may be changed soon?
                # return "Streets"
            # else:
            return self._location # Otherwise we use the
        # Not sure we require a setter here now that I've added home and workplaces.
        @location.setter
        def location(self, value):
            # *Adding some location code that needs to be executed always:
            # if value == "slavemarket":
                # self.status = "slave"
                # self.home = "slavemarket"
            self._location = value

        @property
        def action(self):
            return self._action
        @action.setter
        def action(self, value):
            # Resting considerations:
            c0 = getattr(value, "type", None) == "Resting"
            c1 = self.previousaction == value
            if c0 or c1:
                self._action = value
                return

            # SchoolCourses, we need to remove the student as action is being changed:
            if isinstance(self._action, SchoolCourse):
                course = self._action
                self._action = None
                course.remove_student(self)

            old_action = self._action
            wp = self.workplace
            mj = simple_jobs["Manager"]

            if getattr(wp, "manager", None) == self:
                # Works as a Manager so special considerations are needed:
                wp.manager = None
                wp.manager_effectiveness = 0
            if value == mj:
                # Check if we already have a manager in the building:
                if wp.manager:
                    wp.manager.previousaction = ''
                    wp.manager._action = None
                    wp.manager = None
                wp.manager = self

            self._action = value

        @property
        def workplace(self):
            return self._workplace
        @workplace.setter
        def workplace(self, value):
            if value != self._workplace:
                # We need to make sure that manager is reassigned:
                mj = simple_jobs["Manager"]
                old_action = self.action
                if old_action == mj:
                    self.action = None
                elif isinstance(value, Job):
                    if old_action not in value.get_valid_jobs():
                        self.action = None
            self._workplace = value

        @property
        def home(self):
            return self._home
        @home.setter
        def home(self, value):
            """Home setter needs to add/remove actors from their living place.

            Checking for vacancies should be handle at functions that are setting
            homes.
            """
            if isinstance(self._home, HabitableLocation):
                self._home.inhabitants.remove(self)
            if isinstance(value, HabitableLocation):
                value.inhabitants.add(self)
            self._home = value

        # Alternative Method for modding first layer of stats:
        def add_exp(self, value, adjust=True):
            # Adds experience, adjusts it by default...
            if adjust:
                value = adjust_exp(self, value)
            self.exp += value

        def mod_stat(self, stat, value):
            self.stats._mod_base_stat(stat, value)

        def mod_skill(self, skill, value):
            self.stats._mod_raw_skill(skill, value, from__setattr__=False)

        def get_max(self, stat):
            return self.stats.get_max(stat)

        def adjust_exp(self, exp):
            '''
            Temporary measure to handle experience...
            '''
            return adjust_exp(self, exp)

        def get_skill(self, skill):
            return self.stats.get_skill(skill)

        @property
        def elements(self):
            return _list(e for e in self.traits if e.elemental)

        @property
        def exp(self):
            return self.stats.exp
        @exp.setter
        def exp(self, value):
            self.stats._mod_exp(value)

        @property
        def level(self):
            return self.stats.level
        @property
        def goal(self):
            return self.stats.goal

        # -------------------------------------------------------------------------------->
        # Show to mimic girls method behavior:
        @property
        def besprite_size(self):
            return get_size(self.besprite)

        def get_sprite_size(self, tag="vnsprite"):
            # First, lets get correct sprites:
            if tag == "battle_sprite":
                if self.height == "average":
                    resize = (200, 180)
                elif self.height == "tall":
                    resize = (200, 200)
                elif self.height == "short":
                    resize = (200, 150)
                else:
                    char_debug("Unknown height setting for %s" % self.id)
                    resize = (200, 180)
            elif tag == "vnsprite":
                if self.height == "average":
                    resize = (1000, 520)
                elif self.height == "tall":
                    resize = (1000, 600)
                elif self.height == "short":
                    resize = (1000, 400)
                else:
                    char_debug("Unknown height setting for %s" % self.id)
                    resize = (1000, 500)
            else:
                raise Exception("get_sprite_size got unknown type for resizing!")
            return resize

        ### Displaying images:
        @property
        def path_to_imgfolder(self):
            if isinstance(self, rChar):
                return rchars[self.id]["_path_to_imgfolder"]
            else:
                return self._path_to_imgfolder

        def _portrait(self, st, at):
            if self.flag("fixed_portrait"):
                return self.flag("fixed_portrait"), None
            else:
                return self.show("portrait", self.get_mood_tag(), type="first_default", add_mood=False, cache=True, resize=(120, 120)), None

        def override_portrait(self, *args, **kwargs):
            kwargs["resize"] = kwargs.get("resize", (120, 120))
            kwargs["cache"] = kwargs.get("cache", True)
            if self.has_image(*args, **kwargs): # if we have the needed portrait, we just show it
                self.set_flag("fixed_portrait", self.show(*args, **kwargs))
            elif "confident" in args: # if not...
                if self.has_image("portrait", "happy"): # then we replace some portraits with similar ones
                    self.set_flag("fixed_portrait", self.show("portrait", "happy", **kwargs))
                elif self.has_image("portrait", "indifferent"):
                    self.set_flag("fixed_portrait", self.show("portrait", "indifferent", **kwargs))
            elif "suggestive" in args:
                if self.has_image("portrait", "shy"):
                    self.set_flag("fixed_portrait", self.show("portrait", "shy", **kwargs))
                elif self.has_image("portrait", "happy"):
                    self.set_flag("fixed_portrait", self.show("portrait", "happy", **kwargs))
            elif "ecstatic" in args:
                if self.has_image("portrait", "happy"):
                    self.set_flag("fixed_portrait", self.show("portrait", "happy", **kwargs))
                elif self.set_flag("fixed_portrait", self.show("portrait", "shy")):
                    self.set_flag("fixed_portrait", self.show("portrait", "shy", **kwargs))
            elif "shy" in args:
                if self.has_image("portrait", "uncertain"):
                    self.set_flag("fixed_portrait", self.show("portrait", "uncertain", **kwargs))
            elif "uncertain" in args:
                if self.has_image("portrait", "shy"):
                    self.set_flag("fixed_portrait", self.show("portrait", "shy", **kwargs))
            else: # most portraits will be replaced by indifferent
                if self.has_image("portrait", "indifferent"):
                    self.set_flag("fixed_portrait", self.show("portrait", "indifferent", **kwargs))

        def show_portrait_overlay(self, s, mode="normal"):
            self.say_screen_portrait_overlay_mode = s

            if not s in self.UNIQUE_SAY_SCREEN_PORTRAIT_OVERLAYS:
                interactions_portraits_overlay.change(s, mode)

        def hide_portrait_overlay(self):
            interactions_portraits_overlay.change("default")
            self.say_screen_portrait_overlay_mode = None

        def restore_portrait(self):
            self.say_screen_portrait_overlay_mode = None
            self.del_flag("fixed_portrait")

        def get_mood_tag(self):
            """
            This should return a tag that describe characters mood.
            We do not have a proper mood flag system at the moment so this is currently determined by joy and
            should be improved in the future.
            """
            # tags = list()
            # if self.fatigue < 50:
                # return "tired"
            # if self.health < 15:
                # return "hurt"
            if self.joy > 75:
                return "happy"
            elif self.joy > 40:
                return "indifferent"
            else:
                return "sad"

        def select_image(self, *tags, **kwargs):
            '''Returns the path to an image with the supplied tags or "".
            '''
            tagset = set(tags)
            exclude = kwargs.get("exclude", None)

            # search for images
            imgset = tagdb.get_imgset_with_all_tags(tagset)
            if exclude:
                imgset = tagdb.remove_excluded_images(imgset, exclude)

            # randomly select an image
            if imgset:
                return choice(tuple(imgset))
            else:
                return ""

        def has_image(self, *tags, **kwargs):
            """
            Returns True if image is found.
            exclude k/w argument (to exclude undesired tags) is expected to be a list.
            """
            tags = list(tags)
            tags.append(self.id)
            exclude = kwargs.get("exclude", None)

            # search for images
            if exclude:
                imgset = tagdb.get_imgset_with_all_tags(tags)
                imgset = tagdb.remove_excluded_images(imgset, exclude)
            else:
                imgset = tagdb.get_imgset_with_all_tags(tags)

            return bool(imgset)

        def show(self, *tags, **kwargs):
            '''Returns an image with the supplied tags.

            Under normal type of images lookup (default):
            First tag is considered to be most important.
            If no image with all tags is found,
            game will look for a combination of first and any other tag from second to last.

            Valid keyword arguments:
                resize = (maxwidth, maxheight)
                    Both dimensions are required
                default = any object (recommended: a renpy image)
                    If default is set and no image with the supplied tags could
                    be found, the value of default is returned and a warning is
                    printed to "devlog.txt".
                cache = load image/tags to cache (can be used in screens language directly)
                type = type of image lookup order (normal by default)
                types:
                     - normal = normal search behavior, try all tags first, then first tag + one of each tags taken from the end of taglist
                     - any = will try to find an image with any of the tags chosen at random
                     - first_default = will use first tag as a default instead of a profile and only than switch to profile
                     - reduce = try all tags first, if that fails, pop the last tag and try without it. Repeat until no tags remain and fall back to profile or default.
                add_mood = Automatically adds proper mood tag. This will not work if a mood tag was specified on request OR this is set to False
                gm_mode = overwrite to add nude/not nude logic for GMs pictures no matter how and where we get them
            '''
            maxw, maxh = kwargs.get("resize", (None, None))
            cache = kwargs.get("cache", False)
            label_cache = kwargs.get("label_cache", False)
            exclude = kwargs.get("exclude", None)
            type = kwargs.get("type", "normal")
            default = kwargs.get("default", None)
            gm_mode = kwargs.get("gm_mode", False)

            if gm_mode and not "Slime" in self.traits:
                if check_lovers(self, hero) or "Exhibitionist" in self.traits:
                    if dice(40):
                        if not "nude" in tags:
                            tags += ("nude",)
                        if not "revealing" in tags:
                            tags += ("revealing",)
                else:
                    if not "nude" in exclude:
                        if not exclude:
                            exclude = ["nude"]
                        else:
                            exclude.append("nude")


            if not all([maxw, maxh]):
                t0 = "Width or Height were not provided to an Image when calling .show method!\n"
                t1 = "Character id: {}; Action: {}; Tags: {}; Last Label: {}.".format(self.id, str(self.action),
                                                                    ", ".join(tags), str(last_label))
                raise Exception(t0 + t1)

            # Direct image request:
            if "-" in tags[0]:
                _path = "/".join([self.path_to_imgfolder, tags[0]])
                if not renpy.loadable(_path):
                    _path = "content/gfx/interface/images/no_image.png"
                return ProportionalScale(_path, maxw, maxh)

            # Mood will never be checked in auto-mode when that is not sensible
            add_mood = kwargs.get("add_mood", True)
            if set(tags).intersection(self.MOOD_TAGS):
                add_mood = False

            pure_tags = list(tags)
            tags = list(tags)
            if add_mood:
                mood_tag = self.get_mood_tag()
                tags.append(mood_tag)

            if label_cache:
                for entry in self.label_cache:
                    if entry[0] == tags and entry[1] == last_label:
                        return ProportionalScale(entry[2], maxw, maxh)

            if cache:
                for entry in self.cache:
                    if entry[0] == tags:
                         return ProportionalScale(entry[1], maxw, maxh)

            # Select Image (set imgpath)
            imgpath = ""
            if type in ["normal", "first_default", "reduce"]:
                imgpath = self.select_image(self.id, *tags, exclude=exclude)
                if not imgpath and add_mood:
                    imgpath = self.select_image(self.id, *pure_tags, exclude=exclude)

                if not imgpath and len(pure_tags) > 1:
                    if type in ["normal", "first_default"]:
                        main_tag = None
                        for tag in pure_tags:
                            if main_tag is None:
                                main_tag = tag
                                continue

                            # Try with the mood first:
                            if add_mood:
                                imgpath = self.select_image(main_tag, tag, self.id, mood_tag, exclude=exclude)
                            # Without mood
                            if not imgpath:
                                imgpath = self.select_image(main_tag, tag, self.id, exclude=exclude)
                            if imgpath:
                                break

                        if type == "first_default" and not imgpath: # In case we need to try first tag as default (instead of profile/default) and failed to find a path.
                            if add_mood:
                                imgpath = self.select_image(main_tag, self.id, mood_tag, exclude=exclude)
                            if not imgpath:
                                imgpath = self.select_image(main_tag, self.id, exclude=exclude)

                    elif type == "reduce":
                        _tags = pure_tags[:]
                        while not imgpath:
                            _tags.pop()
                           
                            # Do not try with empty tags TODO why not? 
                            if not _tags:
                                break
                            # Try with mood first:
                            if add_mood:
                                imgpath = self.select_image(self.id, mood_tag, *_tags, exclude=exclude)
                            if not imgpath:
                                imgpath = self.select_image(self.id, *_tags, exclude=exclude)


            elif type == "any":
                # Try with the mood first:
                if add_mood:
                    for tag in pure_tags:
                        imgpath = self.select_image(self.id, tag, mood_tag, exclude=exclude)
                        if imgpath:
                            break
                # Then try 'any' behavior without the mood:
                if not imgpath:
                    for tag in pure_tags:
                        imgpath = self.select_image(self.id, tag, exclude=exclude)
                        if imgpath:
                            break

            force_battle_sprite = False
            if not imgpath:
                if not default:
                    # New rule (Default Battle Sprites):
                    if "battle_sprite" in pure_tags:
                        force_battle_sprite = True
                    else:
                        if add_mood:
                            imgpath = self.select_image(self.id, 'profile', mood_tag)
                        if not imgpath:
                            imgpath = self.select_image(self.id, 'profile')
                else:
                    char_debug("could not find image with tags %s" % sorted(tags))
                    return default

            # If we got here without being able to find an image ("profile" lookup failed is the only option):
            if force_battle_sprite: # New rule (Default Battle Sprites):
                imgpath = "content/gfx/images/" + "default_{}_battle_sprite.png".format(self.gender)
            elif not imgpath:
                char_debug(str("Total failure while looking for image with %s tags!!!" % tags))
                imgpath = "content/gfx/interface/images/no_image.png"
            else: # We have an image, time to convert it to full path.
                imgpath = "/".join([self.path_to_imgfolder, imgpath])

            # FIXME regardless of type ???
            if label_cache:
                self.label_cache.append([tags, last_label, imgpath])

            if cache:
                self.cache.append([tags, imgpath])

            return ProportionalScale(imgpath, maxw, maxh)

        def get_img_from_cache(self, label):
            """
            Returns imgpath!!! from cache based on the label provided.
            """
            for entry in self.label_cache:
                if entry[1] == label:
                    return entry[2]

            return ""

        def clear_img_cache(self):
            self.cache = list()
            self.label_cache = list()

        def get_vnsprite(self, mood=("indifferent")):
            """
            Returns VN sprite based on characters height.
            Useful for random events that use NV sprites, heigth in unique events can be set manually.
            ***This is mirrored in galleries testmode, this method is not actually used.
            """
            return self.show("vnsprite", mood, resize=self.get_sprite_size())

        # AP + Training ------------------------------------------------------------->
        def restore_ap(self):
            ap = self.get_free_ap()
            if ap > 0 and "Injured" in self.effects:
                ap -= 1
            self.AP = ap

        def get_ap(self):
            ap = 0
            base = 35
            c = self.constitution
            while c >= base:
                c -= base
                ap += 1
                if base == 35:
                    base = 100
                else:
                    base = base * 2

            # if str(self.home) == "Studio Apartment":
            #     ap += 1

            self.setAP = self.baseAP + ap
            return self.setAP

        def get_free_ap(self):
            """
            For next day calculations only! This is not useful for the game events.
            """
            return self.get_ap() - self.reservedAP

        def take_ap(self, value):
            """
            Removes AP of the amount of value and returns True.
            Returns False if there is not enough Action points.
            This one is useful for game events.
            """
            if self.AP - value >= 0:
                self.AP -= value
                return True
            return False

        def auto_training(self, kind):
            """
            Training, right now by NPCs.
            *kind = is a string referring to the NPC
            """
            # Any training:
            self.exp += exp_reward(self, self.tier)

            if kind == "train_with_witch":
                self.magic += randint(1, 3)
                self.intelligence += randint(1, 2)
                mod_by_max(self, "mp", .5)
                if dice(50):
                    self.agility += randint(1, 2)

            if kind == "train_with_aine":
                self.charisma += randint(1, 3)
                mod_by_max(self, "vitality", .5)
                if dice(max(10, self.luck)):
                    self.reputation += 1
                    self.fame += 1
                if dice(1 + self.luck*.05):
                    self.luck += randint(1, 2)

            if kind == "train_with_xeona":
                self.attack += randint(1, 2)
                self.defence += randint(1, 2)
                if dice(50):
                    self.agility += 1
                mod_by_max(self, "health", .5)
                if dice(25 + max(5, int(self.luck/3))):
                    self.constitution += randint(1, 2)

        @property
        def npc_training_price(self):
            base = 250
            return base + base*self.tier

        # Logging and updating daily stats change on next day:
        def log_stats(self):
            # Devnote: It is possible to mod this as stats change
            # Could be messier to code though...
            self.stats.log = shallowcopy(self.stats.stats)
            self.stats.log["exp"] = self.exp
            self.stats.log["level"] = self.level
            for skill in self.SKILLS:
                self.stats.log[skill] = self.stats.get_skill(skill)

        # Items/Equipment related, Inventory is assumed!
        def eq_items(self):
            """Returns a list of all equiped items."""
            if hasattr(self, "eqslots"):
                return self.eqslots.values()
            else:
                return []

        def get_be_items(self):
            if not hasattr(self, "inventory"): # Mobs and such
                return {}

            be_items = OrderedDict()
            for item, amount in self.inventory.items.iteritems():
                if item.be:
                    be_items[item] = amount
            return be_items

        def get_owned_items_per_slot(self, slot):
            # figure out how many items actor owns:
            if self.eqslots.get(slot, None):
                amount = 1
            else:
                amount = 0

            slot_items = [i for i in self.inventory if i.slot == slot]

            return amount + len(slot_items)

        def add_item(self, item, amount=1):
            self.inventory.append(item, amount=amount)

        def remove_item(self, item, amount=1):
            self.inventory.remove(item, amount=amount)

        def remove_all_items(self):
            for i in self.inventory:
                self.inventory.remove(i.id, amount=has_items(i.id, [self]))

        def equip(self, item, remove=True, aeq_mode=False): # Equips the item
            """
            Equips an item to a corresponding slot or consumes it.
            remove: Removes from the inventory (Should be False if item is equipped from directly from a foreign inventory)
            aeq_mode: If we came here because of 'AI' auto equipment function or through players actions.
            **Note that the remove is only applicable when dealing with consumables, game will not expect any other kind of an item.
            """
            if isinstance(item, list):
                for it in item:
                    self.equip(it, remove, aeq_mode)
                return

            if item.slot not in self.eqslots:
                char_debug(str("Unknown Items slot: %s, %s" % (item.slot, self.__class__.__name__)))
                return

            # AEQ considerations:
            # Basically we manually mess with inventory and have
            # no way of knowing what was done to it.
            if not aeq_mode and item.slot != 'consumable':
                self.last_known_aeq_purpose = ''

            # This is a temporary check, to make sure nothing goes wrong:
            # Code checks during the equip method should make sure that the unique items never make it this far:
            if item.unique and item.unique != self.id:
                raise Exception("""A character attempted to equip unique item that was not meant for him/her.
                                   This is a flaw in game design, please report to out development team!
                                   Character: %s/%s, Item:%s""" % self.id, self.__class__, item.id)

            if item.sex not in ["unisex", self.gender]:
                char_debug(str("False character sex value: %s, %s, %s" % (item.sex, item.id, self.__class__.__name__)))
                return

            if item.slot == 'consumable':
                if item in self.consblock:
                    return

                if item.cblock:
                    self.consblock[item] = item.cblock
                if item.ctemp:
                    self.constemp[item] = item.ctemp
                if remove: # Needs to be infront of effect application for jumping items.
                    self.inventory.remove(item)
                self.apply_item_effects(item)
            elif item.slot == 'misc':
                if item in self.miscblock:
                    return

                if self.eqslots['misc']: # Unequip if equipped.
                    temp = self.eqslots['misc']
                    self.inventory.append(temp)
                    del(self.miscitems[temp])
                self.eqslots['misc'] = item
                self.miscitems[item] = item.mtemp
                if remove:
                    self.inventory.remove(item)
            elif item.slot == 'ring':
                if not self.eqslots['ring']:
                    self.eqslots['ring'] = item
                elif not self.eqslots['ring1']:
                    self.eqslots['ring1'] = item
                elif not self.eqslots['ring2']:
                    self.eqslots['ring2'] = item
                else:
                    self.apply_item_effects(self.eqslots['ring'], direction=False)
                    self.inventory.append(self.eqslots['ring'])
                    self.eqslots['ring'] = self.eqslots['ring1']
                    self.eqslots['ring1'] = self.eqslots['ring2']
                    self.eqslots['ring2'] = item
                self.apply_item_effects(item)
                if remove:
                    self.inventory.remove(item)
            else:
                # Any other slot:
                if self.eqslots[item.slot]: # If there is any item equipped:
                    self.apply_item_effects(self.eqslots[item.slot], direction=False) # Remove equipped item effects
                    self.inventory.append(self.eqslots[item.slot]) # Add unequipped item back to inventory
                self.eqslots[item.slot] = item # Assign new item to the slot
                self.apply_item_effects(item) # Apply item effects
                if remove:
                    self.inventory.remove(item) # Remove item from the inventory

        def unequip(self, item, slot=None, aeq_mode=False):
            # AEQ considerations:
            # Basically we manually mess with inventory and have
            # no way of knowing what was done to it.
            if not aeq_mode and item.slot != 'consumable':
                self.last_known_aeq_purpose = ''

            if item.slot == 'misc':
                self.eqslots['misc'] = None
                del(self.miscitems[item])
                self.inventory.append(item)
            elif item.slot == 'ring':
                if slot:
                    self.eqslots[slot] = None
                elif self.eqslots['ring'] == item:
                    self.eqslots['ring'] = None
                elif self.eqslots['ring1'] == item:
                    self.eqslots['ring1'] = None
                elif self.eqslots['ring2'] == item:
                    self.eqslots['ring2'] = None
                else:
                    raise Exception("Error while unequiping a ring! (Girl)")
                self.inventory.append(item)
                self.apply_item_effects(item, direction=False)
            else:
                # Other slots:
                self.inventory.append(item)
                self.apply_item_effects(item, direction=False)
                self.eqslots[item.slot] = None

        def equip_chance(self, item):
            """
            return a list of chances, between 0 and 100 if the person has a preference to equip this item.
            If None is returned the item should not be used. This only includes personal preferences,
            Other factors, like stat bonuses may also have to be taken into account.
            """
            if not can_equip(item, self):
                return None
            if not item.eqchance or item.badness >= 100:
                return None
            chance = []
            when_drunk = 30
            appetite = 50

            for trait in self.traits:
                if trait in trait_selections["badtraits"] and item in trait_selections["badtraits"][trait]:
                    return None

                if trait in trait_selections["goodtraits"] and item in trait_selections["goodtraits"][trait]:
                    chance.append(100)

                # Other traits:
                if trait == "Kamidere": # Vanity: wants pricy uncommon items, but only lasting ones(especially scrolls should be excluded)
                    if not (item.slot == "consumable"): 
                        chance.append((100 - item.chance + min(item.price/10, 100))/2)
                elif trait == "Tsundere": # stubborn: what s|he won't buy, s|he won't wear.
                    chance.append(100 - item.badness)
                elif trait == "Bokukko": # what the farmer don't know, s|he won't eat.
                    chance.append(item.chance)
                elif trait == "Heavy Drinker":
                    when_drunk = 45
                elif trait == "Always Hungry":
                    appetite += 20
                elif trait == "Slim":
                    appetite -= 10

            if item.type == "permanent": # Never pick permanent?
                return None

            if item.slot == "consumable": # Special considerations like food poisoning.
                if item in self.consblock or item in self.constemp:
                    return None
                if item.type == "alcohol":
                    if self.get_flag("drunk_counter", 0) >= when_drunk:
                        return None
                    if 'Depression' in self.effects:
                        chance.append(30 + when_drunk)
                elif item.type == "food":
                    food_poisoning = self.get_flag("food_poison_counter", 0)
                    if not food_poisoning:
                        chance.append(appetite)
                    else:
                        if food_poisoning >= 6:
                            return None
                        chance.append((6-food_poisoning)*9)
            elif item.slot == "misc":
                # If the item self-destructs or will be blocked after one use,
                # it's now up to the caller to stop after the first item of this kind that is picked.
                # no blocked misc items:
                if item in self.miscblock:
                    return None

            if item.tier:
                # only award tier bonus if it's reasonable.
                target_tier = self.tier
                item_tier = item.tier*2
                tier_bonus = max(item_tier - target_tier, 0)
                chance.append(tier_bonus*50)

            chance.append(item.eqchance)
            if item.badness:
                chance.append(-int(item.badness*.5))
            return chance

        def equip_for(self, purpose):
            """
            This method will try to auto-equip items for some purpose!
            """
            purpose = self.guess_aeq_purpose(purpose)

            self.last_known_aeq_purpose = purpose

            # if self.eqslots["weapon"]:
            #     self.unequip(self.eqslots["weapon"])

            aeq_debug("Auto Equipping for -- {} --".format(purpose))
            slots = store.EQUIP_SLOTS
            kwargs = AEQ_PURPOSES[purpose]
            aeq_debug("Auto Equipping Real Weapons: {} --!!".format(kwargs["real_weapons"]))
            return self.auto_equip(slots=slots, **kwargs)

        def auto_equip(self, target_stats, target_skills=None,
                       exclude_on_skills=None, exclude_on_stats=None,
                       slots=None, inv=None, real_weapons=False,
                       base_purpose=None, sub_purpose=None):
            """
            targetstats: expects a list of stats to pick the item
            targetskills: expects a list of skills to pick the item
            exclude_on_stats: items will not be used if stats in this list are being
                diminished by use of the item *Decreased the chance of picking this item
            exclude_on_skills: items will not be used if stats in this list are being
                diminished by use of the item *Decreased the chance of picking this item
            ==>   do not put stats/skills both in target* and in exclude_on_* !
            *default: All Stats - targetstats
            slots: a list of slots, contains just consumables by default
            inv: inventory to draw from.
            real_weapons: Do we equip real weapon types (*Broom is now considered a weapon as well)
            base_purpose: What we're equipping for, used to check vs item.pref_class (list)
            sub_purpose: Same as above but less weight (list)
                If not purpose is matched only 'Any' items will be used.


            So basically the way this works ATM is like this:
            We create a dict (weighted) of slot: [].

            In the list of values of weighted we add lists of weight values
            which we gather and item we gather them for. That is done in Stats.eval_inventory
            and pytChar.equip_chance methods. Later we come back here and sort out the results
            """

            # Prepare data:
            if not slots:
                slots = ["consumable"]
            if not inv:
                inv = self.inventory
            if not target_skills:
                target_skills = set()
            exclude_on_stats = set(exclude_on_stats) if exclude_on_stats else set()
            exclude_on_skills = set(exclude_on_skills) if exclude_on_skills else set()
            base_purpose = set(base_purpose) if base_purpose else set()
            sub_purpose = set(sub_purpose) if sub_purpose else set()

            # Go over all slots and unequip items:
            weighted = {}
            for s in slots:
                if s == "ring":
                    for r in ["ring", "ring1", "ring2"]:
                        item = self.eqslots[r]
                        if item:
                            self.unequip(item, aeq_mode=True)
                elif s == "consumable":
                    pass
                else:
                    item = self.eqslots[s]
                    if item:
                        self.unequip(item, aeq_mode=True)
                weighted[s] = []

            # allow a little stat/skill penalty, just make sure the net weight is positive.
            min_value = -5
            upto_skill_limit = False

            # traits that may influence the item selection process
            # This will never work, will it?????
            for t in self.traits:
                # bad eyesight may cause inclusion of items with more penalty
                if t == "Bad Eyesight":
                    min_value = -10
                # a clumsy person may also select items not in target skill
                elif t == "Clumsy":
                    target_skills = set(self.stats.skills.keys())
                # a stupid person may also select items not in target stat
                elif t == "Stupid":
                    target_stats = set(self.stats)
                elif t == "Smart":
                    upto_skill_limit = True

            # This looks like a shitty idea! Problem here is that we may care
            # about some stats more than others and this fucks that up completely.
            # exclude_on_stats = exclude_on_stats.union(target_stats)
            # exclude_on_skills = exclude_on_skills.union(target_skills)
            # self.stats.eval_inventory(container, weighted, chance_func=self.equip_chance,
            #                           upto_skill_limit=upto_skill_limit,
            #                           min_value=min_value, check_money=check_money,
            #                           limit_tier=limit_tier,
            #                           **kwargs)
            self.stats.eval_inventory(inv, weighted,
                                      target_stats, target_skills,
                                      exclude_on_skills, exclude_on_stats,
                                      chance_func=self.equip_chance,
                                      upto_skill_limit=upto_skill_limit,
                                      min_value=min_value,
                                      base_purpose=base_purpose,
                                      sub_purpose=sub_purpose,
                                      smart_ownership_limit=False)

            returns = list() # We return this list with all items used during the method.

            # Actually equip the items on per-slot basis:
            for slot, picks in weighted.iteritems():
                if not picks:
                    continue

                # We track one item, the one we think is best for all items,
                # except consumable and rings.
                selected = [0, None] if slot not in ("consumable", "ring") else []

                # Get the total weight for every item:
                for _weight, item in picks:
                    aeq_debug("(A-Eq=> {}) Slot: {} Item: {} ==> Weights: {}".format(
                                        self.name, item.slot, item.id, str(_weight)))
                    _weight = sum(_weight)

                    if _weight > 0:
                        if slot not in ("consumable", "ring"):
                            c0 = slot in ("weapon", "smallweapon")
                            c1 = not real_weapons and item.type != "tool"
                            if c0 and c1:
                                if DEBUG_AUTO_ITEM:
                                    msg = []
                                    msg.append("Skipping AE Weapons!")
                                    msg.append("Real Weapons: {}".format(real_weapons))
                                    if base_purpose:
                                        msg.append("Base: {}".format(base_purpose))
                                    if sub_purpose:
                                        msg.append("Sub: {}".format(sub_purpose))
                                    aeq_debug(" ".join(msg))
                                continue
                            if _weight > selected[0]:
                                selected = [_weight, item] # store weight and item for the highest weight
                        else:
                            selected.append([_weight, item])

                # For most slots, we just want to equip one item we selected:
                if slot not in ("consumable", "ring"):
                    item = selected[1]
                    if item:
                        inv.remove(item)
                        self.equip(item, remove=False, aeq_mode=True)
                        aeq_debug("     --> {} equipped {} to {}.".format(item.id, self.name, item.slot))
                        returns.append(item.id)
                    continue

                # Here we have a selected matrix with weights/items
                # consumables and rings that we may want to equip more than one of.
                selected.sort(key=itemgetter(0), reverse=True)
                for weight, item in selected:
                    if slot == "ring":
                        equipped_rings = []
                        for s in ["ring", "ring1", "ring2"]:
                            if isinstance(self.eqslots[s], Item):
                                equipped_rings.append(s)
                        if len(equipped_rings) == 3:
                            break

                    while 1:
                        # We got to run this calculation every time as the situation
                        # will change with every item consumed or every ring equipped
                        # it also conciders effects (Drunk, overeating)
                        result = self.equip_chance(item)
                        if result is None or sum(result) <= 0:
                            break

                        # If we don't have any more of the item, let's move on.
                        if item not in inv:
                            break

                        useful = False
                        for stat in target_stats:
                            if stat in item.max and item.max[stat] > 0:
                                useful = True
                                break
                            if stat in item.mod:
                                bonus = item.get_stat_eq_bonus(self.stats, stat)
                                needed = self.get_max(stat) - getattr(self, stat)
                                if needed*1.4 >= bonus: # We basically allow 40% waste
                                    useful = True
                                    break

                        if not useful: # Still here? Let's try skills:
                            for skill in item.mod_skills:
                                if skill in target_skills:
                                    useful = True
                                    break

                        if not useful:
                            break
                        else:
                            inv.remove(item)
                            self.equip(item, remove=False, aeq_mode=True)
                            returns.append(item.id)

                        # This is what we were missing! We can consume all the
                        # Consumables that we have as long as they're useful.
                        # But we need to equip only three rings tops:
                        equipped_rings = []
                        for s in ["ring", "ring1", "ring2"]:
                            if isinstance(self.eqslots[s], Item):
                                equipped_rings.append(s)
                        if len(equipped_rings) == 3:
                            break

            return returns

        def auto_buy_item(self, item, amount=1, equip=False):
            if isinstance(item, basestring):
                item = store.items[item]
            if item in store.all_auto_buy_items:
                amount = min(amount, round_int(self.gold/item.price))
                if amount != 0:
                    self.take_money(item.price*amount, reason="Items")
                    self.inventory.append(item, amount)
                    if equip:
                        self.equip(item)
                    return [item.id] * amount
            return []

        def guess_aeq_purpose(self, hint=None):
            """
            "Fighting": Generic purpose for combat.

            Other Options are:
             'Combat'
             'Barbarian'
             'Shooter'
             'Battle Mage'
             'Mage'

             'Casual'
             'Slave'

             'Striptease'
             'Sex'

             'Manager'
             'Service' (Maid)
             """

            occs = self.gen_occs
            bt = self.traits.basetraits
            purpose = None # Needs to be defaulted to something.

            if hint in store.AEQ_PURPOSES:
                purpose = hint
            elif hint == "Fighting":
                if traits["Shooter"] in bt:
                    purpose = "Shooter"
                elif "Caster" in occs and "Warrior" not in occs:
                    purpose = "Mage"
                elif len(set(["Warrior", "Caster"]).intersection(occs)) == 2:
                    purpose = "Battle Mage"
                elif "Combatant" in occs:
                    purpose = "Barbarian"
            else: # We just guess...
                if "Specialist" in occs:
                    purpose = "Manager"
                elif traits["Stripper"] in bt:
                    purpose = "Striptease"
                elif traits["Maid"] in bt:
                    purpose = "Service"
                elif traits["Prostitute"] in bt:
                    purpose = "Sex"
                elif "Caster" in occs and "Warrior" not in occs:
                    purpose = "Mage"
                elif len(set(["Warrior", "Caster"]).intersection(occs)) == 2:
                    purpose = "Battle Mage"
                elif traits["Shooter"] in bt:
                    purpose = "Shooter"
                elif "Combatant" in occs:
                    purpose = "Barbarian"
                else: # Safe option.
                    if DEBUG_AUTO_ITEM:
                        temp = "Supplied unknown aeq purpose: %s for %s, (Class: %s)" % (purpose,
                                                                    self.name, self.__class__.__name__)
                        temp += " ~Casual will be used."
                        aeq_debug(temp)
                    purpose = "Casual"

            return purpose

        def auto_buy(self, item=None, amount=1, slots=None, casual=False,
                     equip=False, container=None, purpose=None,
                     check_money=True, inv=None,
                     limit_tier=False, direct_equip=False,
                     smart_ownership_limit=True):
            """Gives items a char, usually by 'buying' those,
            from the container that host all items that can be
            sold in PyTFall.

            item: auto_buy specific item.
            amount: how many items to buy (used as a total instead of slots).
            slots: what slots to shop for, if None equipment slots and
                consumable will be used together with amount argument.
                Otherwise expects a dict of slot: amount.
            casual: If True, we also try to get a casual outfit for the character.
            equip: Equip the items after buying them, if true we equip whatever
                we buy, if set to purpose (Casual, Barbarian, etc.), we auto_equip
                for that purpose.
            container: Container with items or Inventory to shop from. If None
                we use.
            direct_equip: Special arg, only when building the char, we can just equip
                the item they 'auto_buy'.
            smart_ownership_limit: Limit the total amount of item char can buy.
                if char has this amount or more of that item:
                    3 of the same rings max.
                    1 per any eq_slot.
                    5 cons items max.
                item will not be concidered for purchase.

            Simplify!

            - Add items class_prefs and Casual.
            - Add casual as attr.
            - Maybe merge with give_tiered_items somehow!
            """
            if item:
                return self.auto_buy_item(item, amount, equip)

            if not container: # Pick the container we usually shop from:
                container = store.all_auto_buy_items
            if slots:
                slots_to_buy = slots
                amount = float("inf") # We will subtract 1 from here below
            else:
                slots_to_buy = {s: float("inf") for s in self.eqslots.keys()}

            # Create dict gather data, we gather slot: ([30, 50], item) types:
            weighted = {s: [] for s in slots_to_buy}

            if not purpose: # Let's see if we can get a purpose from last known auto equip purpose:
                purpose = self.guess_aeq_purpose(self.last_known_aeq_purpose)

            kwargs = AEQ_PURPOSES[purpose].copy()
            kwargs.pop("real_weapons", None)
            kwargs["base_purpose"] = set(kwargs["base_purpose"])
            kwargs["sub_purpose"] = set(kwargs["sub_purpose"])

            min_value = -10
            upto_skill_limit = False
            self.stats.eval_inventory(container, weighted, chance_func=self.equip_chance,
                                      upto_skill_limit=upto_skill_limit,
                                      min_value=min_value, check_money=check_money,
                                      limit_tier=limit_tier,
                                      smart_ownership_limit=smart_ownership_limit,
                                      **kwargs)

            rv = [] # List of item name strings we return in case we need to report
            # what happened in this method to player.
            for slot, _items in weighted.iteritems():
                if not _items:
                    continue

                per_slot_amount = slots_to_buy[slot]
                if slot in store.EQUIP_SLOTS:
                    amount, per_slot_amount, rv = self.ab_equipment(_items,
                                                   slot,
                                                   amount, per_slot_amount,
                                                   rv, equip, check_money,
                                                   direct_equip=direct_equip)
                elif slot == "consumable":
                    amount, per_slot_amount, rv = self.ab_consumables(_items,
                                                     slot,
                                                     amount, per_slot_amount,
                                                     rv, equip, check_money)
                if amount <= 0:
                    break

            if equip and not direct_equip:
                self.equip_for(purpose)

            return rv

        def ab_equipment(self, _items, slot, amount, per_slot_amount,
                         rv, equip, check_money, direct_equip=False):
            buy_amount = min(amount, per_slot_amount)
            amount_owned = self.get_owned_items_per_slot(slot)

            # We also want to set max amount to buy based on how many items
            # char already has (5 for rings, 2 for everything else)
            if not check_money: # special check, where we just force items.
                pass
            elif slot == "ring":
                buy_amount = min(buy_amount, 5)
            else:
                buy_amount = min(buy_amount, 2)

            # Check if we want to go on, skip needless calculations otherwise.
            if not buy_amount:
                return amount, per_slot_amount, rv

            # raise Exception(_items)
            _items = [(sum(weights), item) for weights, item in _items]
            _items.sort(key=itemgetter(0), reverse=True)
            for weight, item in _items:
                c0 = not check_money
                c1 = check_money and self.take_money(item.price, reason="Items")
                if c0 or c1:
                    buy_amount -= 1
                    amount -= 1
                    per_slot_amount -= 1
                    rv.append(item.id)

                    if direct_equip:
                        self.equip(item)
                    else:
                        self.inventory.append(item)

                if not buy_amount:
                    break

            return amount, per_slot_amount, rv

        def ab_consumables(self, _items, slot, amount, per_slot_amount,
                         rv, equip, check_money):
            buy_amount = min(amount, per_slot_amount)
            amount_owned = self.get_owned_items_per_slot(slot)

            # We also want to set max amount to buy based on how many items
            # char already has (5 for rings, 2 for everything else)
            if not check_money: # special check, where we just force items.
                pass
            else:
                buy_amount = min(buy_amount, 20)

            # Check if we want to go on, skip needless calculations otherwise.
            if not buy_amount:
                return amount, per_slot_amount, rv

            _items = [(sum(weights), item) for weights, item in _items]
            _items.sort(key=itemgetter(0), reverse=True)
            for weight, item in _items:
                # Do not buy more than 3 of any consumable item:
                if self.inventory[item] >= 3:
                    continue

                c0 = not check_money
                c1 = check_money and self.take_money(item.price, reason="Items")
                if c0 or c1:
                    buy_amount -= 1
                    amount -= 1
                    per_slot_amount -= 1
                    self.inventory.append(item)
                    rv.append(item.id)

                if not buy_amount:
                    break

            return amount, per_slot_amount, rv

        def auto_buy_old_but_optimized(self, item=None, amount=1, equip=False):
            """Older version of autobuy method which should be more optimized
            for performace than the new one.
            """
            if item:
                if isinstance(item, basestring):
                    item = store.items[item]
                if item in store.all_auto_buy_items:
                    amount = min(amount, round_int(self.gold/item.price))
                    if amount != 0:
                        self.take_money(item.price*amount, reason="Items")
                        self.inventory.append(item, amount)
                        if equip:
                            self.equip(item)
                        return [item.id] * amount
                return []

            # otherwise if it's just a request to buy an item randomly
            # make sure that she'll NEVER buy an items that is in badtraits
            skip = set()
            goodtraits = []
            for t in self.traits:
                if t in trait_selections["badtraits"]:
                    skip = skip.union(trait_selections["badtraits"][t])
                if t in trait_selections["goodtraits"]:
                    goodtraits.extend(trait_selections["goodtraits"][t])

            returns = []
            # high chance to try to buy an item she really likes based on traits
            if goodtraits and dice(80):
                i = random.randint(1, len(goodtraits))
                while i > 0:
                    pick = goodtraits[i-1]
                    # filter out too expensive ones
                    if pick.price <= self.gold:
                        # weapons not accepted for status
                        if self.status != "slave" or not (pick.slot in ("weapon", "smallweapon") or pick.type in ("armor", "scroll")):
                            # make sure that girl will never buy more than 5 of any item!
                            count = self.inventory[pick] if self.eqslots[pick.slot] != pick else self.inventory[pick] + 1
                            if pick.slot == "ring":
                                if self.eqslots["ring1"] == pick: count += 1
                                if self.eqslots["ring2"] == pick: count += 1

                                count += self.eqslots.values().count(pick)

                            penalty = pick.badness + count * 20
                            # badtraits skipped here (late test because the search takes time)
                            if penalty < 100 and dice(100 - penalty) and not pick in skip and self.take_money(pick.price, "Items"):
                                self.inventory.append(pick)
                                returns.append(pick.id)

                                amount -= 1
                                if amount == 0:
                                    return returns
                                break
                        i -= 1 # enough money, but not a lucky pick, just try next
                    else:
                        # if the pick is more than she can afford, next pick will be half as pricy
                        i = i // 2 # ..break if this floors to 0

            skip = skip.union(goodtraits) # the goodtrait items are only available in the 1st selection round

            # define selections
            articles = []
            # if she has no body slot items, she will try to buy a dress
            if not self.eqslots["body"] or all(i.slot != "body" for i in self.inventory):
                articles.append("body")

            # 30% (of the remaining) chance for her to buy any good restore item.
            if dice(30):
                articles.append("restore")

            # then a high chance to buy a snack, I assume that all chars can eat and enjoy normal food even if it's actually useless for them in terms of anatomy, since it's true for sex
            if ("Always Hungry" in self.traits and dice(80)) or self.vitality > 100 and dice(200 - self.vitality):
                articles.append("food")

            if amount > 2: # food doesn't count, it's not a big meal
                # define weighted choice for remaining articles - based on status and class
                choices = [("rest", 100)]
                dress_weight = 100

                # for slaves exclude all weapons, spells and armor
                if self.status != "slave":
                    if "Warrior" in self.occupations:
                        choices.append(("warrior", 100))
                        # if we still didn't pick the items, if the character has Warrior occupation, she may ignore dresses
                        dress_weight = 60 if self.occupations.issuperset(("SIW", "Server", "Specialist")) else 25
                    if "Caster" in self.occupations:
                        choices.append(("scroll", 25))

                choices.append(("dress", dress_weight))
                choice_sum = sum(w for c, w in choices)

                # add remaining choices, based on (normalized) weighted chances
                for r in random.sample(xrange(choice_sum), amount - 2):
                    for c, w in choices:
                        r -= w
                        if r <= 0:
                            articles.append(c)
                            break
            else:
                # oopsie, selected too many already, fixing that here
                articles = articles[:amount]

            for article in articles:
                wares = auto_buy_items[article]

                i = random.randint(1, len(wares))
                while i > 0:
                    price, pick = wares[i-1]
                    if price <= self.gold:
                        count = self.inventory[pick] if self.eqslots[pick.slot] != pick else self.inventory[pick] + 1
                        if pick.slot == "ring":
                            if self.eqslots["ring1"] == pick: count += 1
                            if self.eqslots["ring2"] == pick: count += 1
                        penalty = pick.badness + count * 20
                        if penalty < 100 and dice(100 - penalty) and not pick in skip and self.take_money(pick.price, "Items"):
                            self.inventory.append(pick)
                            returns.append(pick.id)
                            break
                        i -= 1
                    else:
                        i = i // 2

            return returns

        def load_equip(self, eqsave):
            # load equipment from save, if possible
            ordered = collections.OrderedDict(sorted(eqsave.items()))

            for slot, desired_item in ordered.iteritems():

                currently_equipped = self.eqslots[slot]
                if currently_equipped == desired_item:
                    continue

                # rings can be on other fingers. swapping them is allowed in any case
                if slot == "ring":

                    # if the wanted ring is on the next finger, or the next finger requires current ring, swap
                    if self.eqslots["ring1"] == desired_item or ordered["ring1"] == currently_equipped:
                        (self.eqslots["ring1"], self.eqslots[slot]) = (self.eqslots[slot], self.eqslots["ring1"])

                        currently_equipped = self.eqslots[slot]
                        if currently_equipped == desired_item:
                            continue

                if slot == "ring" or slot == "ring1":

                    if self.eqslots["ring2"] == desired_item or ordered["ring2"] == currently_equipped:
                        (self.eqslots["ring2"], self.eqslots[slot]) = (self.eqslots[slot], self.eqslots["ring2"])

                        currently_equipped = self.eqslots[slot]
                        if currently_equipped == desired_item:
                            continue

                # if we have something equipped, see if we're allowed to unequip
                if currently_equipped and equipment_access(self, item=currently_equipped, silent=True, allowed_to_equip=False):
                    self.unequip(item=currently_equipped, slot=slot)

                if desired_item:
                    # if we want something else and have it in inventory..
                    if not self.inventory[desired_item]:
                        continue

                    # ..see if we're allowed to equip what we want
                    if equipment_access(self, item=desired_item, silent=True):
                        if can_equip(item=desired_item, character=self, silent=False):
                            self.equip(desired_item)

        # Applies Item Effects:
        def apply_item_effects(self, item, direction=True, misc_mode=False):
            """Deals with applying items effects on characters.

            directions:
            - True: Apply Effects
            - False: Remove Effects
            """
            # Attacks/Magic -------------------------------------------------->
            # Attack Skills:
            attack_skills = getattr(item, "attacks", [])
            for battle_skill in attack_skills:
                if battle_skill not in store.battle_skills:
                    msg = "Item: {} applied invalid {} battle skill to: {} ({})!".format(item.id, battle_skill, self.fullname, self.__class__)
                    char_debug(msg)
                    continue
                else:
                    battle_skill = store.battle_skills[battle_skill]
                func = self.attack_skills.append if direction else self.attack_skills.remove
                func(battle_skill, False)
            if attack_skills:
                # Settle the default attack skill:
                default = self.default_attack_skill
                if len(self.attack_skills) > 1 and default in self.attack_skills:
                    self.attack_skills.remove(default)
                elif not self.attack_skills:
                    self.attack_skills.append(default)

            # Combat Spells:
            for battle_skill in item.add_be_spells + item.remove_be_spells:
                if battle_skill not in store.battle_skills:
                    msg = "Item: {} applied invalid {} battle skill to: {} ({})!".format(item.id, battle_skill, self.fullname, self.__class__)
                    char_debug(msg)
                    continue
                else:
                    battle_skill = store.battle_skills[battle_skill]
                if battle_skill.name in item.add_be_spells:
                    func = self.magic_skills.append if direction else self.magic_skills.remove
                else:
                    func = self.magic_skills.remove if direction else self.magic_skills.append
                func(battle_skill, False)

            # Taking care of stats: -------------------------------------------------->
            # Max Stats:
            for stat, value in item.max.items():
                # Reverse the value if appropriate:
                original_value = value
                if not direction:
                    value = -value

                if "Left-Handed" in self.traits and item.slot == "smallweapon":
                    self.stats.max[stat] += value*2
                elif "Left-Handed" in self.traits and item.slot == "weapon":
                    self.stats.max[stat] += int(value*.5)
                elif "Knightly Stance" in self.traits and stat == "defence" and item.type == "armor":
                    self.stats.max[stat] += int(value*1.3)
                elif "Berserk" in self.traits and stat == "defence":
                    self.stats.max[stat] += int(value*.5)
                elif "Berserk" in self.traits and stat == "attack":
                    self.stats.max[stat] += int(value*2)
                elif "Hollow Bones" in self.traits and stat == "agility" and original_value < 0:
                    pass
                elif "Elven Ranger" in self.traits and stat == "defence" and original_value < 0 and item.type in ["bow", "crossbow", "throwing"]:
                    pass
                elif "Sword Master" in self.traits and item.type == "sword":
                    self.stats.max[stat] += int(value*1.3)
                elif "Shield Master" in self.traits and item.type == "shield":
                    self.stats.max[stat] += int(value*1.3)
                elif "Dagger Master" in self.traits and item.type == "dagger":
                    self.stats.max[stat] += int(value*1.3)
                elif "Bow Master" in self.traits and item.type == "bow":
                    self.stats.max[stat] += int(value*1.3)
                else:
                    self.stats.max[stat] += value

            # Min Stats:
            for stat, value in item.min.items():
                # Reverse the value if appropriate:
                original_value = value
                if not direction:
                    value = -value

                if "Left-Handed" in self.traits and item.slot == "smallweapon":
                    self.stats.min[stat] += value*2
                elif "Left-Handed" in self.traits and item.slot == "weapon":
                    self.stats.min[stat] += int(value*.5)
                elif "Knightly Stance" in self.traits and stat == "defence":
                    self.stats.min[stat] += int(value*1.3)
                elif "Berserk" in self.traits and stat == "defence":
                    self.stats.min[stat] += int(value*.5)
                elif "Berserk" in self.traits and stat == "attack":
                    self.stats.min[stat] += int(value*2)
                elif "Hollow Bones" in self.traits and stat == "agility" and original_value < 0:
                    pass
                elif "Elven Ranger" in self.traits and stat == "defence" and original_value < 0 and item.type in ["bow", "crossbow", "throwing"]:
                    pass
                elif "Sword Master" in self.traits and item.type == "sword":
                    self.stats.min[stat] += int(value*1.3)
                elif "Dagger Master" in self.traits and item.type == "dagger":
                    self.stats.min[stat] += int(value*1.3)
                elif "Shield Master" in self.traits and item.type == "shield":
                    self.stats.min[stat] += int(value*1.3)
                elif "Bow Master" in self.traits and item.type == "bow":
                    self.stats.min[stat] += int(value*1.3)
                else:
                    self.stats.min[stat] += value

            # Items Stats:
            for stat, value in item.mod.items():
                # Reverse the value if appropriate:
                original_value = value
                if not direction:
                    value = -value

                # This health thing could be handled differently (note for the post-beta refactor)
                if stat == "health" and self.health + value <= 0:
                    self.health = 1 # prevents death by accident...
                    continue

                if original_value < 0:
                    condition = True
                elif item.statmax and getattr(self, stat) >= item.statmax:
                    condition = False
                else:
                    condition = True

                if condition:
                    if stat == "gold":
                        if misc_mode and self.status == "slave":
                            temp = hero
                        else:
                            temp = self
                        if value < 0:
                            temp.take_money(-value, reason="Upkeep")
                        else:
                            temp.add_money(value, reason="Items")
                    elif stat == "exp":
                        self.exp += value
                    elif stat in ['health', 'mp', 'vitality', 'joy'] or (item.slot in ['consumable', 'misc'] and not (item.slot == 'consumable' and item.ctemp)):
                        if direction:
                            if 'Fast Metabolism' in self.effects and item.type == "food":
                                self.mod_stat(stat, (2*value))
                            elif "Summer Eternality" in self.traits and stat == "health" and value > 0:
                                self.mod_stat(stat, (int(.35*value)))
                            elif "Winter Eternality" in self.traits and stat == "mp" and value > 0:
                                self.mod_stat(stat, (int(.35*value)))
                            elif "Effective Metabolism" in self.traits and stat == "vitality" and value > 0:
                                if item.type == "food":
                                    self.mod_stat(stat, (int(2*value)))
                                else:
                                    self.mod_stat(stat, (int(1.5*value)))
                            elif "Magical Kin" in self.traits and stat == "mp" and value > 0:
                                if item.type == "alcohol":
                                    self.mod_stat(stat, (int(2*value)))
                                else:
                                    self.mod_stat(stat, (int(1.5*value)))
                            else:
                                self.mod_stat(stat, value)
                        else:
                            self.mod_stat(stat, value)
                    else:
                        if "Left-Handed" in self.traits and item.slot == "smallweapon":
                            self.stats.imod[stat] += value*2
                        elif "Left-Handed" in self.traits and item.slot == "weapon":
                            self.stats.imod[stat] += int(value*.5)
                        elif "Knightly Stance" in self.traits and stat == "defence":
                            self.stats.imod[stat] += int(value*1.3)
                        elif "Berserk" in self.traits and stat == "defence":
                            self.stats.imod[stat] += int(value*.5)
                        elif "Berserk" in self.traits and stat == "attack":
                            self.stats.imod[stat] += int(value*2)
                        elif "Hollow Bones" in self.traits and stat == "agility" and original_value < 0:
                            pass
                        elif "Elven Ranger" in self.traits and stat == "defence" and original_value < 0 and item.type in ["bow", "crossbow", "throwing"]:
                            pass
                        elif "Sword Master" in self.traits and item.type == "sword":
                            self.stats.imod[stat] += int(value*1.3)
                        elif "Dagger Master" in self.traits and item.type == "dagger":
                            self.stats.imod[stat] += int(value*1.3)
                        elif "Shield Master" in self.traits and item.type == "shield":
                            self.stats.imod[stat] += int(value*1.3)
                        elif "Bow Master" in self.traits and item.type == "bow":
                            self.stats.imod[stat] += int(value*1.3)
                        else:
                            try:
                                self.stats.imod[stat] += value
                            except:
                                raise Exception(item.id, stat)

            # Special modifiers based off traits:
            temp = ["smallweapon", "weapon", "body", "cape", "feet", "wrist", "head"]
            if "Royal Assassin" in self.traits and item.slot in temp:
                value = int(item.price*.01) if direction else -int(item.price*.01)
                self.stats.max["attack"] += value
                self.mod_stat("attack", value)
            elif "Armor Expert" in self.traits and item.slot in temp:
                value = int(item.price*.01) if direction else -int(item.price*.01)
                self.stats.max["defence"] += value
                self.mod_stat("defence", value)
            elif "Arcane Archer" in self.traits and item.type in ["bow", "crossbow", "throwing"]:
                max_val = int(item.max["attack"]*.5) if direction else -int(item.max["attack"]*.5)
                imod_val = int(item.mod["attack"]*.5) if direction else -int(item.mod["attack"]*.5)
                self.stats.max["magic"] += max_val
                self.stats.imod["magic"] += imod_val
            if direction and "Recharging" in self.traits and item.slot == 'consumable' \
                and not item.ctemp and not("mp" in item.mod):
                self.mod_stat("mp", 10)

            # Skills:
            for skill, data in item.mod_skills.items():
                if not self.stats.is_skill(skill):
                    msg = "'%s' item tried to apply unknown skill: %s!"
                    char_debug(str(msg % (item.id, skill)))
                    continue

                if not direction:
                    data = [-i for i in data]

                if not item.skillmax or (self.get_skill(skill) < item.skillmax): # Multi messes this up a bit.
                    s = self.stats.skills[skill] # skillz
                    sm = self.stats.skills_multipliers[skill] # skillz muplties
                    sm[0] += data[0]
                    sm[1] += data[1]
                    sm[2] += data[2]
                    s[0] += data[3]
                    s[1] += data[4]

            # Traits:
            for trait in item.removetraits + item.addtraits:
                if trait not in store.traits:
                    char_debug("Item: {} has tried to apply an invalid trait: {}!".format(item.id, trait))
                    continue

                if item.slot not in ['consumable', 'misc'] or (item.slot == 'consumable' and item.ctemp):
                    truetrait = False
                else:
                    truetrait = True

                if trait in item.addtraits:
                    func = self.apply_trait if direction else self.remove_trait
                else:
                    func = self.remove_trait if direction else self.apply_trait
                func(store.traits[trait], truetrait)

            # Effects:
            if hasattr(self, "effects"):
                if direction:
                    if item.slot == 'consumable' and item.type == 'food':
                        self.up_counter("food_poison_counter", 1)
                        if self.get_flag("food_poison_counter", 0) >= 7 and not ('Food Poisoning' in self.effects):
                            self.enable_effect('Food Poisoning')

                    if item.slot == 'consumable' and item.type == 'alcohol':
                        self.up_counter("drunk_counter", item.mod["joy"])
                        if self.get_flag("drunk_counter", 0) >= 35 and not ('Drunk' in self.effects):
                            self.enable_effect('Drunk')
                        elif 'Drunk' in self.effects and self.AP > 0 and not ('Drinker' in self.effects):
                            self.AP -=1

                for effect in item.addeffects:
                    if direction and not effect in self.effects:
                        self.enable_effect(effect)
                    elif not direction and effect in self.effects:
                        self.disable_effect(effect)

                for effect in item.removeeffects:
                    if direction and effect in self.effects:
                        self.disable_effect(effect)

            # Jump away from equipment screen if appropriate:
            if getattr(store, "eqtarget", None) is self:
                if item.jump_to_label:
                    renpy.scene(layer="screens") # hides all screens
                    eqtarget.inventory.set_page_size(15)
                    hero.inventory.set_page_size(15)
                    jump(item.jump_to_label)

        def item_counter(self):
            # Timer to clear consumable blocks
            for item in self.consblock.keys():
                self.consblock[item] -= 1
                if self.consblock[item] <= 0:
                    del(self.consblock[item])

            # Timer to remove effects of a temp consumer items
            for item in self.constemp.keys():
                self.constemp[item] -= 1
                if self.constemp[item] <= 0:
                    self.apply_item_effects(item, direction=False)
                    del(self.constemp[item])

            # Counter to apply misc item effects and settle misc items conditions:
            for item in self.miscitems.keys():
                self.miscitems[item] -= 1
                if self.miscitems[item] <= 0:
                    # Figure out if we can pay the piper:
                    for stat, value in item.mod.items():
                        if value < 0:
                            if stat == "exp":
                                pass
                            elif stat == "gold":
                                if self.status == "slave":
                                    temp = hero
                                else:
                                    temp = self
                                if temp.gold + value < 0:
                                    break
                            else:
                                if getattr(self, stat) + value < self.stats.min[stat]:
                                    break
                    else:
                        self.apply_item_effects(item, misc_mode=True)

                        # For Misc item that self-destruct:
                        if item.mdestruct:
                            del(self.miscitems[item])
                            self.eqslots['misc'] = False
                            if not item.mreusable:
                                self.miscblock.append(item)
                            return

                        if not item.mreusable:
                            self.miscblock.append(item)
                            self.unequip(item)
                            return

                    self.miscitems[item] = item.mtemp

        # Trait methods *now for all characters:
        # Traits methods
        def apply_trait(self, trait, truetrait=True): # Applies trait effects
            self.traits.apply(trait, truetrait=truetrait)

        def remove_trait(self, trait, truetrait=True):  # Removes trait effects
            if 'Chastity' in self.effects and trait.id == "Virgin":
                pass
            else:
                self.traits.remove(trait, truetrait=truetrait)

        # Effects:
        ### Effects Methods
        def enable_effect(self, name, **kwargs):
            if name == "Poisoned" and "Artificial Body" not in self.traits:
                ss_mod = kwargs.get("ss_mod", None)
                duration = kwargs.get("duration", 10)
                if ss_mod is None:
                    ss_mod = {}
                    ss_mod["health"] = -locked_random("randint", 5, 10)
                obj = CharEffect(name, duration=duration, ss_mod=ss_mod)
                obj.enable(self)
            elif name == "Unstable":
                ss_mod = {}
                ss_mod["joy"] = randint(20, 30) if randrange(2) else -randint(20, 30)
                obj = CharEffect(name, duration=randint(2, 4), ss_mod=ss_mod)
                obj.enable(self)
            elif name == "Down with Cold":
                ss_mod = {}
                ss_mod["health"] = -randint(2, 5)
                ss_mod["vitality"] = -randint(5, 15)
                ss_mod["joy"] = -randint(2, 5)
                duration = locked_random("randint", 6, 14)
                obj = CharEffect(name, duration=duration, ss_mod=ss_mod)
                obj.enable(self)
            elif name == "Food Poisoning":
                ss_mod = {}
                ss_mod["health"] = -randint(8, 12)
                ss_mod["vitality"] = -randint(10, 25)
                ss_mod["joy"] = -randint(8, 12)
                duration = locked_random("randint", 6, 14)
                obj = CharEffect(name, duration=duration, ss_mod=ss_mod)
                obj.enable(self)
            else:
                ss_mod = kwargs.get("ss_mod", {})
                duration = kwargs.get("duration", 10)
                obj = CharEffect(name, ss_mod, duration)
                obj.enable(self)

        def disable_effect(self, name):
            effect = self.effects.get(name, None)
            if effect is not None:
                effect.end(self)

        # Relationships:
        def is_friend(self, char):
            return char in self.friends

        def is_lover(self, char):
            return char in self.lovers

        # Post init and ND.
        def init(self):
            # Normalize character
            if not self.fullname:
                self.fullname = self.name
            if not self.nickname:
                self.nickname = self.name

            # AP restore:
            self.restore_ap()

            # Always init the tiers:
            self.recalculate_tier()

            # add Character:
            if not self.say:
                self.update_sayer()

            if not self.origin:
                self.origin = choice(["Alkion", "PyTFall", "Crossgate"])

        def next_day(self):
            self.jobpoints = 0
            self.clear_img_cache()

            self.del_flag("food_poison_counter")
            self.del_flag("drunk_counter")

        def nd_auto_train(self, txt):
            if self.flag("train_with_witch"):
                if self.get_free_ap():
                    if hero.take_money(self.npc_training_price, "Training"):
                        self.auto_training("train_with_witch")
                        self.reservedAP += 1
                        txt.append("\nSuccessfully completed scheduled training with Abby the Witch!")
                    else:
                        txt.append("\nNot enough funds to train with Abby the Witch. Auto-Training will be disabled!")
                        self.del_flag("train_with_witch")
                        self.remove_trait(traits["Abby Training"])
                else:
                    s0 = "\nNot enough AP left in reserve to train with Abby the Witch."
                    s1 = "Auto-Training will not be disabled."
                    s2 = "{color=[red]}This character will start next day with 0 AP!){/color}"
                    txt.append(" ".join([s0, s1, s2]))

            if self.flag("train_with_aine"):
                if self.get_free_ap():
                    if hero.take_money(self.npc_training_price, "Training"):
                        self.auto_training("train_with_aine")
                        self.reservedAP += 1
                        txt.append("\nSuccessfully completed scheduled training with Aine!")
                    else:
                        txt.append("\nNot enought funds to train with Aine. Auto-Training will be disabled!")
                        self.del_flag("train_with_aine")
                        self.remove_trait(traits["Aine Training"])
                else:
                    s0 = "\nNot enough AP left in reserve to train with Aine."
                    s1 = "Auto-Training will not be disabled."
                    s2 = "{color=[red]}This character will start next day with 0 AP!){/color}"
                    txt.append(" ".join([s0, s1, s2]))

            if self.flag("train_with_xeona"):
                if self.get_free_ap():
                    if hero.take_money(self.npc_training_price, "Training"):
                        self.auto_training("train_with_xeona")
                        self.reservedAP += 1
                        txt.append("\nSuccessfully completed scheduled combat training with Xeona!")
                    else:
                        txt.append("\nNot enough funds to train with Xeona. Auto-Training will be disabled!")
                        self.remove_trait(traits["Xeona Training"])
                        self.del_flag("train_with_xeona")
                else:
                    s0 = "\nNot enough AP left in reserve to train with Xeona."
                    s1 = "Auto-Training will not be disabled."
                    s2 = "{color=[red]}This character will start next day with 0 AP!){/color}"
                    txt.append(" ".join([s0, s1, s2]))

        def nd_log_report(self, txt, img, flag_red, type='girlndreport'):
            # Change in stats during the day:
            charmod = dict()
            for stat, value in self.stats.log.items():
                if stat == "exp":
                    charmod[stat] = self.exp - value
                elif stat == "level":
                    charmod[stat] = self.level - value
                elif stat in self.SKILLS:
                    charmod[stat] = round_int(self.stats.get_skill(stat) - value)
                else:
                    charmod[stat] = self.stats.stats[stat] - value

            # Create the event:
            evt = NDEvent()
            evt.red_flag = flag_red
            evt.charmod = charmod
            evt.type = type
            evt.char = self
            evt.img = img
            evt.txt = txt
            NextDayEvents.append(evt)


    class Mob(PytCharacter):
        """
        I will use ArenaFighter for this until there is a reason not to...
        """
        def __init__(self):
            super(Mob, self).__init__(arena=True)

            # Basic Images:
            self.portrait = ""
            self.battle_sprite = ""
            self.combat_img = ""

            self.controller = BE_AI(self)

        @property
        def besprite_size(self):
            webm_spites = mobs[self.id].get("be_webm_sprites", None)
            if webm_spites:
                return webm_spites["idle"][1]
            return get_size(self.besprite)

        def has_image(self, *tags):
            """
            Returns True if image is found.
            """
            return True

        def show(self, *args, **kwargs):
            what = args[0]
            resize = kwargs.get("resize", (100, 100))
            cache = kwargs.get("cache", True)

            if what in ["battle", "fighting"]:
                what = "combat"
            if what == "portrait":
                what = self.portrait
            elif what == "battle_sprite":
                # See if we can find idle animation for this...
                webm_spites = mobs[self.id].get("be_webm_sprites", None)
                if webm_spites:
                    return ImageReference(webm_spites["idle"][0])
                else:
                    what = self.battle_sprite
            elif what == "combat" and self.combat_img:
                what = self.combat_img
            else:
                what = self.battle_sprite

            if isinstance(what, ImageReference):
                return prop_resize(what, resize[0], resize[1])
            else:
                return ProportionalScale(what, resize[0], resize[1])

        def restore_ap(self):
            self.AP = self.baseAP + int(self.constitution / 20)

        def init(self):
            # Normalize character
            if not self.fullname:
                self.fullname = self.name
            if not self.nickname:
                self.nickname = self.name

            # If there are no basetraits, we add Warrior by default:
            if not self.traits.basetraits:
                self.traits.basetraits.add(traits["Warrior"])
                self.apply_trait(traits["Warrior"])

            self.arena_willing = True # Indicates the desire to fight in the Arena
            self.arena_permit = True # Has a permit to fight in main events of the arena.
            self.arena_active = True # Indicates that girl fights at Arena at the time.

            if not self.portrait:
                self.portrait = self.battle_sprite

            super(Mob, self).init()


    class Player(PytCharacter):
        def __init__(self):
            super(Player, self).__init__(arena=True, inventory=True, effects=True)

            self.img_db = None
            self.id = "mc" # Added for unique items methods.
            self.name = 'Player'
            self.fullname = 'Player'
            self.nickname = 'Player'
            self._location = locations["Streets"]
            self.status = "free"
            self.gender = "male"

            self.autoequip = False # Player can manage his own shit.

            self._buildings = list()
            self._chars = list()

            self.fin = Finances(self)

            # Team:
            self.team = Team(implicit=[self])
            self.team.name = "Player Team"

            # Exp Bar:
            self.exp_bar = ExpBarController(self)

            self.autocontrol = {
            "Rest": False,
            "Tips": False,
            "SlaveDriver": False,
            "Acts": {"normalsex": True, "anal": True, "blowjob": True, "lesbian": True},
            "S_Tasks": {"clean": True, "bar": True, "waitress": True},
            }

        # Girls/Brothels/Buildings Ownership
        @property
        def buildings(self):
            """
            Returns a list of all buildings in heros ownership.
            """
            return self._buildings

        @property
        def dirty_buildings(self):
            """
            The buildings that can be cleaned.
            """
            return [building for building in self.buildings if isinstance(building, BuildingStats)]

        @property
        def famous_buildings(self):
            """
            The buildings that have reputation.
            """
            return [building for building in self.buildings if isinstance(building, FamousBuilding)]

        @property
        def upgradable_buildings(self):
            """
            The buildings that can be upgraded.
            """
            return [b for b in self.buildings if isinstance(b, UpgradableBuilding)]

        def add_building(self, building):
            if building not in self._buildings:
                self._buildings.append(building)

            self.sort_buildings()

        def sort_buildings(self):
            workable = []
            habitable = []
            rest = []

            for b in self._buildings:
                if isinstance(b, UpgradableBuilding):
                    if b.workable:
                        workable.append(b)
                    elif b.habitable and not b.workable:
                        habitable.append(b)
                    else:
                        rest.append(b)
                else:
                    rest.append(b)

            workable.sort(key=attrgetter("tier"), reverse=True)
            habitable.sort(key=attrgetter("tier"), reverse=True)

            self._buildings = workable + habitable + rest


        def remove_building(self, building):
            if building in self._buildings:
                self._buildings.remove(building)
            else:
                raise Exception("{} building does not belong to the player!".format(str(building)))

        @property
        def chars(self):
            """List of owned girls
            :returns: @todo
            """
            return self._chars

        def add_char(self, char):
            if char not in self._chars:
                self._chars.append(char)

        def remove_char(self, char):
            if char in self._chars:
                self._chars.remove(char)
            else:
                raise Exception, "This char (ID: %s) is not in service to the player!!!" % self.id

        # ----------------------------------------------------------------------------------
        def nd_pay_taxes(self, txt, flag_red):
            txt.append("\nIt's time to pay taxes!")
            ec = store.pytfall.economy

            if self.fin.income_tax_debt:
                temp = "Your standing income tax debt to the government: %d Gold." % self.fin.income_tax_debt
                txt.append(temp)

            # Income Taxes:
            income, tax = self.fin.get_income_tax(log_finances=True)
            temp = "Over the past week your taxable income amounted to: {color=[gold]}%d Gold{/color}.\n" % income
            txt.append(temp)
            if income < 5000:
                s0 = "You may consider yourself lucky as any sum below 5000 Gold is not taxable."
                s1 = "Otherwise the government would have totally ripped you off :)"
                temp = " ".join([s0, s1])
                txt.append(temp)

            if tax or self.fin.income_tax_debt:
                temp = "Your income tax for this week is %d. " % tax
                txt.append(temp)

                self.fin.income_tax_debt += tax
                if tax != self.fin.income_tax_debt:
                    temp = "That makes it a total amount of: %d Gold. " % self.fin.income_tax_debt
                    txt.append(temp)

                if self.take_money(self.fin.income_tax_debt, "Income Taxes"):
                    temp = "\nYou were able to pay that in full!\n"
                    txt.append(temp)
                    self.fin.income_tax_debt = 0
                else:
                    flag_red = True
                    s0 = "\nYou've did not have enough money..."
                    s1 = "Be advised that if your debt to the government reaches 50000,"
                    s2 = "they will indiscriminately confiscate your property until it is paid in full."
                    s3 = "(meaning that you will loose everything that you own at repo prices).\n"
                    else_srt = " ".join([s0, s1, s2, s3])

            # Property taxes:
            temp = choice(["\nWe're not done yet...\n",
                           "\nProperty tax:\n",
                           "\nProperty taxes next!\n"])
            txt.append(temp)
            b_tax, s_tax, tax = self.fin.get_property_tax(log_finances=True)
            if b_tax:
                temp = "Real Estate Tax: %d Gold.\n" % b_tax
                txt.append(temp)
            if s_tax:
                temp = "Slave Tax: %d Gold.\n" % s_tax
                txt.append(temp)
            if tax:
                temp = "\nThat makes it a total of {color=[gold]}%d Gold{/color}" % tax
                txt.append(temp)
                self.fin.property_tax_debt += tax
                if self.fin.property_tax_debt != tax:
                    s0 = " Don't worry, we didn't forget about your debt of %d Gold either." % self.fin.property_tax_debt
                    s1 = "Yeap, there are just the two inevitable things in life:"
                    s2 = "Death and Paying your tax on Monday!"
                    temp = " ".join([s0, s1, s2])
                    txt.append(temp)

                if self.take_money(self.fin.property_tax_debt, "Property Taxes"):
                    temp = "\nYou settled the payment successfully, but your wallet feels a lot lighter now :)\n"
                    txt.append(temp)
                    self.fin.property_tax_debt = 0
                else:
                    temp = "\nYour payment failed..."
                    txt.append(temp)
            else:
                temp = "\nHowever, you do not have enough Gold...\n"
                txt.append(temp)

            total_debt = self.fin.income_tax_debt + self.fin.property_tax_debt
            if total_debt:
                temp = "\n\nYour current total debt to the government is {color=[gold]}%d Gold{/color}!" % total_debt
                txt.append(temp)
            if total_debt > 50000:
                flag_red = True
                temp = " {color=[red]}... And you're pretty much screwed because it is above 50000!{/color} Your property will now be confiscated!"
                txt.append(temp)

                slaves = [c for c in self.chars if c.status == "slave"]
                all_properties = slaves + self.upgradable_buildings
                shuffle(all_properties)
                while total_debt and all_properties:
                    cr = ec.confiscation_range
                    multiplier = round(uniform(*cr), 2)
                    confiscate = all_properties.pop()

                    if isinstance(confiscate, Building):
                        price = confiscate.get_price()
                        if self.home == confiscate:
                            self.home = locations["Streets"]
                        if self.location == confiscate:
                            set_location(self, None)
                        self.remove_building(confiscate)
                        retire_chars_from_location(self.chars, confiscate)
                    elif isinstance(confiscate, Char):
                        price = confiscate.fin.get_price()
                        hero.remove_char(confiscate)
                        if confiscate in self.team:
                            self.team.remove(confiscate)
                        # locations:
                        confiscate.home = pytfall.sm
                        confiscate.workplace = None
                        confiscate.action = None
                        set_location(confiscate, char.home)

                    temp = choice(["\n{} has been confiscated for a price of {}% of the original value. ".format(
                                                                                    confiscate.name, multiplier*100),
                                   "\nThose sobs took {} from you! ".format(confiscate.name),
                                   "\nYou've lost {}! If only you were better at managing your business... ".format(
                                                                                    confiscate.name)])
                    txt.append(temp)
                    total_debt = total_debt - int(price*multiplier)
                    if total_debt > 0:
                        temp = "You are still required to pay %s Gold." % total_debt
                        txt.append(temp)
                    else:
                        temp = "Your debt has been paid in full!"
                        txt.append(temp)
                        if total_debt <= 0:
                            total_debt = -total_debt
                            temp = " You get a sum of %d Gold returned to you from the last repo!" % total_debt
                            txt.append(temp)
                            hero.add_money(total_debt, reason="Tax Returns")
                            total_debt = 0
                    if not all_properties and total_debt:
                        temp = "\n You do not own anything that might be repossessed by the government..."
                        txt.append(temp)
                        temp = " You've been declared bankrupt and your debt is now Null and Void!"
                        txt.append(temp)
                    self.fin.income_tax_debt = 0
                    self.fin.property_tax_debt = 0

            return flag_red

        def next_day(self):
            img = 'profile'
            txt = []
            flag_red = False

            # -------------------->
            txt.append("Hero Report:\n\n")

            # Home location nd mods:
            loc = self.home
            try:
                mod = loc.daily_modifier
            except:
                raise Exception("Home location without daily_modifier field was set. ({})".format(loc))

            if mod > 0:
                txt.append("You've comfortably spent a night.")
            elif mod < 0:
                flag_red = True
                txt.append("{color=[red]}You should find some shelter for the night... it's not healthy to sleep outside.{/color}\n")

            for stat in ("health", "mp", "vitality"):
                mod_by_max(self, stat, mod)

            # Training with NPCs --------------------------------------->
            self.nd_auto_train(txt)

            # Taxes:
            if all([calendar.weekday() == "Monday",
                    day != 1]):
                flag_red = self.nd_pay_taxes(txt, flag_red)

            if self.arena_rep == -500 and self.arena_permit:
                txt.append("")
                txt.append("{color=[red]}You've lost your Arena Permit... Try not to suck at it so much!{/color}")
                self.arena_permit = False
                self.arena_rep = 0
                flag_red = True
                txt.append("")

            # Finances related ---->
            self.fin.next_day()

            # ------------->
            self.item_counter()
            self.restore_ap()
            self.reservedAP = 0
            self.log_stats()

            # ------------>
            self.nd_log_report(txt, img, flag_red, type='mcndreport')

            self.arena_stats = dict()

            super(Player, self).next_day()


    class Char(PytCharacter):
        # wranks = {
                # 'r1': dict(id=1, name=('Rank 1: Kirimise', '(Almost beggar)'), price=0),
                # 'r2': dict(id=2, name=("Rank 2: Heya-Mochi", "(Low-class prostitute)"), price=1000, ref=45, exp=10000),
                # 'r3': dict(id=3, name=("Rank 3: Zashiki-Mochi", "(Middle-class Prostitute"), price=3000, ref=60, exp=25000),
                # 'r4': dict(id=4, name=("Rank 4: Tsuke-Mawashi", "(Courtesan)"), price=5000, ref=80, exp=50000),
                # 'r5': dict(id=5, name=("Rank 5: Chûsan", "(Famous)"), price=7500, ref=100, exp=100000),
                # 'r6': dict(id=6, name=("Rank 6: Yobidashi", "(High-Class Courtesan)"), price=10000, ref=120, exp=250000),
                # 'r7': dict(id=7, name=("Rank 7: Koshi", "(Nation famous)"), price=25000, ref=200, exp=400000),
                # 'r8': dict(id=8, name=("Rank 8: Tayu", "(Legendary)"), price=50000, ref=250, exp=800000)
            # }
        RANKS = {}
        def __init__(self):
            super(Char, self).__init__(arena=True, inventory=True, effects=True)
            # Game mechanics assets
            self.gender = 'female'
            self.desc = ""
            self.status = ""
            self._location = "slavemarket"

            self.rank = 1

            self.baseAP = 2

            # Can set character specific event for recapture
            self.runaway_look_event = "escaped_girl_recapture"

            self.nd_ap = 0 # next day action points
            self.gold = 0
            self.price = 500
            self.alive = True

            # Image related:
            # self.picture_base = dict()

            self.nickname = ""
            self.fullname = ""

            # Relays for game mechanics
            # courseid = specific course id girl is currently taking -- DEPRECATED: Training now uses flags
            # wagemod = Percentage to change wage payout
            self.wagemod = 100

            # Unhappy/Depressed counters:
            self.days_unhappy = 0
            self.days_depressed = 0

            # Trait assets
            self.init_traits = list() # List of traits to be enabled on game startup (should be deleted in init method)

            # Autocontrol of girls action (during the next day mostly)
            # TODO lt: Enable/Fix (to work with new skills/traits) this!
            # TODO lt: (Move to a separate instance???)
            self.autocontrol = {
            "Rest": True,
            "Tips": False,
            "SlaveDriver": False,
            "Acts": {"normalsex": True, "anal": True, "blowjob": True, "lesbian": True},
            "S_Tasks": {"clean": True, "bar": True, "waitress": True},
            }

            # Auto-equip/buy:
            self.autobuy = False
            self.autoequip = False
            self.given_items = dict()

            self.txt = list()
            self.fin = Finances(self)

            # Exp Bar:
            self.exp_bar = ExpBarController(self)

        def init(self):
            """Normalizes after __init__"""

            # Names:
            if not self.name:
                self.name = self.id
            if not self.fullname:
                self.fullname = self.name
            if not self.nickname:
                self.nickname = self.name

            # Base Class | Status normalization:
            if not self.traits.basetraits:
                pattern = create_traits_base(self.GEN_OCCS)
                for i in pattern:
                    self.traits.basetraits.add(i)
                    self.apply_trait(i)

            if self.status not in self.STATUS:
                if set(["Combatant", "Specialist"]).intersection(self.gen_occs):
                    self.status = "free"
                else:
                    self.status = random.sample(self.STATUS, 1).pop()

            # Locations + Home + Status:
            # SM string --> object
            if self.location == "slavemarket":
                set_location(self, pytfall.sm)
            if self.location == "city":
                set_location(self, store.locations["City"])

            # Make sure all slaves that were not supplied custom locations string, find themselves in the SM
            if self.status == "slave" and (str(self.location) == "City" or not self.location):
                set_location(self, pytfall.sm)

            # if character.location == existing location, then she only can be found in this location
            if self.status == "free" and self.location == pytfall.sm:
                set_location(self, store.locations["City"])

            # Home settings:
            if self.location == pytfall.sm:
                self.home = pytfall.sm
            if self.status == "free":
                if not self.home:
                    self.home = locations["City Apartments"]

            # Wagemod:
            if self.status == 'slave':
                self.wagemod = 0
            else:
                self.wagemod = 100

            # Battle and Magic skills:
            if not self.attack_skills:
                self.attack_skills.append(self.default_attack_skill)

            # FOUR BASE TRAITS THAT EVERY GIRL SHOULD HAVE AT LEAST ONE OF:
            if not list(t for t in self.traits if t.personality):
                self.apply_trait(traits["Deredere"])
            if not list(t for t in self.traits if t.race):
                self.apply_trait(traits["Unknown"])
            if not list(t for t in self.traits if t.breasts):
                self.apply_trait(traits["Average Boobs"])
            if not list(t for t in self.traits if t.body):
                self.apply_trait(traits["Slim"])

            # Dark's Full Race Flag:
            if not self.full_race:
                self.full_race = str(self.race)

            # Second round of stats normalization:
            for stat in ["health", "joy", "mp", "vitality"]:
                setattr(self, stat, self.get_max(stat))

            # Arena:
            if "Combatant" in self.gen_occs and self not in hero.chars and self.arena_willing is not False:
                self.arena_willing = True

            # Settle auto-equip + auto-buy:
            if self.status == "free":
                self.autobuy = True
            self.autoequip = True
            self.set_flag("day_since_shopping", 1)

            # add ADVCharacter:
            self.update_sayer()
            self.say_screen_portrait = DynamicDisplayable(self._portrait)
            self.say_screen_portrait_overlay_mode = None

            # Calculate upkeep.
            self.fin.calc_upkeep()

            super(Char, self).init()

        def update_sayer(self):
            self.say = Character(self.nickname, show_two_window=True, show_side_image=self, **self.say_style)

        # def get_availible_pics(self):
        #     """
        #     Determines (per category) what pictures are available for the fixed events (like during the jobs).
        #     This is ran once during the game startup, should also run in the after_load label...
        #     Meant to decrease the amount of checks during the Next Day jobs. Should be activated in post Alpha code review.
        #     PS: It's better to simply add tags to a set instead of booleans as dict values.
        #     """
        #     # Lets start with the normal sex category:
        #     if self.has_image("sex"):
        #         self.picture_base["sex"] = dict(sex=True)
        #     else:
        #         self.picture_base["sex"] = dict(sex=False)
        #
        #     # Lets check for the more specific tags:
        #     if self.build_image_base["sex"]["sex"]:
        #         if self.has_image("sex", "doggy"):
        #             self.picture_base["sex"]["doggy"] = True
        #         else:
        #             self.picture_base["sex"]["doggy"] = False
        #         if self.has_image("sex", "missionary"):
        #             self.picture_base["sex"]["missionary"] = True
        #         else:
        #             self.picture_base["sex"]["missionary"] = False

        # Logic assists:
        def allowed_to_view_personal_finances(self):
            if self.status == "slave":
                return True
            elif self.disposition > 900:
                return True
            return False

        ### Next Day Methods
        def restore(self):
            # Called whenever character needs to have on of the main stats restored.
            l = list()
            if self.autoequip:
                if self.health < self.get_max("health")*.3:
                    l.extend(self.auto_equip(["health"]))
                if self.vitality < self.get_max("vitality")*.2:
                    l.extend(self.auto_equip(["vitality"]))
                if self.mp < self.get_max("mp")*.1:
                    l.extend(self.auto_equip(["mp"]))
                if self.joy < self.get_max("joy")*.4:
                    l.extend(self.auto_equip(["joy"]))
            if l:
                self.txt.append("She used: %s %s during the day!" % (", ".join(l), plural("item", len(l))))
            return l

        def check_resting(self):
            # Auto-Rest should return a well rested girl back to work (or send them auto-resting!):
            txt = []
            if not isinstance(self.action, Rest):
                # This will set this char to AutoRest using normal checks!
                can_do_work(self, check_ap=False, log=txt)
            else: # Char is resting already, we can check if is no longer required.
                self.action.after_rest(self, txt)
            return "".join(txt)

        def next_day(self):
            # Local vars
            img = 'profile'
            txt = []
            flag_red = False
            flag_green = False

            # Update upkeep, should always be a saf thing to do.
            self.fin.calc_upkeep()

            # If escaped:
            if self in pytfall.ra:
                self.health = max(1, self.health - randint(3, 5))
                txt.append("\n{color=[red]}This girl has escaped! Assign guards to search for her or do so yourself.{/color}\n\n")
                flag_red = True
            # TODO se/Char.nd(): This can't be right? This is prolly set to the exploration log object.
            elif self.action == "Exploring":
                txt.append("\n{color=[green]}She is currently on the exploration run!{/color}\n")
            else:
                # Front text (Days employed)
                days = set_font_color(self.fullname, "green")
                if not self.flag("daysemployed"):
                    txt.append("{} has started working for you today! ".format(days))
                else:
                    txt.append("{} has been working for you for {} {}. ".format(days,
                                                                            self.flag("daysemployed"),
                                                                            plural("day", self.flag("daysemployed"))))
                self.up_counter("daysemployed")

                if self.status == "slave":
                    txt.append("She is a slave.")
                else:
                    txt.append("She is a free citizen.")

                # Home location nd mods:
                loc = self.home
                mod = loc.daily_modifier

                if mod > 0:
                    temp = "She comfortably spent a night in {}.".format(str(loc))
                    if self.home == hero.home:
                        if self.disposition > -500:
                            # Slave is assumed as we can't effect where free chars spend nights in.
                            temp += " She is happy to live under the same roof as her master!"
                            self.disposition += 1
                            self.joy += randint(1, 3)
                        else:
                            temp += " Even though you both live in the same house, she hates you too much to really care."

                    txt.append(temp)

                elif mod < 0:
                    flag_red = True
                    txt.append("{color=[red]}She presently resides in the %s.{/color}" % str(loc))
                    txt.append("{color=[red]}It's not a comfortable or healthy place to sleep in.{/color}")
                    txt.append("{color=[red]}Try finding better accommodations for your worker!{/color}\n")

                for stat in ("health", "mp", "vitality"):
                    mod_by_max(self, stat, mod)

                # Finances:
                # Upkeep:
                if not self.is_available:
                    pass
                elif in_training_location(self):
                    txt.append("Upkeep is included in price of the class your girl's taking. \n")
                else:
                    # The whole upkeep thing feels weird, penalties to slaves are severe...
                    amount = self.fin.get_upkeep()

                    if not amount:
                        pass
                    elif amount < 0:
                        txt.append("She actually managed to save you some money ({color=[gold]}%d Gold{/color}) instead of requiring upkeep! Very convenient! \n" % (-amount))
                        hero.add_money(-amount, reason="Workers Upkeep")
                    elif hero.take_money(amount, reason="Workers Upkeep"):
                        self.fin.log_logical_expense(amount, "Upkeep")
                        if hasattr(self.workplace, "fin"):
                            self.workplace.fin.log_logical_expense(amount, "Workers Upkeep")
                        txt.append("You paid {color=[gold]}%d Gold{/color} for her upkeep. \n" % amount)
                    else:
                        if self.status != "slave":
                            self.joy -= randint(3, 5)
                            self.disposition -= randint(5, 10)
                            txt.append("\nYou failed to pay her upkeep, she's a bit cross with your because of that... \n")
                        else:
                            self.joy -= 20
                            self.disposition -= randint(25, 50)
                            self.health = max(1, self.health - 10)
                            self.vitality -= 25
                            txt.append("\nYou've failed to provide even the most basic needs for your slave. This will end badly... \n")

            # This whole routine is basically fucked and done twice or more. Gotta do a whole check of all related parts tomorrow.
            # Settle wages:
            if self not in pytfall.ra:
                img = self.fin.settle_wage(txt, img)

                tips = self.flag("ndd_accumulated_tips")
                if tips:
                    temp = choice(["Total tips earned: %d Gold. " % tips,
                                   "%s got %d Gold in tips. " % (self.nickname, tips)])
                    txt.append(temp)

                    if self.autocontrol["Tips"]:
                        temp = choice(["As per agreement, your worker gets to keep all her tips! This is a very good motivator. ",
                                       "She's happy to keep it. "])
                        txt.append(temp)

                        self.add_money(tips, reason="Tips")
                        self.fin.log_logical_expense(tips, "Tips")
                        if isinstance(self.workplace, Building):
                            self.workplace.fin.log_logical_expense(tips, "Tips")

                        self.disposition += (1 + round_int(tips*.05))
                        self.joy += (1 + round_int(tips*.025))
                    else:
                        temp = choice(["You take all of her tips for yourself. ",
                                       "You keep all of it. "])
                        txt.append(temp)
                        hero.add_money(tips, reason="Worker Tips")

            # Training with NPCs ---------------------------------------------->
            if self.is_available:
                self.nd_auto_train(txt)

                # Shopping (For now will not cost AP):
                self.nd_autoshop(txt)
                # --------------------------------->>>

                self.restore()
                self.check_resting()

                # Unhappiness and related:
                img = self.nd_joy_disposition_checks(txt, img)

                # Effects:
                if 'Poisoned' in self.effects:
                    txt.append("\n{color=[red]}This girl is suffering from the effects of Poison!{/color}\n")
                    flag_red = True
                if all([not self.autobuy, self.status != "slave", self.disposition < 950]):
                    self.autobuy = True
                    txt.append("She will go shopping whenever it may please here from now on!\n")
                if all([self.status != "slave", self.disposition < 850, not self.autoequip]):
                    self.autoequip = True
                    txt.append("She will be handling her own equipment from now on!\n")

                # Prolly a good idea to throw a red flag if she is not doing anything:
                # I've added another check to make sure this doesn't happen if
                # a girl is in FG as there is always something to do there:
                if not self.action:
                    flag_red = True
                    txt.append("\n\n  {color=[red]}Please note that she is not really doing anything productive!-{/color}\n")

            txt.append("{color=[green]}\n\n%s{/color}" % "\n".join(self.txt))

            # Finances related:
            self.fin.next_day()

            # Resets and Counters:
            self.restore_ap()
            self.reservedAP = 0
            self.item_counter()

            self.up_counter("day_since_shopping")

            self.nd_log_report(txt, img, flag_red, type='girlndreport')

            self.txt = list()
            super(Char, self).next_day()

        def nd_autoshop(self, txt):
            if all([self.autobuy, self.flag("day_since_shopping") > 5,
                    self.gold > 1000]):

                self.set_flag("day_since_shopping", 1)
                temp = choice(["\n\n%s decided to go on a shopping tour :)\n" % self.nickname,
                               "\n\n%s went to town to relax, take her mind of things and maybe even do some shopping!\n" % self.nickname])
                txt.append(temp)

                result = self.auto_buy(amount=randint(1, 2))
                if result:
                    temp = choice(["{color=[green]}She bought {color=[blue]}%s %s{/color} for herself. This brightened her mood a bit!{/color}\n\n"%(", ".join(result), plural("item",len(result))),
                                   "{color=[green]}She got her hands on {color=[blue]}%s %s{/color}! She's definitely in better mood because of that!{/color}\n\n"%(", ".join(result),
                                                                                                                                                                   plural("item", len(result)))])
                    txt.append(temp)
                    flag_green = True
                    self.joy += 5 * len(result)
                else:
                    temp = choice(["But she ended up not doing much else than window-shopping...\n\n",
                                   "But she could not find what she was looking for...\n\n"])
                    txt.append(temp)

        def nd_joy_disposition_checks(self, txt, img):
            size = ND_IMAGE_SIZE

            if self.joy <= 25:
                txt.append("\n\nThis girl is unhappy!")
                img = self.show("profile", "sad", resize=size)
                self.days_unhappy += 1
            else:
                if self.days_unhappy - 1 >= 0:
                    self.days_unhappy -= 1

            if self.days_unhappy > 7 and self.status != "slave":
                txt.append("{color=[red]}She has left your employment because you do not give a rats ass about how she feels!{/color}")
                flag_red = True
                hero.remove_char(self)
                self.home = locations["City Apartments"]
                self.action = None
                self.workplace = None
                set_location(self, locations["City"])
            elif self.disposition < -500:
                if self.status != "slave":
                    txt.append("{color=[red]}She has left your employment because she no longer trusts or respects you!{/color}")
                    flag_red = True
                    img = self.show("profile", "sad", resize=size)
                    hero.remove_char(self)
                    self.home = locations["City Apartments"]
                    self.action = None
                    self.workplace = None
                    set_location(self, locations["City"])
                elif self.days_unhappy > 7:
                    if dice(50):
                        txt.append("\n{color=[red]}Took her own life because she could no longer live as your slave!{/color}")
                        img = self.show("profile", "sad", resize=size)
                        flag_red = True
                        self.health = 0
                    else:
                        txt.append("\n{color=[red]}Tried to take her own life because she could no longer live as your slave!{/color}")
                        img = self.show("profile", "sad", resize=size)
                        flag_red = True
                        self.health = 1

            # This is temporary code, better and more reasonable system is needed,
            # especially if we want different characters to befriend each other.

            # until we'll have means to deal with chars
            # with very low disposition (aka slave training), negative disposition will slowly increase
            if self.disposition < -200:
                self.disposition += randint(2, 5)

            friends_disp_check(self, txt)

            return img


    class rChar(Char):
        '''Randomised girls (WM Style)
        Basically means that there can be a lot more than one of them in the game
        Different from clones we discussed with Dark, because clones should not be able to use magic
        But random girls should be as good as any of the unique girls in all aspects
        It will most likely not be possible to write unique scripts for random girlz
        '''
        def __init__(self):
            super(rChar, self).__init__()


    class Customer(PytCharacter):
        def __init__(self, gender="male", caste="Peasant"):
            super(Customer, self).__init__()

            # Using direct access instead of a flag, looks better in code:
            self.served_by = ()
            self.du_without_service = 0 # How long did this client spent without service

            self.gender = gender
            self.caste = caste
            self.rank = ilists.clientCastes.index(caste)
            self.regular = False # Regular clients do not get removed from building lists as those are updated.

            # Traits activation:
            if dice(2):
                self.apply_trait('Aggressive')

            # Alex, we should come up with a good way to set portrait depending on caste
            self.portrait = "" # path to portrait
            self.questpic = "" # path to picture used in quests
            self.act = ""
            self.pronoun = ""

            # determine act and pronoun
            if self.gender == 'male':
                self.act = choice(["sex", "anal", "blowjob"])
                self.pronoun = 'He'

            elif self.gender == 'female':
                self.act = "lesbian"
                self.pronoun = 'She'


    class NPC(Char):
        """There is no point in this other than an ability to check for instances of NPCs
        """
        def __init__(self):
            super(NPC, self).__init__()
