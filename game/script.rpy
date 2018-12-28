init 100 python:
    tagdb = TagDatabase()
    for tag in tags_dict.values():
        tagdb.tagmap[tag] = set()

    tl.start("Loading: Mobs")
    mobs = load_mobs()
    tl.end("Loading: Mobs")

default defeated_mobs = {}
default gazette = Gazette()

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
        loc = HabitableLocation(id="Streets", daily_modifier=-.1, rooms=float("inf"), desc="Cold and unneighborly city alleys")
        locations[loc.id] = loc

        loc = HabitableLocation(id="City Apartments", daily_modifier=.2, rooms=float("inf"), desc="Girls apartments somewhere in the city")
        locations[loc.id] = loc

        loc = Location(id="City")
        locations[loc.id] = loc

        loc = HabitableLocation(id="After Life", daily_modifier=.0, rooms=float("inf"), desc="No one knows where is this place and what's going on there")
        locations[loc.id] = loc

    python: # Traits:
        # Load all game elements:
        tl.start("Loading/Sorting: Traits")
        traits = load_traits()
        global_flags.set_flag("last_modified_traits", os.path.getmtime(content_path('db/traits')))

    call sort_traits_for_gameplay from _call_sort_traits_for_gameplay

    $ tl.end("Loading/Sorting: Traits")

    python: # Items/Shops:
        tl.start("Loading/Sorting: Items")
        items = load_items()
        items.update(load_gifts())
        global_flags.set_flag("last_modified_items", os.path.getmtime(content_path('db/items')))
        items_upgrades = json.load(renpy.file("content/db/upgrades.json"))

        # Build shops:
        pytfall.init_shops()

    call sort_items_for_gameplay from _call_sort_items_for_gameplay

    $ tl.end("Loading/Sorting: Items")

    python: # Dungeons (Building (Old))
        tl.start("Loading: Dungeons")
        dungeons = load_dungeons()
        tl.end("Loading: Dungeons")

    # Battle Skills:
    $ tl.start("Loading: Battle Skills")
    $ battle_skills = dict()
    call load_battle_skills from _call_load_battle_skills
    $ tiered_magic_skills = dict()
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
        businesses = load_businesses()
        tl.end("Loading: Businesses")

    $ tl.start("Loading: Schools")
    $ schools = {}
    python hide: # Training/Schools/Weird Proxies by Thewlis:
        school = School()
        school.add_courses()
        schools[school.name] = school
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
        #global_flags.set_flag("last_modified_chars", os.path.getmtime(content_path('chars')))
        npcs = load_characters("npc", NPC)
        #global_flags.set_flag("last_modified_npcs", os.path.getmtime(content_path('npc')))
        rchars = load_random_characters()
        #global_flags.set_flag("last_modified_rchars", os.path.getmtime(content_path('rchars')))
        tl.end("Loading: All Characters!")
        if DEBUG_LOG:
            devlog.info("Loaded %d images from filenames!" % tagdb.count_images())

        # Start auto-quests
        pytfall.world_quests.first_day()

        # tl.start("Loading: Mobs")
        # mobs = load_mobs()
        # tl.end("Loading: Mobs")

    python: # SE (Areas)
        tl.start("Loading: Exploration Areas")
        # pytfall.forest_1 = Exploration()
        fg_areas = load_fg_areas()
        tl.end("Loading: Exploration Areas")

    python: # Move to a World AI method:
        tl.start("Loading: Populating World with RChars")
        pytfall.populate_world()
        tl.end("Loading: Populating World with RChars")

    python: # Girlsmeets:
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
                        $ n = 0
                    "Overpowered":
                        $ n = 10
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

            male_fighters, female_fighters = load_special_arena_fighters()
            af = choice(male_fighters.values())
            del male_fighters[af.id]

            hero._path_to_imgfolder = af._path_to_imgfolder
            hero.id = af.id
            hero.say = Character(hero.nickname, color=ivory, show_two_window=True, show_side_image=hero.show("portrait", resize=(120, 120)))
            hero.restore_ap()
            hero.log_stats()

            if DEBUG and not hero.home:
                ap = None 
                for b in buildings.values():
                    if ap == None or b.price > ap.price:
                        ap = b
                if ap:
                    hero.buildings.append(ap)
                    hero.home = ap
                del ap

    # Set Human trait for the MC: (We may want to customize this in the future)
    python:
        if not isinstance(hero.race, Trait):
            hero.apply_trait(traits["Human"])
            hero.full_race = "Human"

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

label sort_items_for_gameplay:
    python:
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
    return

label sort_traits_for_gameplay:
    python:
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
    return

label after_load:
    if hasattr(store, "stored_random_seed"):
        $ renpy.random.setstate(stored_random_seed)

    python hide:
        for c in store.chars.values():
            c.clear_img_cache()

    init python:
        def update_object(obj_dest, obj_src, prefix):
            for attr, v in vars(obj_dest).items():
                if hasattr(obj_src, attr):
                    v2 = getattr(obj_src, attr)
                    if v2 != v:
                        devlog.info("{} - Modified Attr {}: {} -> {} in {}".format(prefix, attr, str(v), str(v2), str(obj_dest)))
                        setattr(obj_dest, attr, v2)
                else:
                    devlog.info("{} - Attr Removed: {} from {}".format(prefix, attr, str(obj_dest)))
                    delattr(obj_dest, attr)

            for attr, v2 in vars(obj_src).items():
                if not hasattr(obj_dest, attr):
                    devlog.info("{} - New Attr {} for {} with value {}".format(prefix, attr, str(obj_dest), str(v2)))
                    setattr(obj_dest, attr, v2)

    # Updating Databases:
    # Items:
    python hide:
        last_modified_items = global_flags.get_flag("last_modified_items", 0)
        last_modified = os.path.getmtime(content_path('db/items'))
        if last_modified_items < last_modified: 
            tl.start("Updating items")
            updated_items = load_items()
            updated_items.update(load_gifts())

            for id, item in updated_items.iteritems():
                curr_item = store.items.get(id, None)
                if curr_item is None:
                    # Add new item
                    store.items[id] = item
                    devlog.info("New Item: {}".format(id))
                else:
                    # Update the existing item
                    update_object(curr_item, item, "Item")

            del updated_items
            tl.end("Updating items")
            global_flags.set_flag("last_modified_items", last_modified)
            renpy.call("sort_items_for_gameplay")

    # Traits:
    python hide:
        last_modified_traits = global_flags.get_flag("last_modified_traits", 0)
        last_modified = os.path.getmtime(content_path('db/traits'))
        if last_modified_traits < last_modified:
            tl.start("Updating traits")
            updated_traits = load_traits()
            for id, trait in updated_traits.iteritems():
                curr_trait = store.traits.get(id, None)
                if curr_trait is None:
                    # Add new trait
                    store.traits[id] = trait
                    devlog.info("New Trait: {}".format(id))
                else:
                    # Update the existing trait
                    update_object(curr_trait, trait, "Trait")

            del updated_traits
            tl.end("Updating traits")
            global_flags.set_flag("last_modified_traits", last_modified) 
            renpy.call("sort_traits_for_gameplay")

    # All kinds of chars:
    python hide:
        # uChars:
        # always run till tagdb is not separated from the load_characters
        #last_modified_chars = global_flags.get_flag("last_modified_chars", 0)
        #last_modified = os.path.getmtime(content_path('chars'))
        if True: # last_modified_chars < last_modified:
        #    tl.start("Updating chars")
            updated_chars = load_characters("chars", Char)
            for id, char in updated_chars.items():
                curr_char = store.chars.get(id, None)
                if curr_char is None:
                    # Add new char
                    store.chars[id] = char
        #            devlog.info("New Character: {}".format(id))
        #        else:
        #            # Update the existing char
        #            update_object(curr_char, char, "Char")

        #    del updated_chars
        #    tl.end("Updating chars")
        #    global_flags.set_flag("last_modified_chars", last_modified)

        # NPCs:
        # always run till tagdb is not separated from load_characters
        #last_modified_npcs = global_flags.get_flag("last_modified_npcs", 0)
        #last_modified = os.path.getmtime(content_path('npc'))
        if True: #last_modified_npcs < last_modified:
        #    tl.start("Updating NPCs")
            updated_npcs = load_characters("npc", NPC)
            for id, npc in updated_npcs.items():
                curr_npc = store.npcs.get(id, None)
                if curr_npc is None:
                    # Add new NPC
                    store.npcs[id] = npc
        #            devlog.info("New NPC: {}".format(id))
        #        else:
        #            # Update the existing npc
        #            update_object(curr_npc, npc, "NPC")

        #    del updated_npcs
        #    tl.end("Updating NPCs")
        #    global_flags.set_flag("last_modified_npcs", last_modified)

        # rChars:
        # always run till tagdb is not separated from load_random_characters
        # last_modified_rchars = global_flags.get_flag("last_modified_rchars", 0)
        # last_modified = os.path.getmtime(content_path('rchars'))
        if True: #last_modified_rchars < last_modified:
        #    tl.start("Updating rchars")
            store.rchars = load_random_characters()
        #    tl.end("Updating rchars")
        #    global_flags.set_flag("last_modified_rchars", last_modified)

        # Arena Chars (We need this for databases it would seem...):
        load_special_arena_fighters()

    python:
        if hasattr(store, "dummy"):
            del dummy

    python hide: # Do we need/want this?
        for skill in store.battle_skills.values():
            skill.source = None

    # Save-Load Compatibility TODO Delete when we're willing to break saves (again :D).
    # python hide:
    #     for c in pytfall.sm.inhabitants.copy():
    #         if c not in chars.itervalues():
    #             remove_from_gameworld(c)
    #     aps = locations["City Apartments"]
    #     for c in aps.inhabitants.copy():
    #         if c not in chars.itervalues():
    #             remove_from_gameworld(c)
    python hide:
        tierless_items = store.tiered_items.get(None)
        if tierless_items:
            for item in tierless_items:
                item.tier = 0
                store.tiered_items[0].append(item)
            del store.tiered_items[None]

        if not hasattr(pytfall.arena, "df_count"):
            pytfall.arena.df_count = 0
            pytfall.arena.hero_match_result = None 

        if not hasattr(hero, "teams"):
            hero.teams = [hero.team]

        for b in hero.buildings:
            if isinstance(b, UpgradableBuilding):
                if not hasattr(b, "init_pep_talk"):
                    ManagerData.__init__(b)
            if isinstance(b, BuildingStats):
                if isinstance(b.auto_clean, bool):
                    val = 90 if b.auto_clean else 100
                    del b.auto_clean
                    b.auto_clean = val 
        for b in businesses.values():
            if isinstance(b, UpgradableBuilding):
                if not hasattr(b, "init_pep_talk"):
                    ManagerData.__init__(b)
            if isinstance(b, BuildingStats):
                if isinstance(b.auto_clean, bool):
                    val = 90 if b.auto_clean else 100
                    del b.auto_clean
                    b.auto_clean = val 

    python hide:
        if hasattr(store, "json_fighters"):
            for id, fighter in store.json_fighters.iteritems():
                if fighter.gender == "male":
                    store.male_fighters[id] = fighter
                else:
                    store.female_fighters[id] = fighter
            del store.json_fighters

        for obj in pytfall.__dict__.values():
            if isinstance(obj, ItemShop) and not hasattr(obj, "total_items_price"):
                obj.total_items_price = 0

    python hide:
        for d in pytfall.world_actions.nest:
            if hasattr(d, "values"):
                for obj in d.values():
                    if not hasattr(obj, "keysym"):
                        obj.keysym = None
            else:
                if not hasattr(d, "keysym"):
                    d.keysym = None

        for d in pytfall.world_actions.locations.values():
            if hasattr(d, "values"):
                for obj in d.values():
                    if not hasattr(obj, "keysym"):
                        obj.keysym = None
            else:
                if not hasattr(d, "keysym"):
                    d.keysym = None

    stop music
    return
