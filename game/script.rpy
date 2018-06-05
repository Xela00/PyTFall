init 100 python:
    tagdb = TagDatabase()
    for tag in tags_dict.values():
        tagdb.tagmap[tag] = set()

    tl.start("Loading: Mobs")
    mobs = load_mobs()
    tl.end("Loading: Mobs")

default defeated_mobs = {}

label start:
    $ renpy.block_rollback()
    $ locked_random("random") # Just making sure that we have set the variable...

    if DEBUG:
        $ renpy.show_screen("debug_tools")
    $ renpy.show_screen("new_style_tooltip")
    $ gfx_overlay = GFXOverlay()
    $ renpy.show("pf_gfx_overlay", what=gfx_overlay, layer="pytfall")

    python: # Variable defaults:
        chars_list_last_page_viewed = 0
        char = None # Character global
        came_to_equip_from = None # Girl equipment screen came from label holder
        eqtarget = None # Equipment screen
        char_profile = None # Girl profile screen came from label holder
        gallery = None

    python: # Day/Calendar/Names/Menu Extensions and some other defaults.
        # Global variables and loading content:
        day = 1
        calendar = Calendar(day=28, month=2, year=125)
        global_flags = Flags()

        ilists = ListHandler()
        # difficulty = Difficulties()

        # Locations (we need this here cause we'll write to it soon):
        locations = dict()

        # Load random names selections for rGirls:
        tl.start("Loading: Random Name Files")
        female_first_names = load_female_first_names(200)
        male_first_names = load_male_first_names(200)
        random_last_names = load_random_last_names(200)
        random_team_names = load_team_names(50)
        tl.end("Loading: Random Name Files")

        tl.start("Loading: PyTFallWorld")
        pytfall = PyTFallWorld()
        tl.end("Loading: PyTFallWorld")

        tl.start("Loading: Menu Extensions")
        menu_extensions = MenuExtension()
        menu_extensions["Abby The Witch Main"] = []
        menu_extensions["Xeona Main"] = []
        tl.end("Loading: Menu Extensions")

    python hide: # Base locations:
        # Create locations:
        loc = HabitableLocation(id="Streets", daily_modifier=-.1, rooms=float("inf"))
        locations[loc.id] = loc

        loc = HabitableLocation(id="City Apartments", daily_modifier=.2, rooms=float("inf"))
        locations[loc.id] = loc

        loc = Location(id="City")
        locations[loc.id] = loc

        loc = HabitableLocation(id="After Life", daily_modifier=.0, rooms=float("inf"))
        locations[loc.id] = loc

    python: # Traits:
        # Load all game elements:
        tl.start("Loading/Sorting: Traits")
        traits = load_traits()

        # This should be reorganized later:
        tgs = object() # TraitGoups!
        tgs.breasts = [i for i in traits.values() if i.breasts]
        tgs.body = [i for i in traits.values() if i.body]
        tgs.base = [i for i in traits.values() if i.basetrait and not i.mob_only]
        tgs.elemental = [i for i in traits.values() if i.elemental]
        tgs.el_names = set([i.id.lower() for i in tgs.elemental])
        tgs.ct = [i for i in traits.values() if i.character_trait]
        tgs.sexual = [i for i in traits.values() if i.sexual] # This is a subset of character traits!
        tgs.race = [i for i in traits.values() if i.race]
        tgs.client = [i for i in traits.values() if i.client]

        # Base classes such as: {"SIW": [Prostitute, Stripper]}
        gen_occ_basetraits = defaultdict(set)
        for t in tgs.base:
            for occ in t.occupations:
                gen_occ_basetraits[occ].add(t)
        gen_occ_basetraits = dict(gen_occ_basetraits)
        tl.end("Loading/Sorting: Traits")

    python: # Items/Shops:
        tl.start("Loading/Sorting: Items")
        items = load_items()
        items.update(load_gifts())
        items_upgrades = json.load(renpy.file("content/db/upgrades.json"))

        # Build shops:
        pytfall.init_shops()

        # Items sorting for AutoBuy:
        shop_items = [item for item in items.values() if (set(pytfall.shops) & set(item.locations))]
        all_auto_buy_items = [item for item in shop_items if item.usable and not item.jump_to_label]

        trait_selections = {"goodtraits": {}, "badtraits": {}}
        auto_buy_items = {k: [] for k in ("body", "restore", "food", "dress", "rest", "warrior", "scroll")}

        for item in all_auto_buy_items:
            for k in ("goodtraits", "badtraits"):
                if hasattr(item, k):
                    for t in getattr(item, k):
                        # same item may occur multiple times for different traits.
                        trait_selections[k].setdefault(t, []).append(item)

            if item.type != "permanent":
                if item.type == "armor" or item.slot == "weapon":
                    auto_buy_items["warrior"].append(item)
                else:
                    if item.slot == "body":
                        auto_buy_items["body"].append(item)
                    if item.type in ("restore", "food", "scroll", "dress"):
                        auto_buy_items[item.type].append(item)
                    else:
                        auto_buy_items["rest"].append(item)

        for k in trait_selections:
            for v in trait_selections[k].values():
                v = sorted(v, key=lambda i: i.price)

        for k in ("body", "restore", "food", "dress", "rest", "warrior", "scroll"):
            auto_buy_items[k] = [(i.price, i) for i in auto_buy_items[k]]
            auto_buy_items[k].sort()

        # Items sorting per Tier:
        tiered_items = {}
        for i in items.values():
            tiered_items.setdefault(i.tier, []).append(i)

        tl.end("Loading/Sorting: Items")

    python: # Dungeons (Building (Old))
        tl.start("Loading: Dungeons")
        dungeons = load_dungeons()
        tl.end("Loading: Dungeons")

    # Battle Skills:
    $ tl.start("Loading: Battle Skills")
    $ battle_skills = dict()
    call load_battle_skills from _call_load_battle_skills
    $ tiered_magic_skills = {}
    python:
        for s in battle_skills.values():
            tiered_magic_skills.setdefault(s.tier, []).append(s)

    $ tl.end("Loading: Battle Skills")

    $ hero = Player()

    python: # Jobs:
        tl.start("Loading: Jobs")
        # This jobs are usually normal, most common type that we have in PyTFall
        temp = [WhoreJob(), StripJob(), BarJob(), Manager(), CleaningJob(), GuardJob(), Rest(), AutoRest()]
        simple_jobs = {j.id: j for j in temp}
        del temp
        tl.end("Loading: Jobs")

    python: # Ads and Buildings:
        tl.start("Loading: Businesses")
        adverts = json.load(renpy.file("content/db/buildings/adverts.json"))
        businesses = load_buildings()
        tl.end("Loading: Businesses")

    $ tl.start("Loading: Schools")
    $ schools = {}
    python hide: # Training/Schools/Weird Proxies by Thewlis:
        school = School() #updated for new School class 6/3/2018.
        school.add_cources()
        schools[school.id] = school # new School class has id not name.
        # schools = load_schools()
        # pytFlagProxyStore = shallowcopy(pytFlagProxyStore)
    $ tl.end("Loading: Schools")

    # python: # Picked Tags and maps (afk atm):
    #     maps = xml_to_dict(content_path('db/map.xml'))
    #
    #     import cPickle as pickle
    #     tl.start("Loading: Binary Tag Database")
    #     # pickle.dump(tagdb.tagmap, open(config.gamedir + "/save.p", "wb"))
    #     tagdb = TagDatabase()
    #     tagdb.tagmap = pickle.load(open(config.gamedir + "/save.p", "rb"))
    #     tagslog.info("loaded %d images from binary files" % tagdb.count_images())
    #     tl.end("Loading: Binary Tag Database")

    python: # Tags/Loading Chars/Mobs/Quests.first_day
        # Loading characters:
        # tagdb = TagDatabase()
        # for tag in tags_dict.values():
        #     tagdb.tagmap[tag] = set()

        tl.start("Loading: All Characters!")
        chars = load_characters("chars", Char)
        npcs = load_characters("npc", NPC)
        rchars = load_random_characters()
        tl.end("Loading: All Characters!")
        if DEBUG_LOG:
            devlog.info("Loaded %d images from filenames!" % tagdb.count_images())

        # Start auto-quests
        pytfall.world_quests.first_day()

        # tl.start("Loading: Mobs")
        # mobs = load_mobs()
        # tl.end("Loading: Mobs")

    # python: # SE (Areas)
    #     tl.start("Loading: Exploration Areas")
    #     # pytfall.forest_1 = Exploration()
    #     fg_areas = load_fg_areas()
    #     tl.end("Loading: Exploration Areas")

    python: # Move to a World AI method:
        tl.start("Loading: Populating World with RChars")
        pytfall.populate_world()
        tl.end("Loading: Populating World with RChars")

    python: # Girlsmeets/Items Upgrades:
        tl.start("Loading: GirlsMeets")
        gm = GirlsMeets()
        tl.end("Loading: GirlsMeets")

    # Loading apartments/guilds:
    call load_resources from _call_load_resources
    jump dev_testing_menu_and_load_mc

label dev_testing_menu_and_load_mc:
    if DEBUG:
        menu:
            "Debug Mode":
                $ hero.traits.basetraits.add(traits["Mage"])
                $ hero.apply_trait(traits["Mage"])
                menu:
                    "Level 1":
                        $ n=0
                    "Overpowered":
                        $ n=10
                $ tier_up_to(hero, n, level_bios=(.9, 1.1), skill_bios=(.8, 1.2), stat_bios=(.8, 1.0))
                $ del n
            "Content":
                menu:
                    "Test Intro":
                        call intro from _call_intro
                        call mc_setup from _call_mc_setup
                    "MC Setup":
                        call mc_setup from _call_mc_setup_1
                    "Skip MC Setup":
                        $ pass
                    "Back":
                        jump dev_testing_menu_and_load_mc
            "GFX":
                while 1:
                    menu gfx_testing_menu:
                        "Particle":
                            scene black
                            show expression ParticleBurst([Solid("#%06x"%renpy.random.randint(0, 0xFFFFFF), xysize=(5, 5)) for i in xrange(50)], mouse_sparkle_mode=True) as pb
                            pause
                            hide pb
                        "Back":
                            jump dev_testing_menu_and_load_mc
    else:
        call intro from _call_intro_1
        call mc_setup from _call_mc_setup_2

    python: # We run this in case we skipped MC setup in devmode!
        if not getattr(hero, "_path_to_imgfolder", None):
            renpy.music.stop()
            if not DEBUG:
                # We're fucked if this is the case somehow :(
                raise Exception("Something went horribly wrong with MC setup!")

            male_fighters, female_fighters, json_fighters = load_special_arena_fighters()
            af = choice(male_fighters.values())
            del male_fighters[af.id]

            hero._path_to_imgfolder = af._path_to_imgfolder
            hero.id = af.id
            hero.say = Character(hero.nickname, color=ivory, show_two_window=True, show_side_image=hero.show("portrait", resize=(120, 120)))
            hero.restore_ap()
            hero.log_stats()

            if DEBUG and not hero.home:
                ap = buildings["Lux Apartment"]
                hero.buildings.append(ap)
                hero.home = ap
                del ap

    jump continue_with_start

label continue_with_start:
    python: # Load Arena
        tl.start("Loading: Arena!")
        pytfall.arena = Arena()
        locations[pytfall.arena.id] = pytfall.arena
        pytfall.arena.setup_arena()
        pytfall.arena.update_matches()
        pytfall.arena.update_teams()
        pytfall.arena.find_opfor()
        pytfall.arena.update_dogfights()
        tl.end("Loading: Arena!")

    # Call girls starting labels:
    $ all_chars = chars.values()
    while all_chars:
        $ temp = all_chars.pop()
        $ chars_unique_label = "_".join(["start", temp.id])
        if renpy.has_label(chars_unique_label):
            call expression chars_unique_label from _call_expression_1

    # Clean up globals after loading chars:
    python:
        for i in ("chars_unique_label", "char", "girl", "testBrothel", "all_chars", "temp", "utka"):
            del(i)

    #  --------------------------------------
    # Put here to facilitate testing:
    if DEBUG and renpy.has_label("testing"):
        call testing from _call_testing

    python in _console:
        if store.DEBUG:
            stdio_lines = []
            stderr_lines = []
            console.history = []

    if hero.name.lower() == "darktl": # LoL! :D
        $ hero.gold += 888888888

    # last minute checks:
    if not hero.home:
        $ hero.home = locations["Streets"]

    python: # Populate Slave Market:
        tl.start("Loading: Populating SlaveMarket")
        pytfall.sm.populate_chars_list()
        tl.end("Loading: Populating SlaveMarket")

    jump mainscreen

label after_load:
    if hasattr(store, "stored_random_seed"):
        $ renpy.random.setstate(stored_random_seed)

    # TODO Delete after schools and recheck the label:
    $ DAILY_EXP_CORE = 100

    python hide:
        for c in store.chars.values():
            c.clear_img_cache()

        # TODO: Remove this after schools recode
        for c in store.pytfall.arena.arena_fighters.values():
            c.label_cache = []

    python hide:
        updated_chars = load_characters("chars", Char)
        for id, char in updated_chars.items():
            if id not in store.chars:
                store.chars[id] = char

        load_characters("npc", NPC)
        store.rchars = load_random_characters()
        load_special_arena_fighters()

    # Complete hack:
    python hide:
        if not hasattr(store.hero, "autocontrol"):
            store.hero.autocontrol = {"Rest": False,
                                        "Tips": False,
                                        "SlaveDriver": False,
                                        "Acts": {"normalsex": True, "anal": True, "blowjob": True, "lesbian": True},
                                        "S_Tasks": {"clean": True, "bar": True, "waitress": True}}

    python hide:
        for building in store.buildings.values():
            if isinstance(building, Flags) and not hasattr(building, "flags"):
                building.flags = dict()

        for building in store.businesses.values():
            if isinstance(building, Flags) and not hasattr(building, "flags"):
                building.flags = dict()

        for building in hero.buildings:
            if isinstance(building, Flags) and not hasattr(building, "flags"):
                building.flags = dict()

    python hide:
        pytfall.economy.property_tax = {"slaves": .001,
                                        "real_estate": .0015}

    python:
        if hasattr(store, "dummy"):
            del dummy

    python hide:
        for b in hero.buildings:
            temp = getattr(b, "workable", False)
            if temp:
                b.needs_management = True
            if hasattr(b, "_adverts"):
                b._adverts = deepcopy(b._adverts)
        for b in businesses.values():
            temp = getattr(b, "workable", False)
            if temp:
                b.needs_management = True
            if hasattr(b, "_adverts"):
                b._adverts = deepcopy(b._adverts)

    python hide:
        for skill in store.battle_skills.values():
            skill.source = None

    python:
        if hasattr(store, "pytRelayProxyStore"):
            pytRelayProxyStore = []

    python hide:
        for c in chars.values() + pytfall.arena.arena_fighters.values():
            if hasattr(c, "guard_relay"):
                delattr(c, "guard_relay")

    # TODO Delete after Schools Rewrite!
    $ type = types.TypeType

    stop music
    return
