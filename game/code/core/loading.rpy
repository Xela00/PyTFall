# The whole thing should one day be recoded over a single renpy.list_files loop.
init 11 python:
    def load_webms():
        webms = {}
        for path in renpy.list_files():
            if "content/gfx/autowebm/" in path:
                split_path = path.split("/")
                folder = split_path[-2]
                file = split_path[-1]
                if "mask" in file:
                    webms.setdefault(folder, {})["mask"] = path
                if "movie" in file:
                    webms.setdefault(folder, {})["movie"] = path
                if "moviemask" in file: # rare cases when movie itself is also the mask
                    webms.setdefault(folder, {})["movie"] = path
                    webms.setdefault(folder, {})["mask"] = path

        for folder in webms:
            temp = folder.split(" ")

            tag = temp[0]
            channel = temp[2] if len(temp) == 3 else "main_gfx_attacks"
            loops = temp[1] if len(temp) >= 2 else 1
            if loops == "inf":
                renpy.image(tag, Movie(channel=channel, play=webms[folder]["movie"], mask=webms[folder].get("mask", None)))
            else:
                loops = int(loops)
                renpy.image(tag, MovieLooped(channel=channel, loops=loops, play=webms[folder]["movie"], mask=webms[folder].get("mask", None)))

    load_webms()

init -11 python:
    # ---------------------- Loading game data:
    def load_json(path):
        file = renpy.file(path)
        data = json.load(file)
        return data

    def load_db_json(fn):
        path = "content/db/" + fn
        return load_json(path)

    def load_tags_folder(folder, path):
        for fn in os.listdir(path):
            if check_image_extension(fn):
                tags = fn.split("-")
                try:
                    del tags[0]
                    tags[-1] = tags[-1].split(".")[0]
                except IndexError:
                    raise Exception("Invalid file path for image: %s in folder %s" % (fn, path))
                for tag in tags:
                    if tag not in tags_dict:
                        raise Exception("Unknown image tag: %s, fn: %s, path: %s" % (tag, fn, path))
                    tagdb.tagmap[tags_dict[tag]].add(fn)
                # Adding filenames to girls id:
                tagdb.tagmap.setdefault(folder, set()).add(fn)

    def load_team_names(amount):
        rn = load_db_json("names/team_names.json")
        return random.sample(rn, amount)

    def load_male_first_names(amount):
        rn = load_db_json("names/male_first_names.json")
        return random.sample(rn, amount)

    def load_female_first_names(amount):
        file_1 = "names/female_first_names_1.json"
        file_2 = "names/female_first_names_2.json"
        rn = load_db_json(file_1) + load_db_json(file_2)
        return random.sample(rn, amount)

    def load_random_last_names(amount):
        with open(content_path("db/names/last_names.json")) as f:
            rn = json.load(f)
        return random.sample(rn, amount)

    def load_characters(path, cls):
        """Loads a Full character from JSON file.

        path: Path to main folder.
        class: Class to use in creating the character.

        This will walk through folders inside of a folder where the path leads, looking for JSONs and reading image tags off file names.
        """
        dir = content_path(path)
        dirlist = os.listdir(dir)
        content = dict()

        exist = getattr(store, "chars", {}).keys()
        exist.extend(getattr(store, "npcs", {}).keys())

        # Get to a folder with unique girl datafiles and imagefolders:
        for packfolder in os.walk(os.path.join(dir,'.')).next()[1]:
                # Load data files one after another.
                for file in os.walk(os.path.join(dir, packfolder, '.')).next()[2]:
                    if file.startswith("data") and file.endswith(".json"):
                        # Load the file:
                        in_file = os.sep.join([dir, packfolder, file])
                        char_debug("Loading from %s!"%str(in_file)) # Str call to avoid unicode
                        with open(in_file) as f:
                            ugirls = json.load(f)

                        # Apply the content of the file to the character:
                        for gd in ugirls: # We go over each dict one mainaining correct order of application:
                            if "id" not in gd:
                                # Only time we throw an error instead of writing to log.
                                raise Exception("No id was specified in %s JSON Datafile!" % str(in_file))

                            folder = id = gd["id"]
                            _path = os.sep.join([dir, packfolder, folder])
                            if os.path.isdir(_path):
                                # We load the new tags!:
                                load_tags_folder(folder, _path)

                            if id in exist:
                                continue

                            char = cls()
                            char.id = id
                            # We set the path to the character
                            # so we know where to draw images from:
                            setattr(char, "_path_to_imgfolder",
                                    "/".join(["content/{}".format(path),
                                              packfolder, folder]))

                            # Check if there is a gender:
                            if "gender" in gd:
                                char.gender = gd["gender"]

                            # @Review: We make sure all traits get applied first!
                            for key in ("blocked_traits", "ab_traits"):
                                if key in gd:
                                    _traits  = set()
                                    for t in gd[key]:
                                        if t in store.traits:
                                            _traits.add(store.traits[t])
                                        else:
                                            char_debug("%s trait is unknown for %s (In %s)!" % (t, gd["id"], key))
                                    setattr(char.traits, key, _traits)

                            # Get and normalize basetraits:
                            if "basetraits" in gd:
                                basetraits = set()
                                if gd["basetraits"]:
                                    for trait in gd["basetraits"]:
                                        if trait in traits:
                                            basetraits.add(traits[trait])
                                        else:
                                            char_debug("%s besetrait is unknown for %s!" % (trait, gd["id"]))

                                if len(basetraits) > 2:
                                    while len(basetraits) > 2:
                                        basetraits.pop()

                                # In case that we have basetraits:
                                if basetraits:
                                    char.traits.basetraits = basetraits

                                for trait in char.traits.basetraits:
                                    char.apply_trait(trait)

                            for key in ("personality", "breasts", "body", "race"):
                                if key in gd:
                                    trait = gd[key]
                                    if trait in traits:
                                        char.apply_trait(traits[trait])
                                    else:
                                        char_debug("%s %s is unknown for %s!" % (trait, key, gd["id"]))

                            if "elements" in gd:
                                for trait in gd["elements"]:
                                    if trait in traits:
                                        char.apply_trait(traits[trait])
                                    else:
                                        char_debug("%s element is unknown for %s!" % (trait, gd["id"]))

                            if "traits" in gd:
                                for trait in gd["traits"]:
                                    if trait in traits:
                                        char.apply_trait(traits[trait])
                                    else:
                                        char_debug("%s trait is unknown for %s!" % (trait, gd["id"]))

                            # if "stats" in gd:
                            #     for stat in gd["stats"]:
                            #         if stat in STATIC_CHAR.STATS:
                            #             value = gd["stats"][stat]
                            #             if stat != "luck":
                            #                 value = int(round(float(value)*char.get_max(stat))/100)
                            #             char.mod_stat(stat, value)
                            #         else:
                            #             devlog.warning("%s stat is unknown for %s!" % (stat, gd["id"]))
                            #     del gd["stats"]
                            #
                            # if "skills" in gd:
                            #     for skill, value in gd["skills"].items():
                            #         if char.stats.is_skill(skill):
                            #             char.stats.mod_full_skill(skill, value)
                            #         else:
                            #             devlog.warning("%s skill is unknown for %s!" % (skill, gd["id"]))
                            #     del gd["skills"]

                            if "default_attack_skill" in gd:
                                skill = gd["default_attack_skill"]
                                if skill in store.battle_skills:
                                    char.default_attack_skill = store.battle_skills[skill]
                                else:
                                    char_debug("%s JSON Loading func tried to apply unknown default attack skill: %s!" % (gd["id"], skill))

                            if "magic_skills" in gd:
                                # Skills can be either a list or a dict:
                                skills = gd["magic_skills"]
                                if isinstance(skills, list):
                                    pass
                                else:
                                    skills = skills.keys()
                                for skill in skills:
                                    if skill in store.battle_skills:
                                        skill = store.battle_skills[skill]
                                        char.magic_skills.append(skill)
                                    else:
                                        char_debug("%s JSON Loading func tried to apply unknown battle skill: %s!" % (gd["id"], skill))

                            for key in ("color", "what_color"):
                                if key in gd:
                                    if gd[key] in globals():
                                        color = getattr(store, gd[key])
                                    else:
                                        try:
                                            color = Color(gd[key])
                                        except:
                                            debug_str = "{} color supplied to {} is invalid!".format(gd[key], gd["id"])
                                            char_debug(debug_str)
                                            color = ivory
                                    char.say_style[key] = color

                            # Note: Location is later normalized in init method.
                            for key in ("name", "nickname", "fullname", "origin", "gold", "desc", "status", "location", "height", "full_race"):
                                if key in ["name", "nickname", "fullname"] and key in gd:
                                    if len(gd[key]) > 20:
                                        temp = gd[key][0:20]
                                        setattr(char, key, gd[key][0:20])
                                    else:
                                        setattr(char, key, gd[key])
                                elif key in gd:
                                    setattr(char, key, gd[key])

                            char.init() # Normalize!

                            # Tearing up:
                            # if "level" in gd:
                            #     initial_levelup(char, gd["level"])
                            #     del gd["level"]
                            if "tier" in gd:
                                tier = gd["tier"]
                                if isinstance(tier, dict):
                                    tier_up_to(char, **tier)
                                else:
                                    tier_up_to(char, tier)
                            else:
                                tier = uniform(.1, .4)
                                tier_up_to(char, tier)

                            item_up = gd.get("item_up", "auto")
                            if item_up == "auto":
                                if char.status == "slave":
                                    initial_item_up(char,
                                                    give_civilian_items=True,
                                                    give_bt_items=False)
                                else:
                                    initial_item_up(char,
                                                    give_civilian_items=True,
                                                    give_bt_items=True)
                            elif item_up:
                                initial_item_up(char,
                                                give_civilian_items=True,
                                                give_bt_items=True)

                            char.log_stats()

                            content[char.id] = char

        return content

    def load_random_characters():
        dir = content_path('rchars')
        dirlist = os.listdir(dir)
        content = dict()

        #exist = getattr(store, "rchars", {}).keys()

        # Loading all rgirls into the game:
        for packfolder in os.walk(os.path.join(dir,'.')).next()[1]:
            for file in os.walk(os.path.join(dir, packfolder, '.')).next()[2]:
                if file.startswith('data') and file.endswith('.json'):
                    # Load the file:
                    in_file = os.path.join(dir, packfolder, file)
                    char_debug("Loading from %s!"%str(in_file)) # Str call to avoid unicode
                    with open(in_file) as f:
                        rgirls = json.load(f)

                    for gd in rgirls:
                        # @Review: We will return dictionaries instead of blank instances of rGirl from now on!
                        # rg = rChar()
                        if "id" not in gd:
                            # Only time we throw an error instead of writing to log.
                            raise Exception("No id was specified in %s JSON Datafile!" % str(in_file))

                        folder = id = gd["id"]

                        # We load the new tags!:
                        _path = os.path.join(dir, packfolder, folder)
                        if os.path.isdir(_path):
                            load_tags_folder(folder, _path)

                        #if id in exist:
                        #    continue

                        # Set the path to the folder:
                        gd["_path_to_imgfolder"] = os.path.join("content", "rchars", packfolder, folder)

                        content[id] = gd

        return content

    def load_special_arena_fighters():
        females = getattr(store, "female_fighters", {})
        males = getattr(store, "male_fighters", {})
        exist = females.keys()
        exist.extend(males.keys())
        h = getattr(store, "hero")
        if h:
            exist.append(h.id)
        json_data_raw = load_db_json("arena_fighters.json")
        json_data = {}
        for i in json_data_raw:
            json_data[i["name"]] = i["basetraits"]

        tagdb = store.tagdb
        tags_dict = store.tags_dict

        random_traits = tuple(traits[t] for t in ["Courageous", "Aggressive", "Vicious"])
        all_elements = tuple(traits[i.id] for i in tgs.elemental)

        dir = content_path("fighters")
        genders = { "female": "females", "male": "males" }
        groups = {
            "assassins": traits["Assassin"],
            "healers": traits["Healer"],
            "knights": traits["Knight"],
            "mages": traits["Mage"],
            "maids": traits["Maid"],
            "shooters": traits["Shooter"],
            "warriors": traits["Warrior"],
            "json_adjusted": None,
        }
        for gender, base_folder in genders.iteritems():
            for group, trait in groups.iteritems():
                group_path = os.sep.join([dir, base_folder, group])
                if not os.path.isdir(group_path):
                    continue
                for folder in os.listdir(group_path):
                    _path = os.sep.join([group_path, folder])
                    if os.path.isdir(_path):
                        load_tags_folder(folder, _path)

                    # Allow database to be rebuilt but go no further.
                    if folder in exist:
                        continue
                    id = folder
                    path = os.sep.join(["content", "fighters", base_folder, group, folder])

                    elements = None
                    
                    if trait is None: # JSON
                        base = []
                        if id in json_data:
                            for t in json_data[id]:
                                if t in traits:
                                    base.append(traits[t])
                                else:
                                    char_debug("%s basetrait is unknown for %s!" % (t, id))
                    elif group == "assassins":
                        base = [trait]
                    elif group == "healers":
                        base = [trait, traits["Mage"]]
                        elements = [traits["Light"]]
                        if dice(50):
                            elements.append(traits["Water"])
                        if dice(50):
                            elements.append(traits["Air"])
                    elif group == "knights":
                        base = [trait]
                        if dice(50):
                            base.append(traits["Assassin"] if dice(50) else traits["Mage"])
                    elif group == "mages":
                        base = [trait]
                    elif group == "maids":
                        base = [trait, traits["Warrior"]]
                    elif group == "shooters":
                        base = [trait]
                        if dice(50):
                            base.append(traits["Assassin"] if dice(50) else traits["Mage"])
                    else: # group == "warriors":
                        base = [trait]

                    if elements is None:
                        if traits["Mage"] in base:
                            elements = [random.choice(all_elements)]
                        else:
                            elements = [traits["Neutral"]]
                            
                    # Create the fighter entity
                    fighter = NPC()
                    fighter._path_to_imgfolder = path
                    fighter.id = id
                    fighter.gender = gender
                    if '_' in id:
                        fighter.name = get_first_name(gender)
                        fighter.fullname = " ".join([fighter.name, get_last_name()])
                    else:
                        fighter.name = id
                        fighter.full_name = id
                    fighter.nickname = fighter.name

                    for t in random.sample(base, min(2, len(base))):
                        fighter.traits.basetraits.add(t)
                        fighter.apply_trait(t)

                    for e in random.sample(elements, max(1, len(elements)-randint(0, 7))):
                        fighter.apply_trait(e)

                    for e in random.sample(random_traits, randint(1, len(random_traits))):
                        fighter.apply_trait(e)

                    fighter.init()

                    # register the fighter in the corresponding set
                    if gender == "female":
                        females[id] = fighter
                    else: # gender == "male":
                        males[id] = fighter

        return males, females
                            
    def load_mobs():
        content = load_db_json("mobs.json")
        mobs = dict()

        for mob in content:
            if "id" not in mob:
                mob["id"] = mob["name"]
            # mob["defeated"] = 0 # We need to track if the mob was defeated for bestiary.
            mobs[mob["id"]] = mob
        return mobs

    def load_businesses():
        # Load json content
        businesses_data = load_db_json("buildings/businesses.json")
        adverts_data = load_db_json("buildings/adverts.json")

        # Populate into brothel objects:
        businesses = dict()
        idx = 0
        for business in businesses_data:
            b = Building()
            # Allowed upgrades for businesses we have not built yet!
            b.allowed_business_upgrades = business.get("allowed_business_upgrades", {})

            for key, value in business.iteritems():
                if key == "adverts":
                    b.add_adverts([adv for adv in adverts_data if adv['name'] in value])
                elif key == "build_businesses":
                    for business_data in value:
                        cls = getattr(store, business_data["class"])
                        kwargs = business_data.get("kwargs", {})

                        # Load allowed business upgrades if there are any:
                        au = [getattr(store, u) for u in kwargs.get("allowed_upgrades", [])]
                        kwargs["allowed_upgrades"] = au

                        b.add_business(cls(**kwargs))
                elif key == "allowed_businesses":
                    for business in value:
                        business = getattr(store, business)
                        b.allowed_businesses.append(business)
                elif key == "allowed_upgrades":
                    for u in value:
                        u = getattr(store, u)
                        if u not in b.allowed_upgrades:
                            b.allowed_upgrades.append(u)
                else:
                    setattr(b, key, value)

            idx += 1
            b.id = idx
            businesses[idx] = b

        return businesses

    def load_tiles():
        # Load json content
        content = load_db_json("tiles.json")
        tiles = {}
        for tile in content:
            t = Tile()
            for attr in tile:
                t.__dict__[attr] = tile[attr]
            t.init()
            tiles[t.id] = t
        return tiles

    def load_traits():
        content = list()
        folder = content_path('db/traits')
        for file in os.listdir(folder):
            # New file "content/db/traits_chances.json" crashes this function as it matches the naming scheme for the traits files, but not the content scheme
            # Added check to remove it from consideration to prevent crashing, should look into changing its name, conforming to scheme, or better check.
            #
            if file.startswith("traits") and file.endswith(".json") and "_chances" not in file:
                in_file = content_path("".join(["db/traits/", file]))
                with open(in_file) as f:
                    content.extend(json.load(f))
        traits = dict()
        for trait in content:
            t = Trait()
            for attr in trait:
                setattr(t, attr, trait[attr])
            traits[t.id] = t
        return traits

    def load_fg_areas():
        content = list()
        folder = content_path('db')
        for file in os.listdir(folder):
            if file.startswith("fg_areas") and file.endswith(".json"):
                in_file = content_path("".join(["db/", file]))
                with open(in_file) as f:
                    content.extend(json.load(f))
        areas = dict()
        for area in content:
            a = FG_Area()
            for attr in area:
                setattr(a, attr, area[attr])
            if not hasattr(a, "name"):
                a.name = a.id
            areas[a.id] = a

        return areas

    def load_items():
        items = dict()
        folder = content_path('db/items')
        content = list()

        for file in os.listdir(folder):
            if file.startswith("items") and file.endswith(".json"):
                in_file = content_path("".join(["db/items/", file]))
                with open(in_file) as f:
                    content.extend(json.load(f))

        for item in content:
            iteminst = Item()
            for attr in item:
                # We prolly want to convert to objects in case of traits:
                if attr in ("badtraits", "goodtraits"):
                    setattr(iteminst, attr, set(traits[i] for i in item[attr])) # More convinient to have these as sets...
                else:
                    setattr(iteminst, attr, item[attr])
            iteminst.init()
            items[iteminst.id] = iteminst

        return items

    def load_gifts():
        """
        Returns items dict with gift items to be used during girl_meets.
        """
        unprocessed = dict()
        content = dict()
        folder = content_path('db/items')
        for file in os.listdir(folder):
            if file.startswith("gifts") and file.endswith(".json"):
                in_file = content_path("/".join(["db/items/", file]))
                with open(in_file) as f:
                    unprocessed = json.load(f)

                for key in unprocessed:
                    item = Item()
                    item.slot = "gift"
                    item.type = "gift"
                    item.sellable = True
                    item.tier = 0
                    item.__dict__.update(key)
                    content[item.id] = item
        return content

    def load_dungeons():
        content = []
        for file in os.listdir(content_path('db')):
            if file.startswith("dungeon") and file.endswith(".json"):

                in_file = content_path("".join(["db/", file]))
                with open(in_file) as f:
                    content.extend(json.load(f))

        return { d['id']: Dungeon(**d) for d in content }

    def load_battle_skills():
        content = dict()
        battle_skills_data = load_db_json("battle_skills.json")
        fx_maps = ("attacker_action", "attacker_effects", "main_effect", "dodge_effect", "target_sprite_damage_effect", "target_damage_effect", "target_death_effect", "bg_main_effect")

        for skill in battle_skills_data:
            constructor = globals()[skill.pop("class")]
            s = constructor()

            for key, value in skill.iteritems():
                if key in fx_maps:
                    getattr(s, key).update(value)
                elif key == "_DEBUG_BE":
                    if not DEBUG_BE:
                        break
                elif key.startswith("_COMMENT"):
                    pass
                else:
                    setattr(s, key, value)
            else:
                s.init()
                content[s.name] = s

        return content


label load_resources:
    $ buildings = dict()

    python hide:
        # MC Apartments:
        # Load json content
        buildings_data = load_db_json("buildings/buildings.json")

        idx = len(businesses)
        for building in buildings_data:
            b = InvLocation()

            for key, value in building.iteritems():
                setattr(b, key, value)

            idx += 1
            b.id = idx
            buildings[idx] = b

    python: # Jail:
        jail = CityJail()
        jail.id = "City Jail"

        # Add the dungeon to the buildings list
        # Load the hero's dungeon
        # school = TrainingDungeon(load_training("training", PytTraining))
        # schools[school.name] = school
        # buildings[TrainingDungeon.NAME] = schools[TrainingDungeon.NAME]
        # if DEBUG:
        #     hero.add_building(buildings[TrainingDungeon.NAME])

    python:
        # Descriptions for: *Elements
        pytfall.desc = object()
        pytfall.desc.elements = {
        "fire": str("The wildest of all elements bringing a change that can never be undone. In a blink of an eye, it can turn any obstacle to dust leaving nothing but scorched earth in its path. In unskilled hands, it can be more dangerous to its wielders than to their enemies… Fire Element regardless to its power, is weak against Water but have the advantage versus Air."),
        "air": str("The most agile of the elements. Utilizing its transparency and omnipresence to maximum. Wielders of this element are also capable of performing lighting based spells. Being able to strike swiftly and undetected, in capable hands this element does not give opponents much time to defend themselves. The Air Element excels against Earth but struggles greatly when dealing with Fire."),
        "earth": str("The slowest and sturdiest among the elements. Known for sacrificing speed in exchange for overwhelming destructive power. Unlike other elements that leaves evidence of their devastating acts, Earth is capable of literally burying the truth. The Earth Element have the upper hand against Water, but have a hard time against the swift Air."),
        "water": str("The most mysterious among the elements. Hiding it twisted and destructive nature under the calm surface. Leaving behind only rumble and bodies as proof of it fatal capabilities. Dominating Fire with ease, the Water Element is relatively weak against Earth."),
        "darkness": str("One of the two elements born from men desires, thoughts and deeds. Fuelling itself from anger, impure thoughts and evil acts. Dwelling deep in everyone’s soul, patiently expanding, slowly consuming ones soul. Evenly matched and locked in the ethereal struggle Light and Darkness, these opposites can cause chaotic damage against each other."),
        "neutral": str("Neutral alignment is the most popular option among warriors that do not rely on use of magic. It will ensure good degree of resistance from anything some silly mage may throw at its wielder. On other hand, this is possibly the worst choice for any magic user."),
        "light": str("One of the two elements born from men desires, thoughts and deeds. Light nests itself inside everyone souls. Gaining its force from good acts and pure thoughts. Evenly matched and locked in the ethereal struggle Light and Darkness, these opposites can cause chaotic damage against each other.")
        }

    call load_building_upgrades from _call_load_building_upgrades
    return

label load_building_upgrades:
    return

# label load_json_tags:
#     python:
#         # -----------------------------------------------
#         # load image tags into the tag database
#         tl.start("Loading: JSON Tags (OldStyle)")
#         charsdir = os.path.join(gamedir, "content", "chars")
#         rcharsdir = os.path.join(gamedir, "content", "rchars")
#         jsonfiles = locate_files("tags.json", charsdir)
#         rg_jsonfiles = locate_files("tags.json", rcharsdir)
#
#         jsontagdb = TagDatabase.from_json([jsonfiles, rg_jsonfiles])
#         tagslog.info("loaded %d images from tags.json files" % jsontagdb.count_images())
#
#         del charsdir
#         del rcharsdir
#         del jsonfiles
#         del rg_jsonfiles
#
#         # raise Exception, tagdb.__dict__["tagmap"].keys()[1:10]
#         for tag in jsontagdb.tagmap.keys():
#             if tag.startswith("("):
#                 del jsontagdb.tagmap[tag]
#             try:
#                 int(tag)
#                 del jsontagdb.tagmap[tag]
#             except ValueError:
#                 pass
#         tl.end("Loading: JSON Tags (OldStyle)")
#     return

label convert_json_to_filenames:
    if not jsontagdb.tagmap:
        $ renpy.show_screen("message_screen", "No JSON tags were found!")
        return
    else:
        python:
            alltags = set(tags_dict.values())
            nums = "".join(list(str(i) for i in range(10)))
            pool = list("".join([string.ascii_lowercase, nums]))
            inverted = {v:k for k, v in tags_dict.iteritems()}
            # Carefully! We write a script to rename the image files...
            for img in jsontagdb.get_all_images():
                # Normalize the path:
                f = normalize_path("".join([gamedir, "/", img]))
                tags = list(alltags & jsontagdb.get_tags_per_path(img))
                if not tags:
                    char_debug("Deleting the file (No tags found): %s" % f)
                    os.remove(f)
                    continue
                tags.sort()
                tags = list(inverted[tag] for tag in tags)
                # New filename string:
                fn = "".join(["-".join(tags), "-", "".join(list(choice(pool) for i in range(4)))])
                if img.endswith(".png"):
                    fn = fn + ".png"
                elif img.endswith(".jpg"):
                    fn = fn + ".jpg"
                elif img.endswith(".jpeg"):
                    fn = fn + ".jpeg"
                elif img.endswith(".gif"):
                    fn = fn + ".gif"
                elif img.endswith(".webp"):
                    fn = fn + ".webp"
                oldfilename = f.split(os.sep)[-1]
                if oldfilename == fn:
                    continue
                else:
                    newdir = f.replace(oldfilename, fn)
                    try:
                        os.rename(f, newdir)
                    except:
                        char_debug("Could not find: %s"%str(f))

            # Delete the tagfiles:
            charsdir = os.path.join(gamedir, "content", "chars")
            rcharsdir = os.path.join(gamedir, "content", "rchars")
            jsonfiles = locate_files("tags.json", charsdir)
            jsonfiles = list(chain(jsonfiles, locate_files("tags.json", rcharsdir)))
            for file in jsonfiles:
                os.remove(file)
            del charsdir
            del rcharsdir
            del jsonfiles
            renpy.show_screen("message_screen", "%d images converted!" % jsontagdb.count_images())
    return
