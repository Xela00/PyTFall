init -11 python:
    def kill_char(char):
        # Attempts to remove a character from the game world.
        # This happens automatiaclly if char.health goes 0 or below.
        char._location = "After Life"
        char.alive = False
        if char in hero.chars:
            hero.corpses.append(char)
            hero.remove_char(char)
        if char in hero.team:
            hero.team.remove(char)
        gm.remove_girl(char)
    
    # Characters related:
    def get_first_name(sex="female"):
        """Gets a randomly generated first name.
        
        sex: male/female
        """
        if sex == "female":
            if not store.female_first_names:
                store.female_first_names = load_female_first_names(200)
            return store.female_first_names.pop()
        elif sex == "male":
            if not store.male_first_names:
                store.male_first_names = load_male_first_names(200)
            return store.male_first_names.pop()
        else:
            raise Exception("Unknow argument passed to get_first_name func!")
            
    def get_last_name():
        if not store.random_last_names:
            store.random_last_names = load_random_last_names(200)
        return random_last_names.pop()
        
    def get_team_name():
        if not hasattr(store, "random_team_names") or not store.random_team_names:
            store.random_team_names = load_team_names(50)
        return random_team_names.pop()
    
    def build_mob(id=None, level=1):
        mob = Mob()
        Stats = mob.STATS
        Skills = mob.stats.skills.keys()
        
        if not id:
            id = choice(mobs.keys())
            
        if id in mobs:
            data = mobs[id]
            mob.id = id
        else:
            raise Exception("Unknown id {} when creating a mob!".format(id))
        
        if "name" in data:
            mob.name = data["name"]
        else:
            mob.name = mob.id
            
        if "desc" in data:
            mob.desc = data["desc"]
        else:
            mob.desc = "A Mob!"
            
        for i in ("battle_sprite", "portrait", "origin", "locations", "base_race", "race", "front_row"):
            if i in data:
                setattr(mob, i, data[i])
        if "stats" in data:
            d = data["stats"]
            for key in d:
                if key in Stats:
                    if key != "luck":
                        value = d[key]
                        value = int(round(float(value)*100 / mob.get_max(key)))
                        mob.mod_stat(key, value)
                    elif key == "luck":
                        mob.mod_stat(key, d[key])
                else:
                    devlog.warning(str("Stat: {} for Mob with id: {} is invalid! ".format(key, id)))
                    
        if "skills" in data:
            d = data["skills"]
            for key in d:
                if key.lower() in Skills:
                    value = d[key]
                    setattr(mob, key.lower(), value * (2/3.0))
                    setattr(mob, key.capitalize(), value * (1/3.0))
                else:
                    devlog.warning(str("Skill: {} for Mob with id: {} is invalid! ".format(key, id)))
                    
        # Get and normalize basetraits:
        if "basetraits" in data:
            basetraits = set()
            if data["basetraits"]:
                for trait in data["basetraits"]:
                    if trait in traits:
                        basetraits.add(traits[trait])
                    else:
                        devlog.warning("{} besetrait is unknown for Mob {}!".format(trait, id))
                        
            if len(basetraits) > 2:
                while len(basetraits) > 2:
                    basetraits.pop()
                    
            # In case that we have basetraits:
            if basetraits:
                mob.traits.basetraits = basetraits
            
            for trait in mob.traits.basetraits:
                mob.apply_trait(trait)
            
                    
        if "traits" in data:
            d = data["traits"]
            for trait in d:
                if trait in traits:
                    trait = traits[trait]
                else:
                    devlog.warning(str("Trait: {} for Mob with id: {} is invalid! ".format(trait, id)))
                    continue
                mob.apply_trait(trait)
                
        if "default_attack_skill" in data:
            skill = data["default_attack_skill"]
            if skill in store.battle_skills:
                mob.default_attack_skill = store.battle_skills[skill]
            else:
                devlog.warning("%s Mob tried to apply unknown default attack skill: %s!" % (mob.id, skill))
                
        if "attack_skills" in data:
            d = data["attack_skills"]
            for skill in d:
                if skill in store.battle_skills:
                    mob.attack_skills.append(store.battle_skills[skill])
                else:
                    devlog.warning(str("{} Mob tried to apply unknown battle skill: {}!".format(id, skill)))
        
        if "magic_skills" in data:
            d = data["magic_skills"]
            for skill in d:
                if skill in store.battle_skills:
                    mob.magic_skills.append(store.battle_skills[skill])
                else:
                    devlog.warning(str("{} Mob tried to apply unknown battle skill: {}!".format(id, skill)))
            
        mob.init()
        
        if level != 1:
            initial_levelup(mob, level)
            
        return mob
        
    def build_rc(id=None, name=None, last_name=None, pattern=None, level=1, add_to_gameworld=True):
        ''' Creates a random character!
        id: id to choose from the rchars dictionary that holds rGirl loading data from JSON files, will be chosen at random if none availible.
        name: (String) Name for a girl to use. If None one will be chosen from randomNames file!
        last_name: Same thing only for last name :)
        pattern: Pattern to use when creating the character! (Options atm: Warrior, ServiceGirl, Prostitute, Stripper, Manager) If None, we use data or normalize in init()
        level: Level of the character...
        add_to_gameworld: Adds to characters dictionary, should always be True unless character is created not to participate in the game world...
        '''
        rg = rChar()
        Stats = rg.STATS
        Skills = rg.stats.skills.keys()
        
        if not id:
            id = choice(rchars.keys())
        
        if id in rchars:
            data = rchars[id]
            rg.id = id
        else:
            raise Exception("Unknown id {} when creating a random character!".format(id))
        
        # rg.id = id
        
        # Elements:
        if "elements" in data:
            for key in data["elements"]:
                if dice(data["elements"][key]):
                    if key not in traits:
                        key = key.split(" ")[0]
                    if key not in traits:
                        devlog.warning("Element (*Split with ' '): {} for random girl with id: {} is not a valid element for this game!".format(str(key), str(id)))
                        continue
                    rg.apply_trait(traits[key])
                    
        # Traits next:
        if "random_traits" in data:
            for trait in data["random_traits"]:
                chance = trait[1]
                trait = trait[0]
                if dice(chance):
                    if trait in traits:
                        rg.apply_trait(traits[trait])
                    else:
                        devlog.warning("Trait: {} for random girl with id: {} is not a valid trait for this game!".format(str(trait), str(id))) # Added str() call to avoid cp850 encoding
        
        # Names/Origin:
        if not name:
            if not store.female_first_names:
                store.female_first_names = load_female_first_names(200)
            rg.name = get_first_name()
        else:
            rg.name = name
            
        if not last_name:
            rg.fullname = " ".join([rg.name, get_last_name()])
            
        rg.nickname = rg.name
        
        if "origin" not in data:
            rg.origin = "Random Girl"
        
        # Status next:
        if "force_status" in data:
            if data["force_status"]:
                rg.status = data["force_status"]
            else:
                rg.status = choice(["slave", "free"])
        
        # Location if forced:
        if "force_location" in data:
            if data["force_location"]:
                rg.location = data["force_location"]
                
        # Occupations:
        if pattern: # In case if there is no pattern, 
            rg.traits.basetraits = set(create_traits_base(pattern))
            for t in rg.traits.basetraits:
                rg.apply_trait(t)
        # This is possibly temporary: TODO: Update after discussion:
        # if "init_basetraits" in data:
            # d = data["init_basetraits"]
            # if pattern not in d:
                # devlog.warning(str("{} Random Girl tried to apply blocked pattern: {}!".format(id, pattern)))
            # rg.occupation = choice(d)
        
        # Battle and Magic skills:
        if "battle_skills" in data:
            d = data["battle_skills"]
            if d in store.battle_skills:
                rg.attack_skills.append(store.battle_skills[d])
            else:
                devlog.warning(str("%s Random Girl tried to apply unknown battle skill: %s!" % (id, d)))
            
        if "magic_skills" in data:
            d = data["magic_skills"]
            for skill in d:
                if dice(skill[1]):
                    if skill[0] in store.battle_skills:
                        rg.magic_skills.append(store.battle_skills[skill[0]])
                    else:
                        devlog.warning(str("%s Random Girl tried to apply unknown battle skill: %s!" % (id, skill[0])))
                        
        # SKILLS:
        if "random_skills" in data:
            d = data["random_skills"]
            for key in d:
                if key.lower() in Skills:
                    value = randint(d[key][0], d[key][1])
                    setattr(rg, key.lower(), value * (2/3.0))
                    setattr(rg, key.capitalize(), value * (1/3.0))
                else:
                    devlog.warning(str("Skill: %s for random girl with id: %s is invalid! "%(key, id)))
                    
        # STATS:
        if "random_stats" in data:
            d = data["random_stats"]
            for key in d:
                if key in Stats:
                    if key != "luck":
                        value = randint(d[key][0], d[key][1])
                        value = int(round(float(value)*100 / rg.get_max(key)))
                        rg.mod_stat(key, value)
                    elif key == "luck":
                        rg.mod_stat(key, randint(d[key][0], d[key][1]))
                else:
                    devlog.warning(str("Stat: %s for random girl with id: %s is invalid! " % (key, id)))
        
        # Normalizing if not all stats were supplied:
        for stat in Stats:
            if stat not in rg.stats.FIXED_MAX and getattr(rg, stat) == 0:
                setattr(rg, stat, randint(10, 25))
                    
        # Rest of the expected data:
        for i in ("origin", "gold", "desc", "height", "full_race"):
            if i in data:
                setattr(rg, i, data[i])
                
        if "race" in data:
            trait = data["race"]
            if trait in traits:
                rg.apply_trait(traits[trait])
            else:
                devlog.warning("%s is not a valid race (build_rc)!" % (trait))
        
        # Colors in say screen:
        for key in ("color", "what_color"):
            if key in data:
                if data[key] in globals():
                    color = getattr(store, data[key])
                else:
                    try:
                        color = Color(data[key])
                    except:
                        devlog.warning("{} color supplied to {} is invalid!".format(gd[key], gd["id"]))
                        color = ivory
                rg.say_style[key] = color
                
        # Normalizing new girl:
        # We simply run the init method of parent class for this:
        super(rChar, rg).init()
        
        # And at last, leveling up and stats/skills applications:
        if level > 1:
            initial_levelup(rg, level)
            
        # And add to char! :)
        if add_to_gameworld:
            store.chars["_".join([rg.id, rg.name, rg.fullname.split(" ")[1]])] = rg
            
        return rg
    
    def initial_levelup(char, level, max_out_stats=False):
        """
        This levels up the character, usually when it's first created.
        """
        exp = level*(level-1)*500
        char.stats.level = 1
        char.exp = 0
        char.stats.goal = 1000
        char.stats.goal_increase = 1000

        char.exp += exp
        
        if max_out_stats:
            for stat in char.stats.stats:
                if stat not in char.stats.FIXED_MAX:
                    setattr(char, stat, char.get_max(stat))
        # -------- 
        
    def adjust_exp(char, exp):
        '''
        Adjusts experience according to a level of character.
        We will find a better way to handle experience in the future.
        '''
        if char == hero:
            if char.level < 10:
                return int(math.ceil(char.level * exp)*1.4)
            elif char.level < 30:
                return int(math.ceil(char.level * exp)*1.3)
            elif char.level < 40:
                return int(math.ceil(char.level * exp)*1.2)
            else:
                return int(math.ceil(char.level * exp)*1.1)
        elif isinstance(char, Char):
            if char.level < 10:
                return int(math.ceil(char.level * exp)*0.9)
            elif char.level < 20:
                return int(math.ceil(char.level * exp)*0.8)
            elif char.level < 30:
                return int(math.ceil(char.level * exp)*0.75)
            elif char.level < 40:
                return int(math.ceil(char.level * exp)*0.70)
            elif char.level < 50:
                return int(math.ceil(char.level * exp)*0.65)
            elif char.level < 60:
                return int(math.ceil(char.level * exp)*0.6)
            elif char.level < 70:
                return int(math.ceil(char.level * exp)*0.5)
            else:
                return int(math.ceil(char.level * exp)*0.4)
        return int(math.ceil(char.level * exp))
        
    def create_traits_base(pattern):
        """
        Mostly used for NPCs and Random Characters.
        The idea is to attempt creation of interesting and dynamic blue-prints. 
        For the future this prolly should return a matrix or a dict with prof-base and support traits separetly...
        """
        _traits = list()
        if pattern == "Warrior":
            basetrait = choice([traits["Warrior"], traits["Mage"]])
            _traits.append(basetrait)
        elif pattern == "ServiceGirl":
            _traits.append(choice([traits["Maid"], traits["Cleaner"], traits["Waitress"], traits["Bartender"]]))
        elif pattern == "Maid":
            if dice(50):
                _traits = [traits["Maid"], traits["Cleaner"]]
            else:
                _traits.append(choice([traits["Maid"], traits["Cleaner"]]))
        elif pattern == "Prostitute":
            _traits.append(traits["Prostitute"])
        elif pattern == "Stripper":
            _traits.append(traits["Stripper"])
        elif pattern == "Manager":
            _traits.append(traits["Manager"])
        elif pattern == "Dominatrix":
            _traits.append(traits["Dominatrix"])
        else:
            raise Exception("Cannot create base traits list from pattern: {}".format(pattern))
            
        # Should never return more than two traits! That is expected by callers of this func!
        return _traits
        
    def build_client(id=None, gender="male", caste="Peasant", name=None, last_name=None, pattern=None, likes=None, dislikes=None, level=1):
        """
        This function creates Customers to be used in the jobs.
        Some things are initiated in __init__ and funcs/methods that call this.
        
        - pattern: Pattern (string) to be supplied to the create_traits_base function.
        - likes: Expects a list/set/tuple of anything a client may find attractive in a worker/building/upgrade, will be added to other likes (mostly traits), usually adds a building...
        """
        client = Customer(gender, caste)
        
        if not id:
            client.id = "Client" + str(random.random())
            
        if name:
            client.name = name
        else:
            client.name = get_first_name(gender)
            
        if last_name:
            client.fullname = client.name + " " + last_name
        else:
            client.fullname = client.name + " " + get_last_name()
            
        # Patterns:
        if not pattern:
            pattern = random.sample(client.CLASSES, 1).pop()
        pattern = create_traits_base(pattern)
        for i in pattern:
            client.traits.basetraits.add(i)
            client.apply_trait(i)
            
        # Add a couple of client traits: <=== This may not be useful...
        trts = random.sample(tgs.client, randint(2, 5))
        for t in trts:
            client.apply_trait(t)
        
        # Likes:
        # Add some traits from trait groups:
        cl = set()
        cl.add(choice(tgs.breasts))
        cl.add(choice(tgs.body))
        cl.add(choice(tgs.race))
        cl = cl.union(random.sample(tgs.base, randint(1, 2)))
        cl = cl.union(random.sample(tgs.elemental, randint(2, 3)))
        cl = cl.union(random.sample(tgs.ct, randint(2, 4)))
        cl = cl.union(random.sample(tgs.sexual, randint(1, 2)))
        client.likes = cl
        
        if likes:
            client.likes = client.likes.union(likes)
            # We pick some of the traits to like/dislike at random.
        
        if level > 1:
            initial_levelup(client, level)
            
        return client
        
    def create_arena_girls():
        rgirls = store.rchars.keys()
        for i in xrange(85):
            if not rgirls: rgirls = store.rchars.keys()
            if rgirls:
                rgirl = rgirls.pop()
                arena_girl = build_rc(id=rgirl, pattern="Warrior")
                arena_girl.arena_willing = True
                arena_girl.arena_active = False # Should prolly be moved to preparation?
                arena_girl.status = "free"
                
    def copy_char(char):
        """Due to some sh!tty coding on my part, just a simple deepcopy/copy will not do :(
        
        This func cannot be used to make a playable character that can properly interact with the game world.
        """
        if isinstance(char, PytGroup):
            char = char._first

        # new = deepcopy(char)
        # Trying to improve the performace:
        new = pickle.loads(pickle.dumps(char, -1))
        
        # One More Attempt through class Instantiation, does not work yet:
        # new = char.__class__()
        # Stats copy (Only for the new instance attempt)
        # new.id = char.id
        # new.location = shallowcopy(char.location)
        # new.stats = shallowcopy(char.stats)
        # new.stats.instance = new
        # # Effects (Also, just for the new instance attempt)
        # if hasattr(char, "effects"):
            # new.effects = char.effects.copy()
        
        # Traits copy:
        real_traits = list(traits[t] for t in [trait.id for trait in char.traits])
        new.traits[:] = real_traits
        new.traits.normal = char.traits.normal.copy()
        new.traits.items = char.traits.items.copy()
        new.traits.ab_traits = char.traits.ab_traits.copy()
        new.traits.blocked_traits = char.traits.blocked_traits.copy()
        new.traits.basetraits = char.traits.basetraits.copy()
        
        # Equipment slots:
        new.eqslots = char.eqslots.copy()
        
        # Skills:
        real_attack_skills = list(battle_skills[s] for s in [skill.name for skill in char.attack_skills])
        new.attack_skills[:] = real_attack_skills
        new.attack_skills.normal = char.attack_skills.normal.copy()
        new.attack_skills.items = char.attack_skills.items.copy()
        
        real_magic_skills = list(battle_skills[s] for s in [skill.name for skill in char.magic_skills])
        new.magic_skills[:] = real_magic_skills
        new.magic_skills.normal = char.magic_skills.normal.copy()
        new.magic_skills.items = char.magic_skills.items.copy()
        
        return new

    def set_char_to_work(char, building, job=False):
        """Attempts to find the best possible job to the char in given building.
        
        For now it just randomly picks any fitting job or sets to None.
        In the future, this should find the best possible job and set the char to it.
        
        Note: Due to older logic, this function expects job argument to be None when a character is made jobless by player input or game logic!
        """
        if job is False:
            available_jobs = list(j for j in building.jobs if j.all_occs & char.occupations)
            job = choice(available_jobs) if available_jobs else None
        
        # We want to remove char as a building manager if he/she leave the post, we don't do that when char is set to rest or auto-rest.
        if building.manager == char:
            sj = store.simple_jobs
            if job not in (sj["Manager"], sj["Rest"], sj["AutoRest"]):
                building.manager = None
                        
        char.action = job
        # We prolly still want to set a workplace...
        char.workplace = building
        
        if job is None:
            return
        
        if hasattr(building, "all_workers"):
            if char not in building.all_workers:
                building.all_workers.append(char)
                
        # Make sure that the manager is set:
        if job == simple_jobs["Manager"]:
            building.manager = char
