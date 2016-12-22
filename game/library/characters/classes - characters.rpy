# Characters classes and methods:
init -9 python:
    ###### Character Helpers ######
    class SmartTracker(collections.MutableSequence):
        def __init__(self, instance, be_skill=True):
            self.instance = instance # Owner of this object, this is being instanciated as character.magic_skills = SmartTracker(character)
            self.normal = set() # Normal we concider anything that's been applied by normal game operations like events, loading routines and etc.
            self.items = dict() # Stuff that's been applied through items, it's a counter as multiple items can apply the same thing (like a trait).
            self.be_skill = be_skill # If we expect a be skill or similar mode.
            self.list = _list()

        def __len__(self): return len(self.list)

        def __getitem__(self, i): return self.list[i]

        def __delitem__(self, i): del self.list[i]

        def __setitem__(self, i, v):
            self.list[i] = v

        def insert(self, i, v):
            self.list.insert(i, v)

        def __str__(self):
            return str(self.list)

        def append(self, item, normal=True):
            # Overwriting default list method, always assumed normal game operations and never adding through items.
            # ==> For battle & magic skills:
            if self.be_skill:
                if isinstance(item, basestring):
                    if item in store.battle_skills:
                        item = store.battle_skills[item]
                    else:
                        devlog.warning("Tried to apply unknown skill %s to %s!" % (item, self.instance.__class__))
                        return
            if normal: #  Item applied by anything other than that
                self.normal.add(item)
            else:
                self.items[item] = self.items.get(item, 0) + 1

            # The above is enough for magic/battle skills, but for traits... we need to know if the effects should be applied.
            if item in self.normal or self.items.get(item, 0) > 0:
                if not item in self.list:
                    self.list.append(item)
                    return True

        def remove(self, item, normal=True):
            # Overwriting default list method.
            # ==> For battle & magic skills:
            if self.be_skill:
                if isinstance(item, basestring):
                    if item in store.battle_skills:
                        item = store.battle_skills[item]
                    else:
                        devlog.warning("Tried to remove unknown skill %s from %s!" % (item, self.instance.__class__))
                        return
            if normal:
                if item in self.normal:
                    self.normal.remove(item)
            else:
                self.items[item] = self.items.get(item, 0) - 1

            # The above is enough for magic/battle skills, but for traits... we need to know if the effects should be applied.
            if not item in self.normal and self.items.get(item, 0) <= 0:
                if item in self.list:
                    self.list.remove(item)
                    return True


    class SmartTrackerOld(_list):
        """
        Basically a smart list that tracks anything that can be added by items and events/game.
        Prevents removal when unequipping items and/or other types of ralated errors/bugs.
        """
        def __init__(self, instance, be_skill=True):
            _list.__init__(self)
            self.instance = instance # Owner of this object, this is being instanciated as character.magic_skills = SmartTracker(character)
            self.normal = set() # Normal we concider anything that's been applied by normal game operations like events, loading routines and etc.
            self.items = dict() # Stuff that's been applied through items, it's a counter as multiple items can apply the same thing (like a trait).
            self.be_skill = be_skill # If we expect a be skill or similar mode.
            # raise Exception("zzzz", self.instance)

        def __getattr__(self, item):
            raise AttributeError("%s object has no attribute named %r, __dict__: %s" %
                                 (self.__class__.__name__, item, self.__dict__))

        def set_instance(self, instance):
            self.instance = instance

        def append(self, item, normal=True):
            # Overwriting default list method, always assumed normal game operations and never adding through items.
            # ==> For battle & magic skills:
            if self.be_skill:
                if isinstance(item, basestring):
                    if item in store.battle_skills:
                        item = store.battle_skills[item]
                    else:
                        devlog.warning("Tried to apply unknown skill %s to %s!" % (item, self.instance.__class__))
                        return
            if normal: #  Item applied by anything other than that
                self.normal.add(item)
            else:
                self.items[item] = self.items.get(item, 0) + 1

            # The above is enough for magic/battle skills, but for traits... we need to know if the effects should be applied.
            if item in self.normal or self.items.get(item, 0) > 0:
                if not item in self:
                    super(SmartTracker, self).append(item)
                    return True

        def remove(self, item, normal=True):
            # Overwriting default list method.
            # ==> For battle & magic skills:
            if self.be_skill:
                if isinstance(item, basestring):
                    if item in store.battle_skills:
                        item = store.battle_skills[item]
                    else:
                        devlog.warning("Tried to remove unknown skill %s from %s!" % (item, self.instance.__class__))
                        return
            if normal:
                if item in self.normal:
                    self.normal.remove(item)
            else:
                self.items[item] = self.items.get(item, 0) - 1

            # The above is enough for magic/battle skills, but for traits... we need to know if the effects should be applied.
            if not item in self.normal and self.items.get(item, 0) <= 0:
                if item in self:
                    super(SmartTracker, self).remove(item)
                    return True


    class Traits(SmartTracker):
        def __init__(self, *args, **kwargs):
            """
            Trait effects are being applied per level on activation of a trait and on level-ups.
            """
            # raise Exception(args[0])
            # SmartTracker.__init__(self, args[0])
            super(Traits, self).__init__(args[0])
            # self.instance = args[0]

            self.ab_traits = set()  # Permenatly blocked traits (Absolute Block Traits)
            self.blocked_traits = set()  # Blocked traits

            self.basetraits = set() # A set with basetraits (2 maximum)

            # if not hasattr(self, "be_skills"):
                # raise Exception("Meow~")

        def __getattr__(self, item):
            raise AttributeError("%s object has no attribute named %r" %
                                 (self.__class__.__name__, item))

        def __contains__(self, item):
            if isinstance(item, basestring):
                if item in store.traits: item = store.traits[item]
                else: return False

            return super(Traits, self).__contains__(item)

        @property
        def base_to_string(self):
            return ", ".join(sorted(list(str(t) for t in self.basetraits)))

        def apply(self, trait, truetrait=True):
            """
            Activates trait and applies it's effects all the way up to a current level of the characters.
            Truetraits basially means that the trait is not applied throught items (Jobs, GameStart, Events and etc.)
            """
            # If we got a string with a traits name. Let the game throw an error otherwise.
            if not isinstance(trait, Trait):
                trait = store.traits[trait]
            char = self.instance

            # All the checks required to make sure we can even apply this fucking trait: ======================>>
            if trait.sex not in ["unisex", char.gender]:
                return

            # We cannot allow "Neutral" element to be applied if there is at least one element present already:
            if trait.elemental and trait.id == "Neutral":
                if self.instance.elements:
                    return

            # Blocked traits:
            if trait in self.ab_traits | self.blocked_traits:
                return

            # Unique Traits:
            if trait.personality and list(t for t in self if t.personality):
                return
            if trait.race and list(t for t in self if t.race):
                return
            if trait.breasts and list(t for t in self if t.breasts):
                return
            if trait.body and list(t for t in self if t.body):
                return
            if trait.personality:
                char.personality = trait
            if trait.race:
                char.race = trait
            if trait.breasts:
                char.breasts = trait
            if trait.body:
                char.body = trait

            # We need to make sure that no more than x + len(basetraits) of basetraits can be applied, atm x is 4:
            if trait.basetrait:
                if trait not in self.basetraits:
                    if trait.higher_tiers and list(traits[t] for t in trait.higher_tiers if t in self.basetraits):
                        allowed = 4 + len(self.basetraits)
                        bt = len(list(t for t in self if t.basetrait))
                        if bt == allowed:
                            return
                        elif bt > allowed:
                            devlog.warning("BASE TRAITS OVER THE ALLOWED MAX! CHECK Traits.apply method!")
                            return

            if not super(Traits, self).append(trait, truetrait):
                return

            # If we got here... we can apply the effect? Maybe? Please? Just maybe? I am seriouslly pissed at this system right now... ===========>>>

            stats = self.instance.stats
            # If the trait is a basetrait:
            if trait in self.basetraits:
                multiplier = 2 if len(self.basetraits) == 1 else 1
                for stat in trait.init_lvlmax: # Mod value setting
                    if stat in stats:
                        stats.lvl_max[stat] += trait.init_lvlmax[stat] * multiplier
                    else:
                        msg = "'%s' trait tried to apply unknown init lvl max stat: %s!"
                        devlog.warning(str(msg % (trait.id, stat)))

                for stat in trait.init_max: # Mod value setting
                    if stat in stats:
                        stats.max[stat] += trait.init_max[stat] * multiplier
                    else:
                        msg = "'%s' trait tried to apply unknown init max stat: %s!"
                        devlog.warning(str(msg % (trait.id, stat)))

                for stat in trait.init_mod: # Mod value setting
                    if stat in stats:
                        stats.stats[stat] += trait.init_mod[stat] * multiplier
                    else:
                        msg = "'%s' trait tried to apply unknown init max stat: %s!"
                        devlog.warning(str(msg % (trait.id, stat)))

                for skill in trait.init_skills: # Mod value setting
                    if skill in stats.skills:
                        stats.skills[skill][0] += trait.init_skills[skill][0] * multiplier
                        stats.skills[skill][1] += trait.init_skills[skill][1] * multiplier
                    else:
                        msg = "'%s' trait tried to apply unknown init skillt: %s!"
                        devlog.warning(str(msg % (trait.id, skill)))

            # Only for body traits:
            if trait.body:
                if trait.mod_ap:
                    self.instance.baseAP += trait.mod_ap

            for key in trait.max:
                if key in stats.max:
                   stats.max[key] += trait.max[key]
                else:
                    msg = "'%s' trait tried to apply unknown max stat: %s!"
                    devlog.warning(str(msg % (trait.id, key)))

            for key in trait.min:
                # Preventing traits from messing up minimums of stats by pushing them into negative territory. @Review: No longer required as per new stats code.
                if key in stats.min:
                    stats.min[key] += trait.min[key]
                else:
                    msg = "'%s' trait tried to apply unknown min stat: %s!"
                    devlog.warning(str(msg % (trait.id, key)))

            for entry in trait.blocks:
                if entry in traits:
                    self.blocked_traits.add(traits[entry])
                else:
                    devlog.warning(str("Tried to block unknown trait: %s, id: %s, class: %s" % (entry, char.id, char.__class__)))

            # For now just the girls get effects...
            if hasattr(char, "effects"):
                for entry in trait.effects:
                    char.enable_effect(entry)

            if trait.mod_stats:
                if hasattr(char, "upkeep"):
                    char.upkeep += trait.mod_stats.get("upkeep", [0, 0])[0]
                if hasattr(char, "disposition"):
                    char.disposition += trait.mod_stats.get("disposition", [0, 0])[0]
                for level in xrange(char.level+1):
                    char.stats.apply_trait_statsmod(trait)

            if hasattr(trait, "mod_skills"):
                for key in trait.mod_skills:
                    if key in char.SKILLS:
                        sm = stats.skills_multipliers[key] # skillz muplties
                        m = trait.mod_skills[key] # mod
                        sm[0] += m[0]
                        sm[1] += m[1]
                        sm[2] += m[2]
                    else:
                        msg = "'%s' trait tried to apply unknown skill: %s!"
                        devlog.warning(str(msg % (trait.id, key)))

            # Adding resisting elements and attacks:
            for i in trait.resist:
                self.instance.resist.append(i)

            # NEVER ALLOW NEUTRAL ELEMENT WITH ANOTHER ELEMENT!
            if trait.elemental:
                if trait.id != "Neutral" and traits["Neutral"] in self:
                    self.remove(traits["Neutral"])

            # Finally, make sure stats are working:
            char.stats.normalize_stats()

        def remove(self, trait, truetrait=True):
            """
            Removes trait and removes it's effects gained up to a current level of the characters.
            Truetraits basially means that the trait is not applied throught items (Jobs, GameStart, Events and etc.)
            """
            # If we got a string with a traits name. Let the game throw an error otherwise.
            if not isinstance(trait, Trait):
                trait = store.traits[trait]
            char = self.instance

            if trait.sex not in ["unisex", char.gender]:
                return

            # We Never want to remove a base trait:
            if trait in self.basetraits:
                return

            # WE NEVER REMOVE PERMANENT TRAITS FAMILY:
            if any([trait.personality, trait.race, trait.breasts, trait.body]):
                return

            if not super(Traits, self).remove(trait, truetrait):
                return

            stats = char.stats
            for key in trait.max:
                if key in stats.max:
                    stats.max[key] -= trait.max[key]
                else:
                    devlog.warning(str('Maximum Value: %s for Trait: %s does not exist' % (key, trait.id)))

            for key in trait.min:
                if key in stats.min:
                    # Preventing traits from messing up minimums of stats by pushing them into negative territory. @Review: No longer required as per new stats code.
                    # if(self.stats.min[key] - trait.min[key]) >= 0:
                    stats.min[key] -= trait.min[key]
                else:
                    msg = "'%s' trait tried to apply unknown min stat: %s!"
                    devlog.warning(str(msg % (trait.id, key)))

            if trait.blocks:
                _traits = set()
                for entry in trait.blocks:
                    if entry in traits:
                        _traits.add(traits[entry])
                    else:
                        devlog.warning(str("Tried to block unknown trait: %s, id: %s, class: %s" % (entry, char.id, char.__class__)))
                self.blocked_traits -= _traits

            # Ensure that blocks forced by other traits were not removed:
            for entry in self:
                self.blocked_traits = self.blocked_traits.union(entry.blocks)

            # For now just the girls get effects...
            if isinstance(char, Char):
                for entry in trait.effects:
                    self.instance.disable_effect(entry)

            if trait.mod_stats:
                if hasattr(char, "upkeep"):
                    char.upkeep -= trait.mod_stats.get("upkeep", [0, 0])[0]
                if hasattr(char, "disposition"):
                    char.disposition -= trait.mod_stats.get("disposition", [0, 0])[0]
                for level in xrange(char.level+1):
                    char.stats.apply_trait_statsmod(trait, reverse=True)

            if hasattr(trait, "mod_skills"):
                for key in trait.mod_skills:
                    if key in char.SKILLS:
                        sm = stats.skills_multipliers[key] # skillz muplties
                        m = trait.mod_skills[key] # mod
                        sm[0] -= m[0]
                        sm[1] -= m[1]
                        sm[2] -= m[2]
                    else:
                        msg = "'%s' trait tried to apply unknown skill: %s!"
                        devlog.warning(str(msg % (trait.id, key)))

            # Remove resisting elements and attacks:
            for i in trait.resist:
                self.instance.resist.remove(i)
                # We need to check if one of the traits still may apply resistance:
                # for t in self:
                    # if i in t.resist:
                        # self.instance.resist.append(i)
                        # break

            # We add the Neutral element if there are no elements left at all...
            if not self.instance.elements:
                self.apply("Neutral")

            # Finally, make sure stats are working:
            char.stats.normalize_stats()


    class Rank(_object): # Will not be used for the next release...
        """
        Ranks, currently not in use in the game.
        """
        WhRANKS = OrderedDict()
        WhRANKS["0"]=dict(name=('No Rank: Kirimise', '(Almost beggar)'), price=0)
        WhRANKS["1"]=dict(name=("Rank 1: Heya-Mochi", "(Low-class prostitute)"), skills={"oral": 10, "vaginal": 10, "anal": 5}, total_skill=100, price=1000, exp=10000) # note: refinement is not a stat anymore!
        WhRANKS["2"]=dict(name=("Rank 2: Zashiki-Mochi", "(Middle-class Prostitute"), skills={"oral": 25, "vaginal": 15, "anal": 15}, total_skill=300, price=3000, exp=25000)
        WhRANKS["3"]=dict(name=("Rank 3: Tsuke-Mawashi", "(Courtesan)"), skills={"oral": 55, "vaginal": 40, "anal": 25}, total_skill=600, price=5000, exp=50000)
        WhRANKS["4"]=dict(name=("Rank 4: Chûsan", "(Famous)"), skills={"oral": 100, "vaginal": 80, "anal": 50}, total_skill=1000, stats={"refinement": 100}, price=7500, exp=100000)
        WhRANKS["5"]=dict(name=("Rank 5: Yobidashi", "(High-Class Courtesan)"), skills={"oral": 250, "vaginal": 150, "anal": 130}, total_skill=1250, stats={"refinement": 150}, price=10000, exp=250000)
        WhRANKS["6"]=dict(name=("Rank 6: Koshi", "(Nation famous)"), skills={"oral": 500, "vaginal": 500, "anal": 500}, total_skill=2500, stats={"refinement": 500}, price=25000, exp=400000)
        WhRANKS["7"]=dict(name=("Rank 7: Tayu", "(Legendary)"), skills={"oral": 1500, "vaginal": 1500, "anal": 1500}, total_skill=5000, stats={"refinement": 800}, price=50000, exp=800000)

        WaRANKS = OrderedDict()
        WaRANKS["0"]=dict(name=('No Rank', 'Nub with a stick...'), price=0)
        WaRANKS["1"]=dict(name=("Rank 1", "Thug"), skills={}, total_skill=100, stats={}, price=1000, exp=10000)
        WaRANKS["2"]=dict(name=("Rank 2", "Sword Sister"), skills={}, total_skill=300, stats={}, price=3000, exp=25000)
        WaRANKS["3"]=dict(name=("Rank 3", "War Maiden"), skills={}, total_skill=600, stats={}, price=5000, exp=50000)
        WaRANKS["4"]=dict(name=("Rank 4", "Famous"), skills={}, total_skill=1000, stats={}, price=7500, exp=100000)
        WaRANKS["5"]=dict(name=("Rank 5", "War Maiden"), skills={}, total_skill=1250, stats={}, price=10000, exp=250000)
        WaRANKS["6"]=dict(name=("Rank 6", "Valkyrie"), skills={}, total_skill=2500, stats={}, price=25000, exp=400000)
        WaRANKS["7"]=dict(name=("Rank 7", "Legendary"), skills={}, total_skill=5000, stats={}, price=50000, exp=800000)

        StRANKS = OrderedDict()
        StRANKS["0"]=dict(name=('No Rank', 'Nub wiggling her ass...'), price=0)
        StRANKS["1"]=dict(name=("Rank 1", "Stripper"), skills={"strip": 50}, total_skill=100, price=1000, exp=10000)
        StRANKS["2"]=dict(name=("Rank 2", "Lap Dancer"), skills={"strip": 100}, total_skill=300, price=3000, exp=25000)
        StRANKS["3"]=dict(name=("Rank 3", "Seductress"), skills={"strip": 250}, total_skill=600, price=5000, exp=50000)
        StRANKS["4"]=dict(name=("Rank 4", "Famous"), skills={"strip": 500}, total_skill=1000, stats={}, price=7500, exp=100000)
        StRANKS["5"]=dict(name=("Rank 5", "Ecdysiastn"), skills={"strip": 1000}, total_skill=1250, stats={}, price=10000, exp=250000)
        StRANKS["6"]=dict(name=("Rank 6", "Temptress"), skills={"strip": 2500}, total_skill=2500, stats={}, price=25000, exp=400000)
        StRANKS["7"]=dict(name=("Rank 7", "Legendary"), skills={"strip": 5000}, total_skill=5000, stats={}, price=50000, exp=800000)

        SgRANKS = OrderedDict()
        SgRANKS["0"]=dict(name=('No Rank', 'Nub breaking the china...'), price=0)
        SgRANKS["1"]=dict(name=("Rank 1", "Wench"), skills={"service": 50}, total_skill=100, price=1000, exp=10000)
        SgRANKS["2"]=dict(name=("Rank 2", "Servant"), skills={"service": 100}, total_skill=300, price=3000, exp=25000)
        SgRANKS["3"]=dict(name=("Rank 3", "Maid"), skills={"service": 250}, total_skill=600, price=5000, exp=50000)
        SgRANKS["4"]=dict(name=("Rank 4", "Chambermaid"), skills={"service": 500}, total_skill=1000, stats={}, price=7500, exp=100000)
        SgRANKS["5"]=dict(name=("Rank 5", "Housekeeper"), skills={"service": 1000}, total_skill=1250, stats={}, price=10000, exp=250000)
        SgRANKS["6"]=dict(name=("Rank 6", "Famous"), skills={"service": 2500}, total_skill=2500, stats={}, price=25000, exp=400000)
        SgRANKS["7"]=dict(name=("Rank 7", "Legendary"), skills={"service": 5000}, total_skill=5000, stats={}, price=50000, exp=800000)
        """
        Handles ranks for characters. Stores all related data and returns the correct rank/requirement/updates.
        """
        def __init__(self):
            self.current_rank = None
            self.n = None


    class Finances(_object):
        """Helper class that handles finance related matters in order to reduce the size of Characters/Buildings classes.

        TODO: This is fairly old, I should be able to do better now.
        TODO: Naming of methods could be better.
        """
        def __init__(self, *args, **kwargs):
            """
            instance = reference to Character object
            """
            self.instance = args[0]

            """
            Income/expense log consists of personal, wages and tips dicts.
            Private = Private (logs with acutal gold increases/decreases).
            Work(Wages) = Earned but not settled (just a log to be settled later in next day methods).
            Tips = Same as wages, only for tips.
            Cost = What did this girl cost to the player over the day.
            """
            self.game_fin_log = dict()
            self.daily_income_log = dict(work=dict(), tips=dict(), private=dict())
            self.daily_expense_log = dict(work=dict(), private=dict(), cost=dict())
            self.income_tax_debt = 0
            self.property_tax_debt = 0

        # Logging data:
        def log_work_income(self, value, kind):
            """This is for Buildings.
            """
            self.daily_income_log["work"][kind] = self.daily_income_log["work"].get(kind, 0) + int(round(value))

        def log_work_expense(self, value, kind):
            """This is for Buildings.
            """
            self.daily_expense_log["work"][kind] = self.daily_expense_log["work"].get(kind, 0) + int(round(value))

        def log_wage(self, value, kind):
            self.daily_income_log["work"][kind] = self.daily_income_log["work"].get(kind, 0) + int(round(value))

        def log_tips(self, value, kind):
            if not "tips" in self.daily_income_log:
                self.daily_income_log["tips"] = dict()
            self.daily_income_log["tips"][kind] = self.daily_income_log["tips"].get(kind, 0) + int(round(value))

        def log_income(self, value, kind):
            """Logs private Income.
            """
            self.daily_income_log["private"][kind] = self.daily_income_log["private"].get(kind, 0) + int(round(value))

        def log_expense(self, value, kind):
            """Logs private expence.
            """
            self.daily_expense_log["private"][kind] = self.daily_expense_log["private"].get(kind, 0) + int(round(value))

        def log_cost(self, value, kind):
            """
            This logs how much an object (usually a character) has cost the player over the day.
            This is a part of that objects class and is being recorded to players class as a sum of all characters.
            While not technically an expence to a character, it is being recorded to that dict.
            """
            self.daily_expense_log["cost"][kind] = self.daily_expense_log["cost"].get(kind, 0) + int(round(value))

        def take_money(self, value, reason="Other"):
            value = int(round(value))
            if value <= self.instance.gold:
                self.log_expense(value, reason)
                self.instance.gold -= value
                return True
            else:
                return False

        def add_money(self, value, reason="Other"):
            value = int(round(value))
            self.log_income(value, reason)
            self.instance.gold += value

        # Retrieving data:
        def get_work_income(self, kind="all", day=None):
            """Retrieve work income (for buildings/chars?)

            kind = "all" means any income earned on the day.
            """
            if day and day >= store.day:
                raise Exception("Day on income retrieval must be lower than the current day!")

            if not day:
                d = self.daily_income_log["work"]
            else:
                d = self.game_fin_log[str(day)][0]["work"]

            if kind == "all":
                return sum(val for val in d.values())
            elif kind in d:
                return d[kind]
            else:
                raise Exception("Income kind: {} is not valid!".format(kind))

        def get_total_taxes(self, days):
            char = self.instance
            income = dict()
            businesses = [b for b in char.buildings if hasattr(b, "fin")]
            for b in businesses:
                for _day in b.fin.game_fin_log:
                    if int(_day) > day - days:
                        for key in b.fin.game_fin_log[_day][0]["private"]:
                            income[key] = income.get(key, 0) + b.fin.game_fin_log[_day][0]["private"][key]
                        for key in b.fin.game_fin_log[_day][0]["work"]:
                            income[key] = income.get(key, 0) + b.fin.game_fin_log[_day][0]["work"][key]

            income = sum(income.values())

            if income <= 5000:
                tax = 0
            elif income <= 25000:
                tax = int(round(income*0.1))
            elif income <= 50000:
                tax = int(round(income*0.2))
            elif income <= 100000:
                tax = int(round(income*0.3))
            elif income <= 200000:
                tax = int(round(income*0.4))
            else:
                tax = int(round(income*0.45))

            for b in businesses:
                tax += int(b.price*0.04)
            for ch in char.chars:
                if ch.status == "slave":
                    tax += int(ch.fin.get_price()*0.05)

            return tax
        # ================================>
        # Rest
        def expects_wage(self):
            """
            Amount of money each character expects to get paid for her skillset.
            """
            # TODO: To be revised after SKILLS!
            char = self.instance

            wage = 100
            if "Dedicated" in char.traits: # the trait decreases wage, this check should remain after revising! - DarkTl
                wage = int(wage*0.65)

            if 'Prostitute' in char.traits:
                bw = 5 # Base wage
                sm = bw*((1+char.charisma/5 + char.reputation/4 + char.fame/4)/100) # Stats Mod  + char.refinement/5
                osm = (char.anal + char.vaginal + char.oral + char.bdsm) / 4 * (char.rank / 10 + 1) # Occupational Stats M

                wage =  (sm*osm)/5 + bw

            elif 'Dominatrix' in char.traits:
                bw = 2
                sm = bw*(char.character/4 + char.reputation/4 + char.fame/4) # + char.refinement/5
                osm = char.vaginal*char.attack/100

                wage = (sm+osm)/5 + bw

            elif 'Stripper' in char.traits:
                bw = 2
                sm = bw*(char.charisma/4 + char.reputation/4 + char.fame/4) # + char.refinement/5
                osm = char.strip*char.agility/100

                wage = (sm+osm)/5 + bw

            # elif 'Server' in char.occupations:
                # bw = 10
                # sm = char.charisma/5 + char.agility/2 + char.refinement/4
                # osm = char.service*bw

                # wage = sm/2+osm/100

            # elif 'Warrior' in char.occupations or isinstance(self.instance, Player):
                # # Here we include MC for the attack event as well.
                # bw = 15
                # sm = char.agility/100+char.fame/4 + char.reputation/3
                # osm = (char.attack + char.defence + char.magic/2)/100 + bw

                # wage = bw+sm*osm

            # else:
                # for stat in char.stats:
                    # if stat not in ["disposition", "joy", "health", "vitality"]: #, "mood"
                        # wage += getattr(char, stat)
                # wage = wage/2

            # # Normalize:
            # wage = int(wage)
            # if wage < 20:
                # wage = 20

            return wage

        def settle_wage(self):
            """
            Settle wages between girls and player.
            Called during next day method per each individual girl.
            Right now being used for Businesses only, all FG profit goes directly into MC's pockets.
            """
            char = self.instance

            if self.wage_conditions():
                total_wage = sum(self.daily_income_log["work"].values())
                hero.add_money(total_wage, reason="Businesses")

                if char.status != "slave":
                    if char.wagemod >= 100:
                        amount = int(self.expects_wage() + int(round(self.expects_wage()*0.01*(char.wagemod-100))))
                        if hero.take_money(amount, reason="Wages"):
                            self.add_money(amount, reason="Wages")
                            self.log_cost(amount, "Wages")
                            if isinstance(char.location, Building):
                                char.location.fin.log_work_expense(amount, "Wages")
                            if char.disposition < 700:
                                char.disposition += int(round((char.wagemod-100)*0.1))
                            char.joy += int(round((char.wagemod-100)*0.1))

                    elif char.wagemod< 100:
                        amount = int(self.expects_wage() - int(round(self.expects_wage()*0.01*(100-char.wagemod))))
                        if hero.take_money(amount, reason="Wages"):
                            self.log_cost(amount, "Wages")
                            self.add_money(amount, reason="Wages")
                            if isinstance(char.location, Building):
                                char.location.fin.log_work_expense(amount, "Wages")

                else:
                    amount = int(self.expects_wage()*0.01*(char.wagemod))
                    if hero.take_money(amount, reason="Wages"):
                        self.add_money(amount, reason="Wages")
                        self.log_cost(amount, "Wages")
                        if isinstance(char.location, Building):
                            char.location.fin.log_work_expense(amount, "Wages")
                        if char.disposition < 700:
                            char.disposition += int(round((char.wagemod)*0.2))
                        char.joy += int(round((char.wagemod)*0.2))

        def wage_conditions(self):
            char = self.instance
            return char.action not in ["Rest", "AutoRest"] or (char.location != "Streets" and not in_training_location(char))

        def get_price(self):
            # TODO: To be revised after skills are added!
            char = self.instance
            if char.status == 'slave':
                if 'Prostitute' in char.traits:
                    bp = 3000 # Base Price
                    sp = 2 * (char.charisma + char.reputation + char.fame + char.constitution + char.character) #+ 3 * char.refinement
                    ssp = 2 * (char.anal + char.vaginal + char.oral + char.bdsm) # Sex Price
                    if sp > 1200:
                        sp = sp * 1.2
                    if ssp > 850:
                        ssp = ssp * 1.4
                    price = bp + sp + ssp
                    return int(price)
                elif 'Dominatrix' in char.traits:
                    bp = 3900 # Base Price
                    sp = 2 * (char.character + char.reputation + char.fame + char.constitution + char.attack) #+ 3 * char.refinement
                    ssp = 2 * 4 * (char.character)
                    if sp > 1200:
                        sp = sp * 1.2
                    if ssp > 850:
                        ssp = ssp * 1.4
                    price = bp + sp + ssp
                    return int(price)
                elif 'Stripper' in char.traits:
                    bp = 3900 # Base Price
                    sp = 2 * (char.charisma + char.reputation + char.fame + char.constitution + char.character)
                    ssp = 2 * 4 * (char.strip) # Sex Price
                    if sp > 1200:
                        sp = sp * 1.2
                    if ssp > 850:
                        ssp = ssp * 1.4
                    price = bp + sp + ssp
                    return int(price)
                # elif 'Server' in char.occupations:
                    # bp = 3500 # Base Price
                    # sp = 2 * (char.charisma + char.reputation + char.fame + char.constitution + char.character) + 3 * char.refinement
                    # ssp = 2 * 4 * (char.service) # Sex Price
                    # if sp > 1200:
                        # sp = sp * 1.2
                    # if ssp > 850:
                        # ssp = ssp * 1.4
                    # price = bp + sp + ssp
                    # return int(price)
                else:
                    bp = 3000 # Base Price
                    sp = 0
                    for stat in char.stats:
                        if stat not in ["disposition", "joy", "health", "vitality"]: #, "mood"
                            sp += getattr(char, stat)

                    if sp > 1200:
                        sp = sp * 1.2

                    price = bp + sp
                    return int(price)

            else:
                devlog.warning("get_price for {} was ran even though character is free !".format(char.id))
            return 1000


        def get_upkeep(self):
            # TODO: To be revised after skills are added!
            char = self.instance

            if char.status == 'slave':
                if 'Prostitute' in char.traits:
                    bu = 20 * char.rank
                    su = char.charisma/10 + char.constitution/5 + char.reputation/2 + char.fame/2 # + char.refinement*1.5  Stats Upkeep
                    ssu = char.anal/8 + char.vaginal/8 + char.oral/8 + char.bdsm/8

                    return int(bu + su + ssu + char.upkeep)

                elif 'Stripper' in char.traits:
                    bu = 3 * char.strip
                    su = char.charisma/10 + char.constitution/5 + char.reputation/2 + char.fame/2 # + char.refinement*1.5 Stats Upkeep

                    return int(bu + su + char.upkeep)

                elif 'Dominatrix' in char.traits:
                    bu = 3 * char.character
                    su = char.attack/10 + char.constitution/5 + char.reputation/2 + char.fame/2

                    return int(bu + su + char.upkeep)

                # elif 'Server' in char.occupations:
                    # bu = 3 * char.service
                    # su = char.charisma/10 + char.refinement*1.5 + char.constitution/5 + char.reputation/2 + char.fame/2 # Stats Upkeep

                    # return int(bu + su + char.upkeep)

                else:
                    bu = 20
                    su = 0 # Stats Upkeep
                    for stat in char.stats:
                        if stat not in ["disposition", "joy", "health", "vitality", "mood"]:
                            su += getattr(char, stat)

                    return int(bu + su + char.upkeep)

            elif char.status == 'free':
                return char.upkeep

            else: # This is for any unknown types
                bu = 50
                su = 0 # Stats Upkeep
                for stat in char.stats:
                    if stat not in ["disposition", "joy", "health", "vitality", "mood"]:
                        su += getattr(char, stat)

                return int(bu + su + char.upkeep)

        def get_whore_price(self):
            """
            Workprice for girls working as whores.
            """
            # TODO: To be revised after skills are added!
            char = self.instance

            # if char.rank < 4:
                # bp = 10 * char.rank # Base Price
            # elif char.rank < 7 :
                # bp = 15 * char.rank
            # else:
                # bp = 20 * char.rank
            # sp = char.charisma/2 + char.refinement/3 + char.reputation/4 + char.fame/4 # Stats Price
            # ssp = (char.anal + char.vaginal + char.oral + char.bdsm)/4*(1+(char.rank*0.1)) # Sex Stats Price

            return 100 # int(bp + sp + ssp)

        def next_day(self):
            self.game_fin_log[str(day)] = (self.daily_income_log, self.daily_expense_log)
            self.daily_income_log = dict(work=dict(), tips=dict(), private=dict())
            self.daily_expense_log = dict(work=dict(), private=dict(), cost=dict())


    class Stats(_object):
        """Holds and manages stats for PytCharacter Classes.
        DEVNOTE: Be VERY careful when accesing this class directly!
        Some of it's methods assume input from self.instance__setattr__ and do extra calculations!
        """
        FIXED_MAX = set(['joy', 'mood', 'disposition', 'vitality', 'luck', 'alignment'])
        def __init__(self, *args, **kwargs):
            """
            instance = reference to Character object
            Expects a dict with statname as key and a list of:
            [stat, min, max, lvl_max] as value.
            Added skills to this class... (Maybe move to a separate class if they get complex?).
            DevNote: Training skills have a capital letter in them, action skills do not. This should be done thought the class of the character and NEVER using self.mod_skill directly!
            """
            self.instance = args[0]
            self.stats, self.imod, self.min, self.max, self.lvl_max = dict(), dict(), dict(), dict(), dict()

            # Load the stat values:
            for stat, values in kwargs.get("stats", {}).iteritems():
                self.stats[stat] = values[0]
                self.imod[stat] = 0
                self.min[stat] = values[1]
                self.max[stat] = values[2]
                self.lvl_max[stat] = values[3]

            # [action_value, training_value]
            self.skills = {k: [0, 0] for k in self.instance.SKILLS}
            # [actions_multi, training_multi, value_multi]
            self.skills_multipliers = {k: [1, 1, 1] for k in self.skills}

            # Leveling system assets:
            self.goal = 1000
            self.goal_increase = 1000
            self.level = 1
            self.exp = 0

            # Statslog:
            self.log = dict()

        def _raw_skill(self, key):
            """Raw Skills:
            [action_value, training_value]
            """
            if key.islower(): return self.skills[key][0]
            else: return self.skills[key.lower()][1]

        def _get_stat(self, key):
            maxval = self.get_max(key)
            minval = self.min[key]
            val = self.stats[key] + self.imod[key]

            # Normalization:
            if val > maxval:
                if self.stats[key] > maxval:
                    self.stats[key] = maxval
                val = maxval

            elif val < minval:
                if self.stats[key] < minval:
                    self.stats[key] = minval
                val = minval

            if key not in ["disposition", "luck"] and val < 0:
                val = 0

            return val

        def get_skill(self, skill):
            """
            Returns adjusted skill.
            Action points become less useful as they exceed training points * 3.
            """
            skill = skill.lower()
            action = self._raw_skill(skill)
            training = self._raw_skill(skill.capitalize())

            training_range = training * 3
            beyond_training = action - training_range

            if beyond_training >= 0:
                training += training_range + beyond_training / 3.0
            else:
                training += action
            return training * max(min(self.skills_multipliers[skill][2], 1.5), 0.5)

        def is_skill(self, key):
            # Easy check for skills.
            return key.lower() in self.skills

        def is_stat(self, key):
            # Easy check for stats.
            return key.lower() in self.stats

        def normalize_stats(self, stats=None):
            # Makes sure main stats dict is properly aligned to max/min values

            if not stats:
                stats = self.stats

            for stat in stats:
                val = self.stats[stat]
                minval = self.min[stat]
                maxval = self.get_max(stat)
                if val > maxval:
                    self.stats[stat] = maxval
                if val < minval:
                    self.stats[stat] = minval

        def __getitem__(self, key):
            return self._get_stat(key)

        def __iter__(self):
            return iter(self.stats)

        def get_max(self, key):
            val = min(self.max[key], self.lvl_max[key])
            if key not in ["disposition"]:
                if val < 0:
                    val = 0
            return val

        def mod_item_stat(self, key, value):
            if key in self.stats:
                self.imod[key] = self.imod[key] + value

        def settle_effects(self, key, value):
            if hasattr(self.instance, "effects"):
                effects = self.instance.effects

                if key == 'disposition':
                    if effects['Insecure']['active']:
                        if value >= 5:
                            self.instance.joy += 1
                        elif value <= -5:
                            self.instance.joy -= 1
                    if effects['Introvert']['active']:
                        value = int(value*.8)
                    elif effects['Extrovert']['active']:
                        value = int(value*1.2)
                    if effects['Loyal']['active'] and value < 0: # works together with other traits
                        value = int(value*.8)

                    if last_label.startswith("interactions_"):
                        tag = str(random.random())
                        renpy.show_screen("display_disposition", tag, value, 40, 530, 400, 1)
                elif key == 'joy':
                    if effects['Impressible']['active']:
                        value = int(value*1.5)
                    elif effects['Calm']['active']:
                        value = int(value*0.5)
            return value

        def _mod_exp(self, value):
            # Assumes input from setattr of self.instance:
            if hasattr(self.instance, "effects"):
                effects = self.instance.effects
                if effects["Slow Learner"]["active"]:
                    val = value - self.exp
                    value = self.exp + int(round(val*.9))
                if effects["Fast Learner"]["active"]:
                    val = value - self.exp
                    value = self.exp + int(round(val*1.1))

            self.exp = value

            while self.exp >= self.goal:
                self.goal_increase += 1000
                self.goal += self.goal_increase
                self.level += 1

                # Bonuses from traits:
                for trait in self.instance.traits:
                    self.apply_trait_statsmod(trait)

                # Normal Max stat Bonuses:
                for stat in self.stats:
                    if stat not in self.FIXED_MAX:
                        self.lvl_max[stat] += 5
                        self.max[stat] += 2

                        # Chance to increase max stats permanently based on level
                        if self.level >= 20:
                            val = self.level / 20.0
                            if dice(val):
                                self.lvl_max[stat] +=1
                            if dice(val):
                                self.max[stat] +=1
                # Super Bonuses from Base Traits:
                if hasattr(self.instance, "traits"):
                    traits = self.instance.traits.basetraits
                    multiplier = 2 if len(traits) == 1 else 1
                    for trait in traits:
                        # Super Stat Bonuses:
                        for stat in trait.leveling_stats:
                            if stat not in self.FIXED_MAX and stat in self.stats:
                                self.lvl_max[stat] += trait.leveling_stats[stat][0] * multiplier
                                self.max[stat] += trait.leveling_stats[stat][1] * multiplier
                            else:
                                msg = "'%s' stat applied on leveling up (max mods) to %s (%s)!"
                                devlog.warning(str(msg % (stat, self.instance.__class__, trait.id)))

                        # Super Skill Bonuses:
                        for skill in trait.init_skills:
                            if self.is_skill(skill):
                                ac_val = round(trait.init_skills[skill][0] * 0.02) + self.level / 5
                                tr_val = round(trait.init_skills[skill][1] * 0.08) + self.level / 2
                                self.skills[skill][0] = self.skills[skill][0] + ac_val
                                self.skills[skill][1] = self.skills[skill][1] + tr_val
                            else:
                                msg = "'{}' skill applied on leveling up to {} ({})!"
                                devlog.warning(str(msg.format(stat, self.instance.__class__, trait.id)))

                self.stats["health"] = self.get_max("health")
                self.stats["mp"] = self.get_max("mp")
                self.stats["vitality"] = self.get_max("vitality")

        def apply_trait_statsmod(self, trait, reverse=False):
            """Applies "stats_mod" field on characters.
            """
            for key in trait.mod_stats:
                if key not in ["disposition", "upkeep"]:
                    if not self.level%trait.mod_stats[key][1]:
                        self._mod_base_stat(key, trait.mod_stats[key][0]) if not reverse else self._mod_base_stat(key, -trait.mod_stats[key][0])

        def _mod_base_stat(self, key, value):
            # Modifies the first layer of stats (self.stats)
            if key in self.stats: # As different character types may come with different stats.
                value = self.settle_effects(key, value)

                val = self.stats[key] + value

                if key == 'health' and val <= 0:
                    if isinstance(self.instance, Player):
                        jump("game_over")
                    elif isinstance(self.instance, Char):
                        char = self.instance
                        kill_char(char)
                        return

                maxval = self.get_max(key)
                minval = self.min[key]

                if val >= maxval:
                    self.stats[key] = maxval
                    return
                elif val <= minval:
                    self.stats[key] = minval
                    return

                self.stats[key] = val

        def _mod_raw_skill(self, key, value):
            """Modifies a skill.

            # DEVNOTE: THIS SHOULD NOT BE CALLED DIRECTLY! ASSUMES INPUT FROM PytCharcter.__setattr__

            Do we get the most needlessly complicated skills system award? :)
            Maybe we'll simplify this greatly in the future...
            """
            if key.islower():
                at = 0 # Action Skill...
            else:
                key = key.lower()
                at = 1 # Training (knowledge part) skill...

            current_full_value = self.get_skill(key)
            skill_max = SKILLS_MAX[key]
            if current_full_value >= skill_max: # Maxed out...
                return

            value -= self.skills[key][at]
            value *= max(0.5, min(self.skills_multipliers[key][at], 1.5))

            threshold = SKILLS_THRESHOLD[key]
            beyond_training = current_full_value - threshold

            if beyond_training > 0: # insufficient training... lessened increase beyond
                at_zero = skill_max - threshold
                value *= max(0.1, 1 - float(beyond_training)/at_zero)

            self.skills[key][at] += value

        def eval_inventory(self, inventory, weighted, target_stats, target_skills, exclude_on_skills, exclude_on_stats,
                           equip_chance=None, min_value=-5, upto_skill_limit=False):
            """
            weigh items in inventory based on stats. weights per item will be added to weighted.

            inventory: the inventory to evaluate items from
            target_stats: a list of stats to consider for items
            target_skills: similarly, a list of skills
            exclude_on_stats: items will be excluded if stats in this list are negatively affected
            exclude_on_skills: similarly, a list of skills
            equip_chance(): function that takes the item and returns a chance, between 0 and 100
            min_value: at what (negative) value the weight will become zero
            upto_skill_limit: whether or not to calculate bonus beyond training exactly
            """

            # call the functions for these only once
            stats = {'current_stat': {}, 'current_max': {}, 'skill': {}}
            for stat in target_stats:
                stats['current_stat'][stat] = self._get_stat(stat) # current stat value
                stats['current_max'][stat] = self.get_max(stat)   # current stat max

            for skill in self.skills:
                stats['skill'][skill] = self.get_skill(skill)

            # per item the nr of weighting criteria may vary. At the end all of them are averaged.
            # if an item has less than the most weights the remaining are imputed with 50 weights
            most_weights = {slot: 0 for slot in weighted}

            for item in inventory:

                if item.slot not in weighted:
                    continue

                # weights is a list of 0 to 100 values that will be averaged for the final weight, unless we break
                weights = equip_chance(item) if equip_chance else [item.eqchance]

                if weights is not None:
                    for stat, value in item.mod.iteritems():

                        if value < min_value and stat in exclude_on_stats:
                            break # break (in any case below) will cause 0 weights to be added for this item

                        if stat in stats['current_stat']:

                            # a new max may have to be considered
                            new_max = min(self.max[stat] + item.max[stat], self.lvl_max[stat]) if stat in item.max else stats['current_max'][stat]

                            if not new_max:
                                break

                            # what the new value would be:
                            new_stat = max(min(self.stats[stat] + self.imod[stat] + value, new_max), self.min[stat])

                            # add the fraction  increace / decrease
                            weights.append(50 + 100*(new_stat - stats['current_stat'][stat])/new_max)
                    else:
                        for stat, value in item.max.iteritems():

                            if not stat in exclude_on_stats:
                                continue

                            if stat in stats['current_max']:

                                new_max = min(self.max[stat] + value, self.lvl_max[stat])

                                new_stat = self.stats[stat] + self.imod[stat] + (item.mod[stat] if stat in item.mod else 0)

                                # if the stat does change, give weight for this
                                stat_change = new_stat - stats['current_stat'][stat]
                                if stat_change:
                                    if stat_change < min_value:
                                        break
                                    weights.append(50 + 100*stat_change/stats['current_max'][stat])
                                else:
                                    stat_remaining = new_max - stats['current_stat'][stat]
                                    # if training doesn't shift max, at least give a weight up to 1 for the increased max.
                                    # if max decreases, give a penalty, more severe if there is little stat remaining.
                                    weights.append(max(50 + value / (stat_remaining + max(value, 1)), 0)) # stat_remaining is >= 0
                        else:
                            for skill, effect in item.mod_skills.iteritems():

                                if all(i <= 0 for i in effect) and skill in exclude_on_skills:
                                    break

                                if skill in target_skills:

                                    skill_remaining = SKILLS_MAX[skill] - stats['skill'][skill]
                                    if skill_remaining > 0:
                                        # calculate skill with mods applied, as in apply_item_effects() and get_skill()

                                        mod_action = self.skills[skill][0] + effect[3]
                                        mod_training = self.skills[skill][1] + effect[4]
                                        mod_skill_multiplier = self.skills_multipliers[skill][2] + effect[2]

                                        if upto_skill_limit: # more precise calculation of skill limits
                                            training_range = mod_training * 3
                                            beyond_training = mod_action - training_range

                                            if beyond_training >= 0:
                                                mod_training += training_range - mod_action + beyond_training/3.0

                                        mod_training += mod_action
                                        new_skill = mod_training*max(min(mod_skill_multiplier, 1.5), 0.5)
                                        if new_skill < min_value:
                                            break

                                        saturated_skill = max(stats['skill'][skill] + 100, new_skill)

                                        weights.append(50 + 100*(new_skill - stats['skill'][skill]) / saturated_skill)
                            else:
                                l = len(weights)

                                if l > most_weights[item.slot]:
                                    most_weights[item.slot] = l

                                weighted[item.slot].append([weights, item])
            return most_weights


    ###### Character Classes ######
    class PytCharacter(Flags):
        STATS = set()
        SKILLS = set(["vaginal", "anal", "oral", "sex", "strip", "service", "refinement", "group", "bdsm", "dancing",
                               "bartending", "cleaning", "waiting", "management", "exploration", "teaching", "swimming", "fishing"])
        FULLSKILLS = set(skill + "skill" for skill in SKILLS) # Used to access true, final, adjusted skill values through direct access to class, like: char.swimmingskill
        PERSONALITY_TRAITS = set(["Tsundere", "Yandere", "Kuudere", "Dandere", "Ane", "Imouto", "Kamidere", "Bokukko", "Impersonal", "Deredere"]) # Do we still need this? Traits themselves are now flagged!
        CLASSES = set(["Stripper", "Prostitute", "Dominatrix", "Warrior", "ServiceGirl"]) # This is prolly now also too old...
        STATUS = set(["slave", "free"])
        ATTACKS = dict(Rod = "Rod Attack", Sword = "Sword Slash",
                                   Ranged = "Bow Shot", Dagger = "Knife Attack",
                                   Whip = "Whip Strike", Fists = "Fist Attack") # Also should be worked out of the class...
        """
        Decided to create a base class for characters (finally)...
        """
        def __init__(self, arena=False, inventory=False, effects=False):
            super(PytCharacter, self).__init__()
            self.img = ""
            self.portrait = ""
            self.gold = 0
            self.name = ""
            self.fullname = ""
            self.nickname = ""
            self._mc_ref = None # This is how characters refer to MC (hero). May depend on case per case basis and is accessed through obj.mc_ref property.
            self.height = "average"
            self.full_race = ""
            self.gender = "female"

            self.AP = 3
            self.baseAP = 3
            self.reservedAP = 0

            # Locations and actions, most are properties with setters and getters.
            self._location = None # Present Location.
            self._workplace = None  # Place of work.
            self._home = None # Living location.
            self._action = None

            # Traits:
            self.upkeep = 0 # Required for some traits...

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
                # List to keep track of temporary effect
                # consumables that failed to activate on cmax **We are not using this or at least I can't find this in code!
                # self.maxouts = list()

            # Stat support Dicts:
            stats = {
                'charisma': [0, 0, 100, 60],          # means [stat, min, max, lvl_max]
                'constitution': [0, 0, 60, 40],
                'joy': [0, 0, 100, 200],
                'character': [0, 0, 100, 60],
                'reputation': [0, 0, 100, 100],
                'health': [200, 0, 200, 400],
                'fame': [0, 0, 100, 60],
                'mood': [0, 0, 1000, 1000],
                'disposition': [0, -1000, 1000, 1000],
                'vitality': [200, 0, 200, 400],
                'intelligence': [0, 0, 100, 60],

                'luck': [0, -50, 50, 50],

                'attack': [0, 0, 60, 40],
                'magic': [0, 0, 40, 30],
                'defence': [0, 0, 50, 40],
                'agility': [0, 0, 35, 25],
                'mp': [0, 0, 40, 30]
            }
            self.stats = Stats(self, stats=stats)
            self.STATS = set(self.stats.stats.keys())

            if effects:
                # Effects assets:
                self.effects = {
                'Poisoned': {"active": False, "penalty": False, "duration": False, 'desc': "Poison decreases health every day. Make sure you cure it as fast as possible."},
                'Slow Learner': {'active': False, 'desc': "-10% experience"},
                'Fast Learner': {'active': False, 'desc': "+10% experience"},
                "Introvert": {'active': False, 'desc': "Harder to increase and decrease disposition."},
                "Extrovert": {'active': False, 'desc': "Easier to increase and decrease disposition."},
                "Insecure": {'active': False, 'desc': "Significant changes in disposition also change joy."},
                "Sibling": {'active': False, 'desc': "If disposition is low enough, it gradually increases over time."},
                "Assertive": {'active': False, 'desc': "If character is low enough, it increases over time."},
                "Diffident": {'active': False, 'desc': "If character is high enough, it slowly decreases over time."},
                'Food Poisoning': {'active': False, 'activation_count': 0, "desc": "Intemperance in eating or low quality food often lead to problems."},
                'Down with Cold': {'active': False, "desc": "Causes weakness and aches, will be held in a week or two."},
                "Unstable": {"active": False, "desc": "From time to time mood chaotically changes."},
                "Optimist": {"active": False, "desc": "Joy increases over time, unless it's too low. Grants immunity to Elation."},
                "Pessimist": {"active": False, "desc": "Joy decreases over time, unless it's already low enough. Grants immunity to Depression."},
                "Composure": {"active": False, "desc": "Over time joy decreases if it's too high and increases if it's too low."},
                "Kleptomaniac": {"active": False, "desc": "With some luck, gold increases every day."},
                "Drowsy": {"active": False, "desc": "Rest restores more vitality than usual."},
                "Loyal": {"active": False, "desc": "Harder to decrease disposition."},
                "Lactation": {"active": False, "desc": "Her breasts produce milk. If she's your slave or lover, you will get a free sample every day."},
                "Vigorous": {"active": False, "desc": "If vitality is too low, it slowly increases over time."},
                "Silly": {"active": False, "desc": "If intelligence is high enough, it rapidly decreases over time."},
                "Intelligent": {"active": False, "desc": "If she feels fine, her intelligence increases over time."},
                "Fast Metabolism": {"active": False, "desc": "Any food is more effective than usual."},
                "Drunk": {"active": False, 'activation_count': 0, "desc": "It might feel good right now, but tomorrow's hangover is fast approaching (-1AP for every next drink)."},
                "Depression": {"active": False, "desc": "She's in a very low mood right now (-1AP)."},
                "Elation": {"active": False, "desc": "She's in a very high mood right now (+1AP)."},
                "Drinker": {"active": False, "desc": "Neutralizes the AP penalty of Drunk effect. But hangover is still the same."},
                "Injured": {"active": False, "desc": "Some wounds cannot be healed easily. In such cases special medicines are needed."},
                "Exhausted": {"active": False, "desc": "Sometimes anyone needs a good long rest.", 'activation_count': 0},
                "Impressible": {"active": False, "desc": "Easier to decrease and increase joy."},
                "Calm": {"active": False, "desc": "Harder to decrease and increase joy."},
                "Regeneration": {"active": False, "desc": "Restores some health every day."},
                "MP Regeneration": {"active": False, "desc": "Restores some mp every day."},
                "Small Regeneration": {"active": False, "desc": "Restores 10 health every day for 20 days."},
                "Blood Connection": {"active": False, "desc": "Disposition increases and character decreases every day."},
                "Horny": {"active": False, "desc": "She's in the mood for sex."}
                }

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
            self.besprite_size = None # Sprite size in pixels.
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

            # Say style properties:
            self.say_style = {"color": ivory}

            # We add Neutral element here to all classes to be replaced later:
            self.apply_trait(traits["Neutral"])

            self.say = None # Speaker...

        def __getattr__(self, key):
            stats = self.__dict__.get("stats", {})
            if key in self.STATS:
                return stats._get_stat(key)
            elif key.lower() in self.SKILLS:
                return stats._raw_skill(key)
            elif key in self.FULLSKILLS:
                return self.stats.get_skill(key)
            raise AttributeError("%r object has no attribute %r" %
                                          (self.__class__, key))

        def __setattr__(self, key, value):
            if key in self.STATS:
                # Primary stat dict modifier...
                value = value - self.stats._get_stat(key)
                self.stats._mod_base_stat(key, int(round(value)))
            elif key.lower() in self.SKILLS:
                self.__dict__["stats"]._mod_raw_skill(key, value)
            # elif key == 'exp': # We handle this through properties...
                # self.__dict__["stats"]._mod_exp(value)
            else:
                super(PytCharacter, self).__setattr__(key, value)

        # Money:
        def take_money(self, amount, reason="Other"):
            if amount <= self.gold:
                self.gold -= amount
                return True
            else:
                return False

        def add_money(self, amount, reason="Other"):
            self.gold += amount

        # Game assist methods:
        def set_status(self, s):
            if s not in ["slave", "free"]:
                raise Exception("{} status is not valid for {} with an id: {}".format(s, self.__class__, self.id))
            self.status = s

        # Properties:
        @property
        def mc_ref(self):
            if self._mc_ref is None:
                if self.status == "slave":
                    return "Master"
                else:
                    return hero.name
            else:
                return self._mc_ref

        @property
        def p(self):
            # Subject pronoun (he/she/it): (prolly most used so we don't call it 'sp'):
            if self.gender == "female":
                return "she"
            elif self.gender == "male":
                return "he"
            else:
                return "it"

        @property
        def pC(self):
            # Subject pronoun (he/she/it) capitalized:
            return self.p.capitalize()

        @property
        def op(self):
            # Object pronoun (him, her, it):
            if self.gender == "female":
                return "her"
            elif self.gender == "male":
                return "him"
            else:
                return "it"

        @property
        def opC(self):
            # Object pronoun (him, her, it) capitalized:
            return self.op.capitalize()

        @property
        def pp(self):
            # Possessive pronoun (his, hers, its):
            # This may 'gramatically' incorrect, cause things (it) cannot possess/own anything but knowing PyTFall :D
            if self.gender == "female":
                return "hers"
            elif self.gender == "male":
                return "his"
            else:
                return "its"

        @property
        def ppC(self):
            # Possessive pronoun (his, hers, its) capitalized::
            return self.pp.capitalize()

        @property
        def hs(self):
            if self.gender == "female":
                return "sister"
            else:
                return "brother"

        @property
        def hss(self):
            if self.gender == "female":
                return "sis"
            else:
                return "bro"

        @property
        def is_available(self):
            # Is this enought or should there be separate tracker properties for gameworld and player actions? This will prolly do for now.
            if not self.alive:
                return False
            if self.action == "Exploring":
                return False
            return self._available

        @property
        def occupations(self):
            """
            Formely "occupation", will return a set of jobs that a girl may be willing to do based of her basetraits.
            Not decided if this should be strings, Trait objects of a combination of both.
            """
            allowed = set()

            for t in self.traits:
                if t.basetrait:
                    allowed.add(t)
                    allowed = allowed.union(t.occupations)

            return allowed

        @property
        def action(self):
            return self._action
        @action.setter
        def action(self, value):
            self._action = value

        @property
        def arena_rep(self):
            return self._arena_rep
        @arena_rep.setter
        def arena_rep(self, value):
            if value <= -500:
                self._arena_rep = - 500
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
        def workplace(self):
            return self._workplace
        @workplace.setter
        def workplace(self, value):
            self._workplace = value

        @property
        def home(self):
            return self._home
        @home.setter
        def home(self, value):
            self._home = value

        # Alternative Method for modding first layer of stats:
        def add_exp(self, value, adjust=True):
            # Adds experience, adjusts it by default...
            if adjust:
                value = adjust_exp(self, value)
            self.exp += value

        def mod_stat(self, stat, value):
            self.stats._mod_base_stat(stat, value)

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
        def exp(self): # This is already handled in __setattr__ ????
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
        # Show to mimic girls method behaviour:
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
                    devlog.warning("Unknown height setting for %s" % self.id)
                    resize = (200, 180)
            elif tag == "vnsprite":
                if self.height == "average":
                    resize = (1000, 520)
                elif self.height == "tall":
                    resize = (1000, 600)
                elif self.height == "short":
                    resize = (1000, 400)
                else:
                    devlog.warning("Unknown height setting for %s" % self.id)
                    resize = (1000, 500)
            else:
                raise Exception("get_sprite_size got unknown type for resizing!")
            return resize

        def has_image(self, *tags):
            """
            Returns True if image is found.
            """
            return True

        def show(self, what, resize=(None, None), cache=True):
            if what != self.img:
                what = self.img

            return ProportionalScale(what, resize[0], resize[1])

        # AP + Training ------------------------------------------------------------->
        def restore_ap(self):
            self.AP = self.get_free_ap()

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

            if isinstance(self.location, Apartment):
                ap = ap + 1

            if isinstance(self.location, TrainingDungeon):
                ap = ap + (self.location.mod_housing() * 3)

            return self.baseAP + ap

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
            *kind = is a string refering to the NPC
            """
            # Any training:
            char.exp += self.adjust_exp(randint(20, max(25, self.luck)))

            if kind == "train_with_witch":
                self.magic += randint(1, 2)
                self.intelligence += randint(1, 2)
                self.mp += randint(7, 15)

                if dice(50):
                    self.agility += 1

            if kind == "train_with_aine":
                self.charisma += randint(1, 2)
                self.vitality += randint(40, 100)
                if dice(max(10, self.luck)):
                    self.reputation += 1
                    self.fame += 1
                if dice(0.5 + self.luck*0.05):
                    self.luck += randint(1, 2)

            if kind == "train_with_xeona":
                self.attack += 1
                self.defence += 1
                if dice(50):
                    self.agility += 1
                    self.health += randint(10, 20)
                if dice(25 + max(5, int(self.luck/3))):
                    self.constitution += randint(1, 2)

        def get_training_price(self):
            return 1000 + 1000 * (self.level/5)

        # Logging and updating daily stats change on next day:
        def log_stats(self):
            self.stats.log = copy.copy(self.stats.stats)
            self.stats.log["exp"] = self.exp
            self.stats.log["level"] = self.level

        # -------------------------------------------------------------------------------->
        # Equipment Methods (They often assume a character has an inventory)
        def eq_items(self):
            """Returns a list of all equiped items."""
            if hasattr(self, "eqslots"):
                return self.eqslots.values()
            else:
                return []

        def add_item(self, item, amount=1):
            self.inventory.append(item, amount=amount)

        def remove_item(self, item, amount=1):
            self.inventory.remove(item, amount=amount)

        def auto_buy(self, item=None, amount=1, equip=False):

            # handle request to auto-buy a particular item!
            # including forbidden for slaves items - it might be useful
            if item:
                if isinstance(item, basestring):
                    item = store.items[item]

                if item in all_auto_buy_items:
                    amount = min(amount, int(self.gold / item.price))

                    if amount != 0:
                        self.take_money(item.price * amount)
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
                    # why the #*!:-@ is extend() in place and union not??
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

            if amount > 2: #food doesn't count, it's not a big meal

                # define weighted choice for remaining articles - based on status and class
                choices = [("rest", 100)]
                dress_weight = 100

                # for slaves exclude all weapons, spells and armor
                if self.status != "slave":
                    if "Warrior" in self.occupations:
                        choices.append(("warrior", 100))

                        # if we still didn't pick the items, if the character has Warrior occupation, she may ignore dresses
                        dress_weight = 60 if self.occupations.issuperset(("SIW", "Server", "Specialist")) else 25

                    if "Caster" in self.occupations and auto_buy_items["scroll"]: # FIXME: remove 2nd part when we have scrolls.
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

        def equip(self, item, remove=True): # Equips the item
            """
            Equips an item to a corresponding slot or consumes it.
            remove: Removes from the inventory (Should be False if item is equipped from directly from a foreign inventory)
            **Note that the remove is only applicable when dealing with consumables, game will not expect any other kind of an item.
            """
            if isinstance(item, list):
                for it in item:
                    self.equip(it, remove)
                return

            if item.slot not in self.eqslots:
                devlog.warning(str("Unknown Items slot: %s, %s" % (item.slot, self.__class__.__name__)))
                return

            # This is a temporary check, to make sure nothing goes wrong:
            # Code checks during the equip method should make sure that the unique items never make it this far:
            if item.unique and item.unique != item.id:
                raise Exception("A character attempted to equip unique item that was not meant for him/her. This is a flaw in game design, please report to out development team! Character: %s/%s, Item:%s" % self.id, self.__class__, item.id)

            if item.sex not in ["unisex", self.gender]:
                devlog.warning(str("False character sex value: %s, %s,  %s" % (item.sex, item.id, self.__class__.__name__)))
                return

            if item.slot == 'consumable':
                if item.id in self.consblock:
                    return

                if item.cblock:
                    self.consblock[item.id] = item.cblock
                if item.ctemp:
                    self.constemp[item.id] = item.ctemp
                self.apply_item_effects(item)

                # To prevent game trying to remove item on area effect.
                if item.ceffect:
                    pass
                elif remove:
                    self.inventory.remove(item)

            elif item.slot == 'misc':
                if item.id in self.miscblock:
                    return

                if self.eqslots['misc']: # Unequip if equipped.
                    self.inventory.append(self.eqslots['misc'])
                    del(self.miscitems[self.eqslots['misc'].id])
                self.eqslots['misc'] = item
                self.miscitems[item.id] = item.mtemp
                self.inventory.remove(item)

            # elif item.slot == 'belt':
                # if not self.eqslots['belt']:
                    # self.eqslots['belt'] = item
                    # self.inventory.remove(item)
                # elif not self.eqslots['belt1']:
                    # self.eqslots['belt1'] = item
                    # self.inventory.remove(item)
                # elif not self.eqslots['belt2']:
                    # self.eqslots['belt2'] = item
                    # self.inventory.remove(item)
                # else:
                    # self.inventory.append(self.eqslots['belt'])
                    # self.eqslots['belt2'] = self.eqslots['belt1']
                    # self.eqslots['belt1'] = self.eqslots['belt0']
                    # self.eqslots['belt'] = item
                    # self.inventory.remove(item)

            elif item.slot == 'ring':
                if not self.eqslots['ring']:
                    self.eqslots['ring'] = item
                elif not self.eqslots['ring1']:
                    self.eqslots['ring1'] = item
                elif not self.eqslots['ring2']:
                    self.eqslots['ring2'] = item
                else:
                    self.remove_item_effects(self.eqslots['ring'])
                    self.inventory.append(self.eqslots['ring'])
                    self.eqslots['ring'] = self.eqslots['ring1']
                    self.eqslots['ring1'] = self.eqslots['ring2']
                    self.eqslots['ring2'] = item
                self.apply_item_effects(item)
                self.inventory.remove(item)

            else:
                # Any other slot:
                if self.eqslots[item.slot]: # If there is any item equipped:
                    self.remove_item_effects(self.eqslots[item.slot]) # Remove equipped item effects
                    self.inventory.append(self.eqslots[item.slot]) # Add unequipped item back to inventory
                self.eqslots[item.slot] = item # Assign new item to the slot
                self.apply_item_effects(item) # Apply item effects
                self.inventory.remove(item) # Remove item from the inventory

        def unequip(self, item, slot=None):

            if item.slot == 'misc':
                self.eqslots['misc'] = None
                del(self.miscitems[item.id])
                self.inventory.append(item)
            # This prolly has to be rewritten!
            # elif item.slot == 'belt':
                # for entry in [self.eqslots['belt'], self.eqslots['belt1'], self.eqslots['belt2']]:
                    # if entry == item:
                        # self.inventory.append(item)
                        # entry = None
                        # return
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
                self.remove_item_effects(item)

            else:
                # Other slots:
                self.inventory.append(item)
                self.remove_item_effects(item)
                self.eqslots[item.slot] = None

        def equip_chance(self, item):
            """
            return a list of chances, between 0 and 100 if the person has a preference to equip this item.
            If None is returned the item should not be used. This only includes personal preferences,
            Other factors, like stat bonuses may also have to be taken into account.
            """

            # if return is 0 the item should be skipped

            if not item.eqchance or not can_equip(item, self):
                return None

            chance = []
            when_drunk = 30
            appetite = 50

            for trait in self.traits:

                if trait in trait_selections["badtraits"] and item in trait_selections["badtraits"][trait]:
                    return None

                if trait in trait_selections["goodtraits"] and item in trait_selections["goodtraits"][trait]:
                    chance.append(100)

                if trait == "Kamidere": # Vanity: wants pricy uncommon items
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

            if item.type == "permanent": # only allowed if also in goodtraits. but then we already returned 100
                return None

            if item.slot == "consumable":

                if item.ceffect or item.id in self.consblock or item.id in self.constemp:
                    return None

                if item.type == "alcohol":

                    if self.effects['Drunk']['activation_count'] >= when_drunk:
                        return None

                    if self.effects['Depression']['active']:
                        chance.append(30 + when_drunk)

                elif item.type == "food":

                    food_poisoning = self.effects['Food Poisoning']['activation_count']

                    if not food_poisoning:
                        chance.append(appetite)

                    else:
                        if food_poisoning >= 6:
                            return None

                        chance.append((6-food_poisoning) * 9)

            elif item.slot == "misc":
                # If the item self-destructs or will be blocked after one use,
                # it's now up to the caller to stop after the first item of this kind that is picked.

                # no blocked misc items:
                if item.id in self.miscblock:
                    return None

            chance.append(item.eqchance)
            return chance

        def equip_for(self, purpose):
            """
            This method will auto-equip slot items on per purpose basis!
            """
            returns = list()
            if self.eqslots["weapon"]:
                self.unequip(self.eqslots["weapon"])

            slots = [slot for slot in self.eqslots if slot not in ("ring1", "ring2", "consumable")]

            if purpose == "Combat":
                returns.extend(self.auto_equip(['health', 'mp', 'attack', 'magic', 'defence', 'agility', "luck"], slots=slots, real_weapons=True))

            elif purpose == "Battle Mage":
                returns.extend(self.auto_equip(['health', 'mp', 'attack', 'magic'], exclude_on_stats=["agility", "luck", 'defence', 'intelligence'], slots=slots, real_weapons=True))

            elif purpose == "Barbarian":
                returns.extend(self.auto_equip(['health', 'attack', 'constitution', 'agility'], exclude_on_stats=["luck"], slots=slots, real_weapons=True))

            elif purpose == "Wizard":
                returns.extend(self.auto_equip(['mp', 'magic', "luck", 'intelligence'], exclude_on_stats=["health", 'defence'], slots=slots, real_weapons=True))

            elif purpose == "Striptease":
                returns.extend(self.auto_equip(["charisma"], ["strip"], exclude_on_stats=["health", "vitality", "mp", "joy"], slots=slots))

            elif purpose == "Sex":
                returns.extend(self.auto_equip(["charisma"], ["vaginal", "anal", "oral"], exclude_on_stats=["health", "vitality", "mp"], slots=slots))

            elif purpose == "Service":
                returns.extend(self.auto_equip(["charisma"], ["service"], exclude_on_stats=["health", "vitality", "mp", "joy"], slots=slots))

            else:
                devlog.warning("Supplied unknown purpose: %s to equip_for method for: %s, (Class: %s)" % (purpose, self.name, self.__class__.__name__))
            return returns

        def auto_equip(self, target_stats, target_skills=None, exclude_on_skills=None, exclude_on_stats=None, slots=None,
                       inv=None, real_weapons=False):
            """
            targetstats: expects a list of stats to pick the item
            targetskills: expects a list of skills to pick the item
            exclude_on_stats: items will not be used if stats in this list are being diminished by use of the item *Decreased the chance of picking this item
            exclude_on_skills: items will not be used if stats in this list are being diminished by use of the item *Decreased the chance of picking this item
            ==>   do not put stats/skills both in target* and in exclude_on_* !
            *default: All Stats - targetstats
            slots: a list of slots, contains just consumables by default
            inv: nventory to draw from.
            real_weapons: Do we equip real weapon types (*Broom is now considered a weapon as well)
            """

            # Prepair data:
            if not slots:
                slots = ["consumable"]

            weighted = {}
            for k in slots:
                if self.eqslots[k]:
                    item = self.eqslots[k]
                    #if not equipment_access(self, item=item, silent=True, allowed_to_equip=False):
                    #    continue
                    self.unequip(item)

                weighted[k] = []

            if not inv:
                inv = self.inventory
            if not target_skills:
                target_skills = set()

            exclude_on_stats = set(exclude_on_stats) if exclude_on_stats else set()
            exclude_on_skills = set(exclude_on_skills) if exclude_on_skills else set()

            # allow a little stat/skill penalty, just make sure the net weight is positive.
            min_value = -5
            upto_skill_limit = False

            # how much stats weigh vs skills. To compare weight will be normalised to their max values.
            # skills have a overly high max (5000), so the ratio is tipped towards stats.
            #stat_vs_skill = 0.5

            #if traits["Athletic"]:
            #    stat_vs_skill /= 2 # preference for skills over stats

            #if traits["Nerd"]:
            #    stat_vs_skill *= 2 # preference for stats over skills


            #selectivity = 1 if traits["Messy"] or traits["Clumsy"] else 1.5

            #if traits["Smart"] or traits["Psychic"]:
            #    selectivity *= 2

            #last = max(int(len(picks) / selectivity), 1)

            # traits that may influence the item selection process
            for t in self.traits:

                # bad eyesightedness may cause inclusion of items with more penalty
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

            exclude_on_stats = exclude_on_stats.union(target_stats)
            exclude_on_skills = exclude_on_skills.union(target_skills)

            most_weights = self.stats.eval_inventory(inv, weighted, target_stats, target_skills,
                                                     exclude_on_skills, exclude_on_stats,
                                                     equip_chance=self.equip_chance, min_value=min_value,
                                                     upto_skill_limit=upto_skill_limit)

            returns = list() # We return this list with all items used during the method.
            for slot, picks in weighted.iteritems():

                if not picks:
                    continue

                # if we need only one pick, store max and item in selected, otherwise prefilter items
                selected = [0, None] if slot != "consumable" and slot != "ring" else []

                # create averages for items
                for r in picks:
                    # devlog.warn("[%s/%s]: %s" % (r[1].slot, r[1].id, str(r[0])))

                    som = sum(r[0])

                    # impute with weights of 50 for items that have less weights
                    som += 50 * (len(r[0]) - most_weights[slot])

                    r[0] = som/most_weights[slot]
                    if r[0] > 0:
                        if slot != "consumable" and slot != "ring":
                            if slot == "weapon" and not real_weapons and not r[1].type.lower().startswith("nw"):
                                continue

                            if r[0] > selected[0]:
                                selected = r # store weight and item for the highest weight
                        else:
                            selected.append(r)

                if slot != "consumable" and slot != "ring":

                    item = selected[1]

                    if item:
                        inv.remove(item)
                        self.equip(item, remove=False)
                        returns.append(item.id)
                    continue

                # multiple consumables/rings can be taken.
                # consumables not filtered will also be iterated over multiple times

                for weight, item in sorted(selected, key=lambda x: x[0], reverse=True):

                    while self.equip_chance(item) != None:

                        inv.remove(item)
                        self.equip(item, remove=False)
                        returns.append(item.id)

                        if not item.id in inv.items:
                            break

                        for stat in item.mod:
                            if not stat in target_stats:
                                continue

                            if item.slot == "ring" or self.stats._get_stat(stat) < self.get_max(stat)*0.40:
                                break # may select it a 2nd time

                            # If stat is above 40% of max, behave more selective, to prevent wasting items.

                            remains = self.get_max(stat) - self.stats._get_stat(stat)

                            # if effect is larger than remaining required and item is expensive, we don't select it.
                            if remains > 0 or (item.price <= 100 or remains > item.get_stat_eq_bonus(self.stats, stat)):
                                break
                        else:
                            # item gives no stat benefit anymore. Also apply it once for each skill benefit
                            for skill in item.mod_skills:
                                if skill in target_skills:
                                    inv.remove(item)
                                    self.equip(item, remove=False)
                                    returns.append(item.id)
                            break # outer for loop

                        if not item.id in inv.items:
                            break

                    if slot == "ring":
                        slot = "ring1"
                        continue
                    if slot == "ring1":
                        slot = "ring2"
                        continue
            return returns

        def load_equip(self, eqsave):
            # load equipment from save, if possible

            for slot, desired_item in eqsave.iteritems():

                currently_equipped = self.eqslots[slot]
                if currently_equipped == desired_item:
                    continue

                # rings can be on other fingers. swapping them is allowed in any case
                if slot == "ring":

                    # if the wanted ring is on the next finger, or the next finger requires current ring, swap
                    if self.eqslots["ring1"] == desired_item or eqsave["ring1"] == currently_equipped:
                        (self.eqslots["ring1"], self.eqslots[slot]) = (self.eqslots[slot], self.eqslots["ring1"])

                        currently_equipped = self.eqslots[slot]
                        if currently_equipped == desired_item:
                            continue


                if slot == "ring" or slot == "ring1":

                    if self.eqslots["ring2"] == desired_item or eqsave["ring2"] == currently_equipped:
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
        def apply_item_effects(self, item):
            # Attacks/Magic
            if hasattr(item, "attacks"):
                if item.attacks:
                    default = self.default_attack_skill
                    if default in self.attack_skills:
                        self.attack_skills.remove(default)
                for attack in item.attacks:
                    if attack in store.battle_skills:
                        attack = store.battle_skills[attack]
                        self.attack_skills.append(attack, False)
                    else:
                        devlog.warning("Unknown battle skill %s applied by character: %s (%s)!" % (attack, self.fullname, self.__class__))

            for spell in item.add_be_spells:
                if spell in store.battle_skills:
                    spell = store.battle_skills[spell]
                    self.magic_skills.append(spell, False)
                else:
                    devlog.warning("Unknown battle skill %s applied by character: %s (%s)!" % (spell, self.fullname, self.__class__))

            for spell in item.remove_be_spells:
                if spell in store.battle_skills:
                    spell = store.battle_skills[spell]
                    self.magic_skills.remove(spell, False)
                else:
                    devlog.warning("Unknown battle skill %s removed by character: %s (%s)!" % (spell, self.fullname, self.__class__))

            # Taking care of stats: -------------------------------------------------->
            for key in item.max:
                if "Left-Handed" in self.traits and item.slot == "smallweapon":
                    self.stats.max[key] += item.max[key]*2
                elif "Left-Handed" in self.traits and item.slot == "weapon":
                    self.stats.max[key] += int(item.max[key]*0.5)
                elif "Knightly Stance" in self.traits and key == "defence" and item.type == "armor":
                    self.stats.max[key] += int(item.max[key]*1.3)
                elif "Berserk" in self.traits and key == "defence":
                    self.stats.max[key] += int(item.max[key]*.5)
                elif "Berserk" in self.traits and key == "attack":
                    self.stats.max[key] += int(item.max[key]*2)
                elif "Hollow Bones" in self.traits and key == "agility" and item.max[key] <0:
                    pass
                elif "Elven Ranger" in self.traits and key == "defence" and item.max[key] <0 and item.type in ["bow", "crossbow", "throwing"]:
                    pass
                elif "Sword Master" in self.traits and item.type == "sword":
                    self.stats.max[key] += int(item.max[key]*1.3)
                elif "Shield Master" in self.traits and item.type == "shield":
                    self.stats.max[key] += int(item.max[key]*1.3)
                elif "Dagger Master" in self.traits and item.type == "dagger":
                    self.stats.max[key] += int(item.max[key]*1.3)
                elif "Bow Master" in self.traits and item.type == "bow":
                    self.stats.max[key] += int(item.max[key]*1.3)
                else:
                    self.stats.max[key] += item.max[key]
            if "Royal Assassin" in self.traits and item.slot in ["smallweapon", "weapon", "body", "cape", "feet", "wrist", "head"]:
                self.stats.max["attack"] += int(item.price*0.01)
                self.mod_stat("attack", int(item.price*0.01))
            elif "Armor Expert" in self.traits and item.slot in ["smallweapon", "weapon", "body", "cape", "feet", "wrist", "head"]:
                self.stats.max["defence"] += int(item.price*0.01)
                self.mod_stat("defence", int(item.price*0.01))
            for key in item.min:
                self.stats.min[key] += item.min[key]
                if "Left-Handed" in self.traits and item.slot == "smallweapon":
                    self.stats.min[key] += item.min[key]*2
                elif "Left-Handed" in self.traits and item.slot == "weapon":
                    self.stats.min[key] += int(item.min[key]*0.5)
                elif "Knightly Stance" in self.traits and key == "defence":
                    self.stats.min[key] += int(item.min[key]*1.3)
                elif "Berserk" in self.traits and key == "defence":
                    self.stats.min[key] += int(item.min[key]*.5)
                elif "Berserk" in self.traits and key == "attack":
                    self.stats.min[key] += int(item.min[key]*2)
                elif "Hollow Bones" in self.traits and key == "agility" and item.min[key] <0:
                    pass
                elif "Elven Ranger" in self.traits and key == "defence" and item.min[key] <0 and item.type in ["bow", "crossbow", "throwing"]:
                    pass
                elif "Sword Master" in self.traits and item.type == "sword":
                    self.stats.min[key] += int(item.min[key]*1.3)
                elif "Dagger Master" in self.traits and item.type == "dagger":
                    self.stats.min[key] += int(item.min[key]*1.3)
                elif "Shield Master" in self.traits and item.type == "shield":
                    self.stats.min[key] += int(item.min[key]*1.3)
                elif "Bow Master" in self.traits and item.type == "bow":
                    self.stats.min[key] += int(item.min[key]*1.3)
                else:
                    self.stats.min[key] += item.min[key]
            for key in item.mod:
                if key == "health" and self.health + item.mod[key] <= 0:
                    self.health = 1 # prevents death by accident...
                    continue

                if not item.statmax or getattr(self, key) >= item.statmax:
                    if key == 'gold':
                        self.gold += item.mod[key]
                    elif key == "exp":
                        self.exp += item.mod[key]
                    elif key in ['health', 'mp', 'vitality', 'joy'] or (item.slot in ['consumable', 'misc'] and not (item.slot == 'consumable' and item.ctemp)):
                        if self.effects['Fast Metabolism']['active'] and item.type == "food":
                            self.mod_stat(key, (2*item.mod[key]))
                        elif "Summer Eternality" in self.traits and key == "health" and item.mod[key]>0:
                            self.mod_stat(key, (int(0.35*item.mod[key])))
                        elif "Winter Eternality" in self.traits and key == "mp" and item.mod[key]>0:
                            self.mod_stat(key, (int(0.35*item.mod[key])))
                        elif "Effective Metabolism" in self.traits and key == "vitality" and item.mod[key]>0:
                            if item.type == "food":
                                self.mod_stat(key, (int(2*item.mod[key])))
                            else:
                                self.mod_stat(key, (int(1.5*item.mod[key])))
                        elif "Magical Kin" in self.traits and key == "mp" and item.mod[key]>0:
                            if item.type == "alcohol":
                                self.mod_stat(key, (int(2*item.mod[key])))
                            else:
                                self.mod_stat(key, (int(1.5*item.mod[key])))
                        else:
                            self.mod_stat(key, item.mod[key])
                    else:
                        if "Left-Handed" in self.traits and item.slot == "smallweapon":
                            self.stats.imod[key] += item.mod[key]*2
                        elif "Left-Handed" in self.traits and item.slot == "weapon":
                            self.stats.imod[key] += int(item.mod[key]*0.5)
                        elif "Knightly Stance" in self.traits and key == "defence":
                            self.stats.imod[key] += int(item.mod[key]*1.3)
                        elif "Berserk" in self.traits and key == "defence":
                            self.stats.imod[key] += int(item.mod[key]*0.5)
                        elif "Berserk" in self.traits and key == "attack":
                            self.stats.imod[key] += int(item.mod[key]*2)
                        elif "Hollow Bones" in self.traits and key == "agility" and item.mod[key] <0:
                            pass
                        elif "Elven Ranger" in self.traits and key == "defence" and item.mod[key] <0 and item.type in ["bow", "crossbow", "throwing"]:
                            pass
                        elif "Sword Master" in self.traits and item.type == "sword":
                            self.stats.imod[key] += int(item.mod[key]*1.3)
                        elif "Dagger Master" in self.traits and item.type == "dagger":
                            self.stats.imod[key] += int(item.mod[key]*1.3)
                        elif "Shield Master" in self.traits and item.type == "shield":
                            self.stats.imod[key] += int(item.mod[key]*1.3)
                        elif "Bow Master" in self.traits and item.type == "bow":
                            self.stats.imod[key] += int(item.mod[key]*1.3)
                        else:
                            self.stats.imod[key] += item.mod[key]
            for key in item.mod_skills:
                if key in self.SKILLS:
                    if not (item.skillmax and self.get_skill(key) >= item.skillmax): # Multi messes this up a bit.
                        s = self.stats.skills[key] # skillz
                        sm = self.stats.skills_multipliers[key] # skillz muplties
                        m = item.mod_skills[key] # mod
                        sm[0] += m[0]
                        sm[1] += m[1]
                        sm[2] += m[2]
                        s[0] += m[3]
                        s[1] += m[4]
                else:
                    msg = "'%s' item tried to apply unknown skill: %s!"
                    devlog.warning(str(msg % (item.id, key)))

            # Traits:
            if hasattr(self, "traits"):
                for entry in item.removetraits:
                    if entry in traits:
                        if item.slot not in ['consumable', 'misc'] or (item.slot == 'consumable' and item.ctemp):
                            self.remove_trait(traits[entry], truetrait=False)
                        else:
                            self.remove_trait(traits[entry])
                    else:
                        devlog.warning(str("Item: {} has tried to remove an invalid trait: {}!".format(item.id, entry)))

                for entry in item.addtraits:
                    if entry in traits:
                        if item.slot not in ['consumable', 'misc'] or (item.slot == 'consumable' and item.ctemp):
                            self.apply_trait(traits[entry], truetrait=False)
                        else:
                            self.apply_trait(traits[entry])
                    else:
                        devlog.warning(str("Item: %s has tried to apply an invalid trait: %s!" % (item.id, entry)))

            # Effects:
            if hasattr(self, "effects"):
                if item.slot == 'consumable' and item.type == 'food':
                    self.effects['Food Poisoning']['activation_count'] += 1
                    if self.effects['Food Poisoning']['activation_count'] == 7:
                        self.enable_effect('Food Poisoning')

                if item.slot == 'consumable' and item.type == 'alcohol':
                    self.effects['Drunk']['activation_count'] += item.mod["joy"]
                    if self.effects['Drunk']['activation_count'] >= 35 and not self.effects['Drunk']['active']:
                        self.enable_effect('Drunk')
                    elif self.effects['Drunk']['active'] and self.AP > 0 and not self.effects['Drinker']['active']:
                        self.AP -=1

                for entry in item.addeffects:
                    if not self.effects[entry]['active']:
                        self.enable_effect(entry)

                for entry in item.removeeffects:
                    if self.effects[entry]['active']:
                        self.disable_effect(entry)

            # Jump away from equipment screen if appropriate:
            if hasattr(store, "dummy") and not dummy:
                if item.jump_to_label:
                    renpy.scene(layer="screens")
                    global_flags.del_flag("hero_equip")
                    eqtarget.inventory.set_page_size(15)
                    hero.inventory.set_page_size(15)

                    jump(item.jump_to_label)

        def remove_item_effects(self, item):
            # Attacks/Magic:
            if hasattr(item, "attacks"):
                for attack in item.attacks:
                    if attack in store.battle_skills:
                        attack = store.battle_skills[attack]
                        self.attack_skills.remove(attack, False)
                    else:
                        devlog.warning("Unknown battle skill %s applied by character: %s (%s)!" % (attack, self.fullname, self.__class__))
                if not self.attack_skills:
                    default = self.default_attack_skill
                    self.attack_skills.append(default)

            for spell in item.add_be_spells:
                if spell in store.battle_skills:
                    spell = store.battle_skills[spell]
                    self.magic_skills.remove(spell, False)
                else:
                    devlog.warning("Unknown battle skill %s applied by character: %s (%s)!" % (spell, self.fullname, self.__class__))

            for spell in item.remove_be_spells:
                if spell in store.battle_skills:
                    spell = store.battle_skills[spell]
                    self.magic_skills.append(spell, False)
                else:
                    devlog.warning("Unknown battle skill %s removed by character: %s (%s)!" % (spell, self.fullname, self.__class__))

            # Taking care of stats:
            for key in item.max:
                if key in self.STATS:
                    if "Left-Handed" in self.traits and item.slot == "smallweapon":
                        self.stats.max[key] -= item.max[key]*2
                    elif "Left-Handed" in self.traits and item.slot == "weapon":
                        self.stats.max[key] -= int(item.max[key]*0.5)
                    elif "Knightly Stance" in self.traits and key == "defence":
                        self.stats.max[key] -= int(item.max[key]*1.3)
                    elif "Berserk" in self.traits and key == "defence":
                        self.stats.max[key] -= int(item.max[key]*.5)
                    elif "Berserk" in self.traits and key == "attack":
                        self.stats.max[key] -= int(item.max[key]*2)
                    elif "Hollow Bones" in self.traits and key == "agility" and item.max[key] <0:
                        pass
                    elif "Elven Ranger" in self.traits and key == "defence" and item.max[key] <0 and item.type in ["bow", "crossbow", "throwing"]:
                        pass
                    elif "Sword Master" in self.traits and item.type == "sword":
                        self.stats.max[key] -= int(item.max[key]*1.3)
                    elif "Dagger Master" in self.traits and item.type == "dagger":
                        self.stats.max[key] -= int(item.max[key]*1.3)
                    elif "Shield Master" in self.traits and item.type == "shield":
                        self.stats.max[key] -= int(item.max[key]*1.3)
                    elif "Bow Master" in self.traits and item.type == "bow":
                        self.stats.max[key] -= int(item.max[key]*1.3)
                    else:
                        self.stats.max[key] -= item.max[key]
                else:
                    devlog.warning(str("Failed to apply max stat %s to %s from item: %s!" % (key, self.__class__.__name__, item.id)))
            if "Royal Assassin" in self.traits and item.slot in ["smallweapon", "weapon", "body", "cape", "feet", "wrist", "head"]:
                self.stats.max["attack"] -= int(item.price*0.01)
                self.mod_stat("attack", -int(item.price*0.01))
            elif "Armor Expert" in self.traits and item.slot in ["smallweapon", "weapon", "body", "cape", "feet", "wrist", "head"]:
                self.stats.max["defence"] -= int(item.price*0.01)
                self.mod_stat("defence", -int(item.price*0.01))
            for key in item.min:
                if key in self.STATS:
                    # if (self.stats.min[key] - item.min[key]) >= 0: @Review, prolly no longer required.
                    if "Left-Handed" in self.traits and item.slot == "smallweapon":
                        self.stats.min[key] -= item.min[key]*2
                    elif "Left-Handed" in self.traits and item.slot == "weapon":
                        self.stats.min[key] -= int(item.min[key]*0.5)
                    elif "Knightly Stance" in self.traits and key == "defence":
                        self.stats.min[key] -= int(item.min[key]*1.3)
                    elif "Berserk" in self.traits and key == "defence":
                        self.stats.min[key] -= int(item.min[key]*.5)
                    elif "Berserk" in self.traits and key == "attack":
                        self.stats.min[key] -= int(item.min[key]*2)
                    elif "Hollow Bones" in self.traits and key == "agility" and item.min[key] <0:
                        pass
                    elif "Elven Ranger" in self.traits and key == "defence" and item.min[key] <0 and item.type in ["bow", "crossbow", "throwing"]:
                        pass
                    elif "Sword Master" in self.traits and item.type == "sword":
                        self.stats.min[key] -= int(item.min[key]*1.3)
                    elif "Dagger Master" in self.traits and item.type == "dagger":
                        self.stats.min[key] -= int(item.min[key]*1.3)
                    elif "Shield Master" in self.traits and item.type == "shield":
                        self.stats.min[key] -= int(item.min[key]*1.3)
                    elif "Bow Master" in self.traits and item.type == "bow":
                        self.stats.min[key] -= int(item.min[key]*1.3)
                    else:
                        self.stats.min[key] -= item.min[key]
                else:
                    devlog.warning(str("Failed to apply min stat %s to %s from item: %s!" % (key, self.__class__.__name__, item.id)))

            for key in item.mod:
                if key == "health" and self.health - item.mod[key] <= 0:
                    self.health = 1 # prevents death by accident...
                    continue

                if key == 'gold':
                    self.gold -= item.mod[key]
                elif key == "exp":
                    self.exp -= item.mod[key]
                elif key in ['health', 'mp', 'vitality', 'joy'] or (item.slot in ['consumable', 'misc'] and not (item.slot == 'consumable' and item.ctemp)):
                    self.mod_stat(key, -item.mod[key])
                else:
                    if "Left-Handed" in self.traits and item.slot == "smallweapon":
                        self.stats.imod[key] -= item.mod[key]*2
                    elif "Left-Handed" in self.traits and item.slot == "weapon":
                        self.stats.imod[key] -= int(item.mod[key]*0.5)
                    elif "Knightly Stance" in self.traits and key == "defence":
                        self.stats.imod[key] -= int(item.mod[key]*1.3)
                    elif "Berserk" in self.traits and key == "defence":
                        self.stats.imod[key] -= int(item.mod[key]*0.5)
                    elif "Berserk" in self.traits and key == "attack":
                        self.stats.imod[key] -= int(item.mod[key]*2)
                    elif "Hollow Bones" in self.traits and key == "agility" and item.mod[key] <0:
                        pass
                    elif "Elven Ranger" in self.traits and key == "defence" and item.mod[key] <0 and item.type in ["bow", "crossbow", "throwing"]:
                        pass
                    elif "Sword Master" in self.traits and item.type == "sword":
                        self.stats.imod[key] -= int(item.mod[key]*1.3)
                    elif "Shield Master" in self.traits and item.type == "shield":
                        self.stats.imod[key] -= int(item.mod[key]*1.3)
                    elif "Dagger Master" in self.traits and item.type == "dagger":
                        self.stats.imod[key] -= int(item.mod[key]*1.3)
                    elif "Bow Master" in self.traits and item.type == "bow":
                        self.stats.imod[key] -= int(item.mod[key]*1.3)
                    else:
                        self.stats.imod[key] -= item.mod[key]

            for key in item.mod_skills:
                if key in self.SKILLS:
                    s = self.stats.skills[key] # skillz
                    sm = self.stats.skills_multipliers[key] # skillz muplties
                    m = item.mod_skills[key] # mod
                    sm[0] -= m[0]
                    sm[1] -= m[1]
                    sm[2] -= m[2]
                    s[0] -= m[3]
                    s[1] -= m[4]
                else:
                    msg = "'%s' item tried to apply unknown skill: %s!"
                    devlog.warning(str(msg % (item.id, key)))

            # Taking care of traits/effect (for girls):
            if hasattr(self, "traits"):
                for entry in item.addtraits:
                    if entry in traits:
                        if item.slot not in ['consumable', 'misc'] or (item.slot == 'consumable' and item.ctemp):
                            self.remove_trait(traits[entry], truetrait=False)
                        else:
                            self.remove_trait(traits[entry])
                    else:
                        devlog.warning(str("Item: %s has tried to remove an invalid trait: %s!" % (item.id, entry)))

                for entry in item.removetraits:
                    if entry in traits:
                        if item.slot not in ['consumable', 'misc'] or (item.slot == 'consumable' and item.ctemp):
                            self.apply_trait(traits[entry], truetrait=False)
                        else:
                            self.apply_trait(traits[entry])
                    else:
                        devlog.warning(str("Item: %s has tried to apply an invalid trait: %s!" % (item.id, entry)))

            if hasattr(self, "effects"):
                for entry in item.addeffects:
                    if self.effects[entry]['active']:
                        self.disable_effect(entry)

                for entry in item.removeeffects:
                    if not self.effects[entry]['active']:
                        self.enable_effect(entry)

        def item_counter(self):
            # Timer to clear consumable blocks
            for key in self.consblock.keys():
                self.consblock[key] -= 1
                if self.consblock[key] <= 0:
                    del(self.consblock[key])

            # Timer to remove effects of a temp consumer items
            for key in self.constemp.keys():
                self.constemp[key] -= 1
                if self.constemp[key] <= 0:
                    self.remove_item_effects(items[key])
                    del(self.constemp[key])

            # Counter to apply misc item effects and settle misc items conditions:
            for key in self.miscitems.keys():
                self.miscitems[key] -= 1
                if self.miscitems[key] <= 0:
                    self.apply_item_effects(items[key])

                    # For Misc item that self-destruct
                    if items[key].mdestruct:
                        del(self.miscitems[key])
                        self.eqslots['misc'] = False
                        if not items[key].mreusable:
                            self.miscblock.append(items[key].id)
                        return

                    if not items[key].mreusable:
                        self.miscblock.append(items[key].id)
                        self.unequip(items[key])
                        return

                    self.miscitems[key] = items[key].mtemp

        # Trait methods *now for all characters:
        # Traits methods
        def apply_trait(self, trait, truetrait=True): # Applies trait effects
            self.traits.apply(trait, truetrait=truetrait)

        def remove_trait(self, trait, truetrait=True):  # Removes trait effects
            self.traits.remove(trait, truetrait=truetrait)

        # Effects:
        ### Effects Methods
        def enable_effect(self, effect):
            if effect == "Poisoned" and "Artificial Body" not in self.traits:
                self.effects['Poisoned']['active'] = True
                self.effects['Poisoned']['duration'] = 0
                self.effects['Poisoned']['penalty'] = randint(1, 3)

            elif effect == "Unstable":
                self.effects['Unstable']['active'] = True
                self.effects['Unstable']['day_log'] = day
                self.effects['Unstable']['day_target'] = day + randint(2,4)
                self.effects['Unstable']['joy_mod'] = randint(20, 30)
                if dice(50):
                    self.effects['Unstable']['joy_mod'] = -self.effects['Unstable']['joy_mod']

            elif effect == "Optimist":
                self.effects['Optimist']['active'] = True

            elif effect == "Blood Connection":
                self.effects['Blood Connection']['active'] = True

            elif effect == "Horny":
                self.effects['Horny']['active'] = True

            elif effect == "Regeneration":
                self.effects['Regeneration']['active'] = True

            elif effect == "MP Regeneration":
                self.effects['MP Regeneration']['active'] = True

            elif effect == "Small Regeneration":
                self.effects['Small Regeneration']['active'] = True

            elif effect == "Injured":
                self.effects['Injured']['active'] = True

            elif effect == "Exhausted":
                self.effects['Exhausted']['active'] = True

            elif effect == "Drinker":
                self.effects['Drinker']['active'] = True

            elif effect == "Silly":
                self.effects['Silly']['active'] = True

            elif effect == "Intelligent":
                self.effects['Intelligent']['active'] = True

            elif effect == "Depression":
                self.effects['Depression']['active'] = True

            elif effect == "Elation":
                self.effects['Elation']['active'] = True

            elif effect == "Pessimist":
                self.effects["Pessimist"]["active"] = True

            elif effect == "Vigorous":
                self.effects["Vigorous"]["active"] = True

            elif effect == "Composure":
                self.effects['Composure']['active'] = True

            elif effect == "Down with Cold":
                self.effects['Down with Cold']['active'] = True
                self.effects['Down with Cold']['count'] = day
                self.effects['Down with Cold']['duration'] = randint(7, 14)
                self.effects['Down with Cold']['health'] = randint(2, 5)
                self.effects['Down with Cold']['vitality'] = randint(20, 40)
                self.effects['Down with Cold']['joy'] = randint(2, 5)
                self.effects['Down with Cold']['healthy_again'] = day + self.effects['Down with Cold']['duration']

            elif effect == "Kleptomaniac":
                self.effects["Kleptomaniac"]['active'] = True

            elif effect == "Slow Learner":
                self.effects["Slow Learner"]['active'] = True

            elif effect == "Fast Learner":
                self.effects["Fast Learner"]['active'] = True

            elif effect == "Drowsy":
                self.effects["Drowsy"]['active'] = True

            elif effect == "Fast Metabolism":
                self.effects["Fast Metabolism"]["active"] = True

            elif effect == "Drunk":
                self.effects["Drunk"]["active"] = True

            elif effect == "Lactation":
                self.effects["Lactation"]['active'] = True

            elif effect == "Loyal":
                self.effects["Loyal"]['active'] = True

            elif effect == "Introvert":
                self.effects['Introvert']['active'] = True

            elif effect == "Impressible":
                self.effects['Impressible']['active'] = True

            elif effect == "Calm":
                self.effects['Calm']['active'] = True

            elif effect == "Insecure":
                self.effects['Insecure']['active'] = True

            elif effect == "Extrovert":
                self.effects['Extrovert']['active'] = True

            elif effect == "Sibling":
                self.effects['Sibling']['active'] = True

            elif effect == "Assertive":
                self.effects['Assertive']['active'] = True

            elif effect == "Diffident":
                self.effects['Diffident']['active'] = True

            elif effect == "Food Poisoning":
                self.effects['Food Poisoning']['active'] = True
                self.effects['Food Poisoning']['count'] = day
                self.effects['Food Poisoning']['health'] = randint(8, 12)
                self.effects['Food Poisoning']['vitality'] = randint(40, 100)
                self.effects['Food Poisoning']['joy'] = randint(8, 12)
                self.effects['Food Poisoning']['healthy_again'] = day + 2

        def disable_effect(self, effect):
            if effect == "Poisoned":
                for key in self.effects["Poisoned"]:
                    if key != "desc":
                        self.effects["Poisoned"][key] = False

            elif effect == "Unstable":
                for key in self.effects["Unstable"]:
                    if key != "desc":
                        self.effects["Unstable"][key] = False

            elif effect == "Optimist":
                self.effects['Optimist']['active'] = False

            elif effect == "Blood Connection":
                self.effects['Blood Connection']['active'] = False

            elif effect == "Horny":
                self.effects['Horny']['active'] = False

            elif effect == "Regeneration":
                self.effects['Regeneration']['active'] = False

            elif effect == "MP Regeneration":
                self.effects['MP Regeneration']['active'] = False

            elif effect == "Small Regeneration":
                self.effects['Small Regeneration']['active'] = False

            elif effect == "Drinker":
                self.effects['Drinker']['active'] = False

            elif effect == "Injured":
                self.effects['Injured']['active'] = False

            elif effect == "Exhausted":
                self.effects['Exhausted']['active'] = False

            elif effect == "Silly":
                self.effects['Silly']['active'] = False

            elif effect == "Depression":
                self.effects['Depression']['active'] = False

            elif effect == "Elation":
                self.effects['Elation']['active'] = False

            elif effect == "Intelligent":
                self.effects['Intelligent']['active'] = False

            elif effect == "Vigorous":
                self.effects['Vigorous']['active'] = False

            elif effect == "Pessimist":
                self.effects["Pessimist"]["active"] = False

            elif effect == "Fast Metabolism":
                self.effects["Fast Metabolism"]["active"] = False

            elif effect == "Drunk":
                for key in self.effects["Drunk"]:
                    if key != "desc":
                        self.effects["Drunk"][key] = False

            elif effect == "Composure":
                self.effects['Composure']['active'] = False

            elif effect == "Down with Cold":
                for key in self.effects["Down with Cold"]:
                    if key != "desc":
                        self.effects["Down with Cold"][key] = False

            elif effect == "Kleptomaniac":
                self.effects["Kleptomaniac "]['active'] = False

            elif effect == "Slow Learner":
                self.effects["Slow Learner"]['active'] = False

            elif effect == "Fast Learner":
                self.effects["Fast Learner"]['active'] = False

            elif effect == "Introvert":
                self.effects['Introvert']['active'] = False

            elif effect == "Impressible":
                self.effects['Impressible']['active'] = False

            elif effect == "Calm":
                self.effects['Calm']['active'] = False

            elif effect == "Drowsy":
                self.effects['Drowsy']['active'] = False

            elif effect == "Lactation":
                self.effects['Lactation']['active'] = False

            elif effect == "Loyal":
                self.effects['Loyal']['active'] = False

            elif effect == "Extrovert":
                self.effects['Extrovert']['active'] = False

            elif effect == "Insecure":
                self.effects['Insecure']['active'] = False

            elif effect == "Sibling":
                self.effects['Sibling']['active'] = False

            elif effect == "Assertive":
                self.effects['Assertive']['active'] = False

            elif effect == "Diffident":
                self.effects['Diffident']['active'] = False

            elif effect == "Food Poisoning":
                for key in self.effects["Food Poisoning"]:
                    if key != "desc":
                        self.effects["Food Poisoning"][key] = False

        def apply_effects(self, effect):
            '''Called on next day, applies effects'''
            if effect == "Poisoned":
                self.effects['Poisoned']['duration'] += 1
                self.effects['Poisoned']['penalty'] += self.effects['Poisoned']['duration'] * 5
                self.health -= self.effects['Poisoned']['penalty']

            elif effect == "Unstable":
                unstable = self.effects['Unstable']
                unstable['day_log'] += 1
                if unstable['day_log'] == unstable['day_target']:
                    self.joy += unstable['joy_mod']
                    unstable['day_log'] = day
                    unstable['day_target'] = day + randint(2, 4)
                    unstable['joy_mod'] = randint(20, 30) if randrange(2) else -randint(20, 30)

            elif effect == "Optimist":
                if self.joy >= 30:
                    self.joy += 1

            elif effect == "Blood Connection":
                self.disposition += 1
                self.character -=1

            elif effect == "Regeneration":
                h = 0
                if "Summer Eternality" in self.traits:
                    h += int(self.get_max("health")*0.5)
                if h <= 0:
                    h = 1
                self.health += h

            elif effect == "MP Regeneration":
                h = 0
                if "Winter Eternality" in self.traits:
                    h += int(self.get_max("mp")*0.5)
                if h <= 0:
                    h = 1
                self.mp += h

            elif effect == "Small Regeneration":
                self.health += 10

            elif effect == "Depression":
                if self.joy >= 30:
                    self.disable_effect('Depression')
                else:
                    self.AP -= 1

            elif effect == "Elation":
                if self.joy < 95:
                    self.disable_effect('Elation')
                else:
                    self.AP += 1

            elif effect == "Pessimist":
                if self.joy > 80:
                    self.joy -= 2
                elif self.joy > 10:
                    self.joy -= 1

            elif effect == "Assertive":
                if self.character < self.get_max("character")*0.5:
                    self.character += 2

            elif effect == "Diffident":
                if self.character > self.get_max("character")*0.6:
                    self.character -= 1

            elif effect == "Composure":
                if self.joy < 50:
                    self.joy += 1
                elif self.joy > 70:
                    self.joy -= 1

            elif effect == "Vigorous":
                if self.vitality < self.get_max("vitality")*0.25:
                    self.vitality += randint(2, 3)
                elif self.vitality < self.get_max("vitality")*0.5:
                    self.vitality += randint(1, 2)

            elif effect == "Down with Cold":
                if self.effects['Down with Cold']['healthy_again'] <= self.effects['Down with Cold']['count']:
                    self.disable_effect('Down with Cold')
                    return
                if self.health > 50:
                    self.health -= self.effects['Down with Cold']['health']
                self.vitality -= self.effects['Down with Cold']['vitality']
                self.joy -= self.effects['Down with Cold']['joy']
                self.effects['Down with Cold']['count'] += 1
                if self.effects['Down with Cold']['healthy_again'] <= self.effects['Down with Cold']['count']:
                    self.disable_effect('Down with Cold')

            elif effect == "Kleptomaniac":
                if dice(75):
                    self.gold += max(1, randint(1, self.luck+50))

            elif effect == "Injured":
                if self.health > int(self.get_max("health")*0.35):
                    self.health = int(self.get_max("health")*0.35)
                if self.vitality > int(self.get_max("vitality")*0.5):
                    self.vitality = int(self.get_max("vitality")*0.5)
                self.AP -= 1
                self.joy -= 10

            elif effect == "Exhausted":
                if self.vitality > 5:
                    self.vitality = 5
                self.AP -= 1

            elif effect == "Lactation": # TO DO: maybe add milking job, like in WM? with much more milk outcome than this effect has
                if self.health >= 30 and self.vitality >= 30:
                    if self.status == "slave" or check_lovers(self, hero):
                        if "Small Boobs" in self.traits:
                            hero.add_item("Bottle of Milk")
                        elif "Average Boobs" in self.traits:
                            hero.add_item("Bottle of Milk", randint(1, 2))
                        elif "Big Boobs" in self.traits:
                            hero.add_item("Bottle of Milk", randint(2, 3))
                        else:
                            hero.add_item("Bottle of Milk", randint(2, 5))
                    elif not(has_items("Bottle of Milk", [self])): # in order to not stack bottles of milk into free chars inventories they get only one, and only if they had 0
                        self.add_item("Bottle of Milk")

            elif effect == "Silly":
                if self.intelligence >= 200:
                    self.intelligence -= 20
                if self.intelligence >= 100:
                    self.intelligence -= 10
                elif self.intelligence >= 25:
                    self.intelligence -= 5
                else:
                    self.intelligence = 20

            elif effect == "Intelligent":
                if self.joy >= 75 and self.vitality >= self.get_max("vitality")*0.75 and self.health >= self.get_max("health")*0.75:
                    self.intelligence += 1

            elif effect == "Sibling":
                if self.disposition < 100:
                    self.disposition += 2
                elif self.disposition < 200:
                    self.disposition += 1


            elif effect == "Drunk":
                self.vitality -= self.effects['Drunk']['activation_count']
                if self.health > 50:
                    self.health -= 10
                self.joy -= 5
                self.mp -= 20
                self.disable_effect('Drunk')

            elif effect == "Food Poisoning":
                if self.effects['Food Poisoning']['healthy_again'] <= self.effects['Food Poisoning']['count']:
                    self.disable_effect('Food Poisoning')
                    return
                if self.health > 10:
                    self.health -= self.effects['Food Poisoning']['health']
                self.vitality -= self.effects['Food Poisoning']['vitality']
                self.joy -= self.effects['Food Poisoning']['joy']
                self.effects['Food Poisoning']['count'] += 1
                if self.effects['Food Poisoning']['healthy_again'] <= self.effects['Food Poisoning']['count']:
                    self.disable_effect('Food Poisoning')

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

            # add Character:
            if not self.say:
                self.say = Character(self.nickname, show_two_window=True, show_side_image=self.show("portrait", resize=(120, 120)), **self.say_style)

            # Stats log:
            self.log_stats()
            self.restore_ap()

        def next_day(self):
            # We assume this to be safe for any character...
            # Day counter flags:
            for flag in self.flags.keys():
                if flag.startswith("_day_countdown"):
                    self.down_counter(flag, value=1, min=0, delete=True)
                # Deleting _jobs flags once all jobs are complete.
                elif flag.startswith("_jobs"):
                    self.del_flag(flag)

            # Run the effects if they are availible:
            if hasattr(self, "effects"):
                for key in self.effects:
                    if self.effects[key]['active']:
                        self.apply_effects(key)

            # Log stats to display changes on the next day (Only for chars to whom it's useful):
            if self in hero.chars:
                self.log_stats()


    class ArenaFighter(PytCharacter):
        """
        Base class for Custom Arena fighters.
        """
        def __init__(self):
            super(ArenaFighter, self).__init__(arena=True)

            # Basic Images:
            self.img_db = dict()
            self.cache = list()

            self.unique = True


        def show(self, tag, resize=(None, None), cache=True):
            if tag == "battle":
                tag = "combat"
            if tag == "fighting":
                tag = "combat"
            if cache:
                for entry in self.cache:
                    if entry[0] == tag:
                        return ProportionalScale(entry[1], resize[0], resize[1])

            if tag in self.img_db:
                path = choice(self.img_db[tag])
            else:
                path = choice(self.img_db["battle_sprite"])

            if cache:
                self.cache.append([tag, path])

            img = ProportionalScale(path, resize[0], resize[1])

            return img

        def restore_ap(self):
            self.AP = self.baseAP + int(self.constitution / 20)

        def init(self):
            # Normalize character
            if not self.fullname:
                self.fullname = self.name
            if not self.nickname:
                self.nickname = self.name


            self.arena_willing = True # Indicates the desire to fight in the Arena
            self.arena_permit = True # Has a permit to fight in main events of the arena.
            self.arena_active = True # Indicates that girl fights at Arena at the time.
            if self.unique:
                self.arena_active = False # Indicates that char fights at Arena at the time.

            # add Character:
            super(ArenaFighter, self).init()


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

        def show(self, what, resize=(None, None), cache=True):
            if what == "battle":
                what = "combat"
            if what == "fighting":
                what = "combat"
            if what == "portrait":
                what = self.portrait
            elif what == "battle_sprite":
                what = self.battle_sprite
            elif what == "combat" and self.combat_img:
                what = self.combat_img
            else:
                what = self.battle_sprite

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
            self.cache = list()
            self.gold = 20000
            self.name = 'Player'
            self.fullname = 'Player'
            self.nickname = 'Player'
            self._location = locations["Streets"]
            self.status = "free"
            self.gender = "male"

            # Player only...
            self.corpses = list() # Dead bodies go here until disposed off. Why the fuck here??? There gotta be a better place for dead chars than MC's class. We're not really using this atm anyway....

            self._buildings = list()
            self._chars = list()

            self.guard_relay = {"bar_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                           "whore_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                           "club_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0}
                                           }

            for p in pytRelayProxyStore:
                p.reset(self)

            self.fin = Finances(self)

            # Team:
            self.team = Team(implicit=[self])
            self.team.name = "Player Team"

        # Fin Methods:
        def take_money(self, value, reason="Other"):
            return self.fin.take_money(value, reason)

        def add_money(self, value, reason="Other"):
            self.fin.add_money(value, reason)

        # Girls/Borthels/Buildings Ownership
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
            return [building for building in self.buildings if isinstance(building, DirtyBuilding)]

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
            return [building for building in self.buildings if isinstance(building, NewStyleUpgradableBuilding) or isinstance(building, UpgradableBuilding)]

        def add_building(self, building):
            if building not in self._buildings:
                self._buildings.append(building)

        def remove_building(self, building):
            if building in self._buildings:
                self._buildings.remove(building)
            else:
                raise Exception, "This building does not belong to the player!!!"

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
        # Show to mimic girls method behaviour:
        def has_image(self, *tags):
            """
            Returns True if image is found.
            """
            return True

        def show(self, tag, resize=(None, None), cache=True):
            if tag == "battle":
                tag = "combat"
            if tag == "fighting":
                tag = "combat"
            if tag == "cportrait":
                tag = "cportrait"
            if tag == "sprofile":
                tag = "sprofile"
            if cache:
                for entry in self.cache:
                    if entry[0] == tag:
                        return ProportionalScale(entry[1], resize[0], resize[1])

            if tag in self.img_db:
                path = choice(self.img_db[tag])
            else:
                path = choice(self.img_db["battle_sprite"])

            if cache:
                self.cache.append([tag, path])

            img = ProportionalScale(path, resize[0], resize[1])

            return img

        # ----------------------------------------------------------------------------------
        # Next Day:
        def nd_auto_train(self):
            if self.flag("train_with_witch"):
                if self.get_free_ap():
                    if self.take_money(self.get_training_price(), "Training"):
                        self.auto_training("train_with_witch")
                        self.reservedAP += 1
                        txt += "\nSuccessfully completed scheduled training with Abby the Witch!"
                    else:
                       txt +=  "\nNot enought funds to train with Abby the Witch. Auto-Training will be disabled!"
                       self.del_flag("train_with_witch")
                else:
                    txt += "\nNot enough AP left in reserve to train with Abby the Witch. Auto-Training will not be disabled ({color=[red]}This character will start next day with 0 AP{/color})!"

            if self.flag("train_with_aine"):
                if self.get_free_ap():
                    if self.take_money(self.get_training_price(), "Training"):
                        self.auto_training("train_with_aine")
                        self.reservedAP += 1
                        txt += "\nSuccessfully completed scheduled training with Aine!"
                    else:
                       txt +=  "\nNot enought funds to train with Aine. Auto-Training will be disabled!"
                       self.del_flag("train_with_aine")
                else:
                    txt += "\nNot enough AP left in reserve to train with Aine. Auto-Training will not be disabled ({color=[red]}This character will start next day with 0 AP{/color})!"

            if self.flag("train_with_xeona"):
                if self.get_free_ap():
                    if self.take_money(self.get_training_price(), "Training"):
                        self.auto_training("train_with_xeona")
                        self.reservedAP += 1
                        txt += "\nSuccessfully completed scheduled combat training with Xeona!"
                    else:
                       txt +=  "\nNot enought funds to train with Xeona. Auto-Training will be disabled!"
                       self.del_flag("train_with_xeona")
                else:
                    txt += "\nNot enough AP left in reserve to train with Xeona. Auto-Training will not be disabled ({color=[red]}This character will start next day with 0 AP{/color})!"

        def nd_pay_taxes(self):
            if calendar.weekday() == "Monday" and day != 1 and not config.developer:
                txt += "\nIt's time to pay taxes!\n"
                income = dict()
                businesses = [b for b in self.buildings if hasattr(b, "fin")]
                for b in businesses:
                    for _day in b.fin.game_fin_log:
                        if int(_day) > day - 7:
                            for key in b.fin.game_fin_log[_day][0]["private"]:
                                income[key] = income.get(key, 0) + b.fin.game_fin_log[_day][0]["private"][key]
                            for key in b.fin.game_fin_log[_day][0]["work"]:
                                income[key] = income.get(key, 0) + b.fin.game_fin_log[_day][0]["work"][key]

                income = sum(income.values())
                txt += "Over the past week your taxable income accounted for: {color=[gold]}%d Gold{/color}. " % income
                if self.fin.income_tax_debt:
                    txt += "You are indebted to the govenment: %d Gold." % self.fin.income_tax_debt
                txt += "\n"
                if income <= 5000:
                    txt += "You may concider yourself lucky as any sum below 5000 Gold is not taxable. Otherwise the government would have totally ripped you off :)"
                elif income <= 25000:
                    tax = int(round(income*0.1))
                    txt += "Your income tax for this week is %d. " % tax
                    if self.fin.income_tax_debt:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                        txt += "That makes it a total amount of: %d Gold. " % self.fin.income_tax_debt
                    else:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                    if self.take_money(self.fin.income_tax_debt, "Income Taxes"):
                        txt += "\nYou were able to pay that in full!\n"
                        self.fin.income_tax_debt = 0
                    else:
                        txt += "\nYou've did not have enough money... Be advised that if your debt to the government reaches 50000, they will start indiscriminately confiscate your property. (meaning that you will loose everything that you own at repo prices).\n"
                elif income <= 50000:
                    tax = int(round(income*0.2))
                    txt += "Your income tax for this week is %d. " % tax
                    if self.fin.income_tax_debt:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                        txt += "That makes it a total amount of: %d Gold. " % self.fin.income_tax_debt
                    else:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                    if self.take_money(self.fin.income_tax_debt, "Income Taxes"):
                        txt += "\nYou were able to pay that in full!\n"
                        self.fin.income_tax_debt = 0
                    else:
                        txt += "\nYou've did not have enough money... Be advised that if your debt to the government reaches 50000, they will start indiscriminately confiscate your property. (meaning that you will loose everything that you own at repo prices).\n"
                elif income <= 100000:
                    tax = int(round(income*0.3))
                    txt += "Your income tax for this week is %d. " % tax
                    if self.fin.income_tax_debt:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                        txt += "That makes it a total amount of: %d Gold. " % self.fin.income_tax_debt
                    else:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                    if self.take_money(self.fin.income_tax_debt, "Income Taxes"):
                        txt += "\nYou were able to pay that in full!\n"
                        self.fin.income_tax_debt = 0
                    else:
                        txt += "\nYou've did not have enough money... Be advised that if your debt to the government reaches 50000, they will start indiscriminately confiscate your property. (meaning that you will loose everything that you own at repo prices).\n"
                elif income <= 200000:
                    tax = int(round(income*0.4))
                    txt += "Your income tax for this week is %d. " % tax
                    if self.fin.income_tax_debt:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                        txt += "That makes it a total amount of: %d Gold. " % self.fin.income_tax_debt
                    else:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                    if self.take_money(self.fin.income_tax_debt, "Income Taxes"):
                        txt += "\nYou were able to pay that in full!\n"
                        self.fin.income_tax_debt = 0
                    else:
                        txt += "\nYou've did not have enough money... Be advised that if your debt to the government reaches 50000, they will start indiscriminately confiscate your property. (meaning that you will loose everything that you own at repo prices).\n"
                else:
                    tax = int(round(income*0.45))
                    txt += "Your income tax for this week is %d. " % tax
                    if self.fin.income_tax_debt:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                        txt += "That makes it a total amount of: %d Gold. " % self.fin.income_tax_debt
                    else:
                        self.fin.income_tax_debt = self.fin.income_tax_debt + tax
                    if self.take_money(self.fin.income_tax_debt, "Income Taxes"):
                        txt += "\nYou were able to pay that in full!\n"
                        self.fin.income_tax_debt = 0
                    else:
                        txt += "\nYou've did not have enough money... Be advised that if your debt to the government reaches 50000, they will start indiscriminately confiscate your property. (meaning that you will loose everything that you own at repo prices).\n"

                txt += choice(["\nWe're not done yet...\n", "\nProperty tax:\n", "\nProperty taxes next!\n"])
                b_tax = 0
                s_tax = 0
                for b in businesses:
                    b_tax += int(b.price*0.04)
                for char in self.chars:
                    if char.status == "slave":
                        s_tax += int(char.fin.get_price()*0.05)
                if b_tax:
                    txt += "Your property taxes for your real estate are: %d Gold. " % b_tax
                if s_tax:
                    txt += "For Slaves that you own, property tax is: %d Gold." % s_tax
                tax = b_tax + s_tax
                if tax:
                    txt += "\nThat makes it a total of {color=[gold]}%d Gold{/color}" % tax
                    if self.fin.property_tax_debt:
                        txt += " Don't worry, we didn't forget about your debt of %d Gold either. Yeap, there are just the two unevitable things in life: Death and Paying your tax on Monday!" % self.fin.property_tax_debt
                        self.fin.property_tax_debt += tax
                    else:
                        self.fin.property_tax_debt += tax
                    if self.take_money(self.fin.property_tax_debt, "Property Taxes"):
                        txt += "\nWell done, but your wallet feels a lot lighter now :)\n"
                        self.fin.property_tax_debt = 0
                    else:
                        txt += "\nYour payment failed...\n"
                else:
                    txt += "\nHowever, you do not own much...\n"

                total_debt = self.fin.income_tax_debt + self.fin.property_tax_debt
                if total_debt:
                    txt += "\n\nYour current total debt to the govenment is {color=[gold]}%d Gold{/color}!" % total_debt
                if total_debt > 50000:
                    txt += " {color=[red]}... And... your're pretty much screwed because it is above 50000!{/color} Your property will now be confiscated :("
                    all_properties = list()
                    for char in hero.chars:
                        if char.status == "slave":
                            all_properties.append(char)
                    for b in businesses:
                        all_properties.append(b)
                    shuffle(all_properties)
                    while total_debt and all_properties:
                        multiplier = choice([0.4, 0.5, 0.6])
                        confiscate = all_properties.pop()
                        if isinstance(confiscate, Building): # TODO: This may need to be revised.
                            price = confiscate.price
                            if self.location == confiscate:
                                self.location = hero
                            for char in self.chars:
                                if char.location == confiscate:
                                    char.location = hero
                                    char.action = None
                            self.remove_brothel(confiscate)
                        elif isinstance(confiscate, Char):
                            price = confiscate.fin.get_price()
                            hero.remove_char(confiscate)
                            confiscate.location = 'slavemarket'
                            if confiscate in self.team:
                                self.team.remove(confiscate)

                        txt += choice(["\n%s has been confiscated for a price of %s of the original value. " % (confiscate.name, multiplier),
                                               "\nThose sobs took %s from you! " % confiscate.name,
                                               "\nYou've lost %s! If only you were better at managing your business... " % confiscate.name])
                        total_debt = total_debt - int(price*multiplier)
                        if total_debt > 0:
                            txt += "You are still required to pay %s Gold." % total_debt
                        else:
                            txt += "Your debt has been payed in full!"
                            if total_debt <= 0:
                                total_debt = -total_debt
                                txt += " You get a sum of %d Gold returned to you from the last repo!" % total_debt
                                hero.add_money(total_debt, reason="Other")
                                total_debt = 0
                        if not all_properties and total_debt:
                            txt += "\n You do not own anything that might be reposessed by the government..."
                            txt += " You've been declared bankrupt and your debt is now Null and Void!"
                        self.fin.income_tax_debt = 0
                        self.fin.property_tax_debt = 0

        def next_day(self):
            # ND Logic....
            # Relay from GuardJob:

            img = 'profile'
            txt = "" # For future reports...
            flag_red = False

            for event in self.guard_relay:
                for stat in self.guard_relay[event]["stats"]:
                    if stat == "exp":
                        self.exp += self.guard_relay[event]["stats"][stat]
                    elif stat in self.STATS:
                        self.mod_stat(stat, self.guard_relay[event]["stats"][stat])

            # -------------------->
            txt += "MC Report:\n\n"

            if self.location == "Streets":
                self.health -= randint(1, 2)
                flag_red = True
                txt += "{color=[red]}You should find some shelter for the night... it's not healthy to sleep outside.{/color}\n"

            # If in own dungeon
            elif self.location == TrainingDungeon.NAME:
                txt += "You've spent a night at your training dungeon."

                if self.AP > 0:
                    txt += "\nYou've had some Action Points left from the day so you've tried to improve yourself to the very best of your ability to do so! \n"
                    for ap in xrange(self.AP):
                        self.health += randint(5, 10)
                        self.vitality += randint(50, 70)
                        self.mp += randint(5, 10)
                        for stat in self.STATS:
                            if stat not in ["luck", "alignment", "vitality"]:
                                if dice(1 + int(round(self.luck/20.0))):
                                        self.mod_stat(stat, 1)

            else:
                txt += "You've comfortably spent a night under the roof of your dwelling."

                if self.AP > 0:
                    txt += "\nYou've had some Action Points left from the day so you've tried to improve yourself to the very best of your ability to do so! \n"
                    for ap in xrange(self.AP):
                        self.health += randint(5, 10)
                        self.vitality += randint(50, 70)
                        self.mp += randint(5, 10)
                        for stat in self.STATS:
                            if stat not in ["luck", "alignment", "vitality"]:
                                if dice(1 + int(round(self.luck/20.0))):
                                        self.mod_stat(stat, 1)

            # Training with NPCs --------------------------------------->
            self.nd_auto_train()

            # -------------
            # Finances related
            self.fin.next_day()

            # Taxes:
            self.nd_pay_taxes()

            # ------------
            # Stats log:
            statmod = dict()
            for stat in self.stats.log:
                if stat == "exp":
                    statmod[stat] = self.exp - self.stats.log[stat]
                elif stat == "level":
                    statmod[stat] = self.level - self.stats.log[stat]
                else:
                    statmod[stat] = self.stats[stat] - self.stats.log[stat]

            # ------------
            # Create the event:
            evt = NDEvent()
            evt.red_flag = flag_red
            evt.charmod = statmod
            evt.type = 'mcndreport'
            evt.char = self
            evt.img = img
            evt.txt = txt
            NextDayEvents.append(evt)

            # -------------
            self.cache = list()
            self.item_counter()
            self.restore_ap()
            self.reservedAP = 0
            self.log_stats()

            self.guard_relay = {"bar_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                "whore_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                "club_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                }

            for p in pytRelayProxyStore:
                p.reset(self)

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
        MOOD_TAGS = set(["angry", "confident", "defiant", "ecstatic", "happy", "indifferent", "provocative", "sad", "scared", "shy", "tired", "uncertain"])
        UNIQUE_SAY_SCREEN_PORTRAIT_OVERLAYS = ["zoom_fast", "zoom_slow", "test_case"]
        def __init__(self):
            super(Char, self).__init__(arena=True, inventory=True, effects=True)
            # Game mechanics assets
            self.gender = 'female'
            self.race = ""
            # Compability with crazy mod:
            self.desc = ""
            self.status = "slave"
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
            self.cache = list()
            self.img_cache = list()
            self.picture_base = dict()

            self.nickname = ""
            self.fullname = ""
            self.origin = ""

            # Relays for game mechanics
            # courseid = specific course id girl is currently taking -- DEPRECATED: Training now uses flags
            # wagemod = Percentage to change wage payout
            self.wagemod = 100

            # Guard job relay:
            self.guard_relay = {
                "bar_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                "whore_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                "club_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
            }

            # Set relays that use the RelayProxy:
            for p in pytRelayProxyStore:
                p.reset(self)

            # Unhappy/Depressed counters:
            self.days_unhappy = 0
            self.days_depressed = 0

            # Trait assets
            self.init_traits = list() # List of traits to be enabled on game startup (should be deleted in init method)

            # Autocontrol of girls action (during the next day mostly)
            # TODO: Enable/Fix (to work with new skills/traits) this!
            # TODO: (Move to a separate instance???)
            self.autocontrol = {
            "Rest": True,
            "Tips": False,
            }

            # Auto-equip/buy:
            self.autobuy = False
            self.autoequip = False
            self.given_items = dict()

            # Actions:
            self.previousaction = ''
            self.sex_acts = {"vaginal": True, "anal": True, "oral": True, "bdsm": True}

            self.txt = list()
            self.fin = Finances(self)

        def init(self):
            # Normalize girls
            # Names:
            if not self.name:
                self.name = self.id
            if not self.fullname:
                self.fullname = self.name
            if not self.nickname:
                self.nickname = self.name

            # Class | Status normalization:
            # TODO: REMOVE CLASSES FROM HERE!
            if not self.traits.basetraits: # TODO: Just until all chars have proper jsons...
                pattern = create_traits_base(random.sample(self.CLASSES, 1).pop())
                for i in pattern:
                    self.traits.basetraits.add(i)
                    self.apply_trait(i)

            if self.status not in self.STATUS:
                if "Warrior" in self.occupations:
                    self.status = "free"
                else:
                    self.status = random.sample(self.STATUS, 1).pop()

            # Locations + Home + Status:
            # SM string --> object
            if self.location == "slavemarket":
                set_location(self, pytfall.sm)
            """
            # Slaves cannot be Warriors? # This is not reasonable... Slaves are just not allowed to do combat...
            # if self.status == "slave" and "Warrior" in self.occupations:
                # self.status = "free"
            """
            # Make sure all slaves that were not supplied custom locations string, find themselves in the SM
            if self.status == "slave" and (self.location == "city" or not self.location):
                set_location(self, pytfall.sm)

            # TODO: Fix city string to be an object.
            if self.status == "free" and self.location == pytfall.sm:
                set_location(self, "city")

            # Home settings:
            if self.status == "slave" and self.location == pytfall.sm:
                self.home = pytfall.sm
            if self.status == "free":
                if not self.home:
                    self.home = locations["City Apartment"]

            # Wagemod:
            if self.status == 'slave':
                self.wagemod = 0
            else:
                self.wagemod = 100

            # Battle and Magic skills:
            if not self.attack_skills:
                default = store.battle_skills["Fist Attack"]
                self.attack_skills.append(default)

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
            if "Warrior" in self.occupations and self not in hero.chars and self.arena_willing is not False:
                self.arena_willing = True

            # Settle auto-equip + auto-buy:
            if self.status != "slave":
                self.autobuy = True
                self.autoequip = True
            else:
                self.autoequip = True
            self.set_flag("day_since_shopping", 1)

            # add Character:
            self.say = Character(self.nickname, show_two_window=True, show_side_image=self, **self.say_style)

            self.say_screen_portrait = DynamicDisplayable(self._portrait)
            self.say_screen_portrait_overlay_mode = None

            super(Char, self).init()

        def get_availible_pics(self):
            """
            Determines (per category) what pictures are availible for the fixed events (like during the jobs).
            This is ran once during the game startup, should also run in the after_load label...
            Meant to decrease the amount of checks during the Next Day jobs. Should be activated in post Alpha code review.
            PS: It's better to simply add tags to a set instead of booleans as dict values.
            """
            # Lets start with the normal sex category:
            if self.has_image("sex"):
                self.picture_base["sex"] = dict(sex=True)
            else: self.picture_base["sex"] = dict(sex=False) # This is not really required as this should be  taken care of by the show method, maybe for the fututre.

            # Lets check for the more specific tags:
            if self.build_image_base["sex"]["sex"]:
                if self.has_image("sex", "doggy"):
                    self.picture_base["sex"]["doggy"] = True
                else:
                    self.picture_base["sex"]["doggy"] = False
                if self.has_image("sex", "missionary"):
                    self.picture_base["sex"]["missionary"] = True
                else:
                    self.picture_base["sex"]["missionary"] = False

        ### Girls fin methods
        def take_money(self, value, reason="Other"):
            return self.fin.take_money(value, reason)

        def add_money(self, value, reason="Other"):
            self.fin.add_money(value, reason)

        ### Displaying images
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
                return random.sample(imgset, 1)[0]
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
                     - normal = normal search behaviour, try all tags first, then first tag + one of each tags taken from the end of taglist
                     - any = will try to find an image with any of the tags chosen at random
                     - first_default = will use first tag as a default instead of a profile and only than switch to profile
                     - reduce = try all tags first, if that fails, pop the last tag and try without it. Repeat until no tags remain and fall back to profile or default.
                add_mood = Automatically adds proper mood tag. This will not work if a mood tag was specified on request OR this is set to False
            '''
            maxw, maxh = kwargs.get("resize", (None, None))
            cache = kwargs.get("cache", False)
            label_cache = kwargs.get("label_cache", False)
            exclude = kwargs.get("exclude", None)
            type = kwargs.get("type", "normal")
            default = kwargs.get("default", None)

            if "-" in tags[0]:
                _path = "/".join([self.path_to_imgfolder, tags[0]])
                if renpy.loadable(_path):
                    return ProportionalScale(_path, maxw, maxh)
                else:
                    return ProportionalScale("content/gfx/interface/images/no_image.png", maxw, maxh)

            add_mood = kwargs.get("add_mood", True) # Mood will never be checked in auto-mode when that is not sensible
            if set(tags).intersection(self.MOOD_TAGS):
                add_mood = False

            pure_tags = list(tags)
            tags = list(tags)
            if add_mood:
                mood_tag = self.get_mood_tag()
                tags.append(mood_tag)
            original_tags = tags[:]
            imgpath = ""

            if not any([maxw, maxh]):
                raise Exception("Width or Height were not provided to an Image when calling .show method!\n Character id: {}; Action: {}; Tags: {}; Last Label: {}.".format(self.id, str(self.action), ", ".join(tags), str(last_label)))

            if label_cache:
                for entry in self.img_cache:
                    if entry[0] == tags and entry[1] == last_label:
                        return ProportionalScale(entry[2], maxw, maxh)

            if cache:
                for entry in self.cache:
                    if entry[0] == tags:
                         return ProportionalScale(entry[1], maxw, maxh)

            # Select Image (set imgpath)
            if type in ["normal", "first_default", "reduce"]:
                if add_mood:
                    imgpath = self.select_image(self.id, *tags, exclude=exclude)
                if not imgpath:
                    imgpath = self.select_image(self.id, *pure_tags, exclude=exclude)

                if type in ["normal", "first_default"]:
                    if not imgpath and len(pure_tags) > 1:
                        tags = pure_tags[:]
                        main_tag = tags.pop(0)
                        while tags and not imgpath:
                            descriptor_tag = tags.pop()

                            # We will try mood tag on the last lookup as well, it can do no harm here:
                            if not imgpath and add_mood:
                                imgpath = self.select_image(main_tag, descriptor_tag, self.id, mood_tag, exclude=exclude)
                            if not imgpath:
                                imgpath = self.select_image(main_tag, descriptor_tag, self.id, exclude=exclude)
                        tags = original_tags[:]

                        if type == "first_default" and not imgpath: # In case we need to try first tag as default (instead of profile/default) and failed to find a path.
                            if add_mood:
                                imgpath = self.select_image(main_tag, self.id, mood_tag, exclude=exclude)
                            else:
                                imgpath = self.select_image(main_tag, self.id, exclude=exclude)

                elif type == "reduce":
                    if not imgpath:
                        tags = pure_tags[:]
                        while tags and not imgpath:
                            # if len(tags) == 1: # We will try mood tag on the last lookup as well, it can do no harm here: # Resulted in Exceptions bacause mood_tag is not set properly... removed for now.
                                # imgpath = self.select_image(self.id, tags[0], mood_tag, exclude=exclude)
                            if not imgpath:
                                imgpath = self.select_image(self.id, *tags, exclude=exclude)
                            tags.pop()

                        tags = original_tags[:]

            elif type == "any":
                tags = pure_tags[:]
                shuffle(tags)
                # Try with the mood first:
                if add_mood:
                    while tags and not imgpath:
                        tag = tags.pop()
                        imgpath = self.select_image(self.id, tag, mood_tag, exclude=exclude)
                    tags = original_tags[:]
                # Then try 'any' behavior without the mood:
                if not imgpath:
                    tags = pure_tags[:]
                    shuffle(tags)
                    while tags and not imgpath:
                        tag = tags.pop()
                        imgpath = self.select_image(self.id, tag, exclude=exclude)
                    tags = original_tags[:]

            if imgpath == "":
                msg = "could not find image with tags %s"
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
                    devlog.warning(str(msg % sorted(tags)))
                    return default

            # If we got here without being able to find an image ("profile" lookup failed is the only option):
            if "force_battle_sprite" in locals(): # New rule (Default Battle Sprites):
                imgpath = "content/gfx/images/" + "default_{}_battle_sprite.png".format(self.gender)
            elif not imgpath:
                devlog.warning(str("Total failure while looking for image with %s tags!!!" % tags))
                imgpath = "content/gfx/interface/images/no_image.png"
            else: # We have an image, time to convert it to full path.
                imgpath = "/".join([self.path_to_imgfolder, imgpath])

            if label_cache:
                self.img_cache.append([tags, last_label, imgpath])

            if cache:
                self.cache.append([tags, imgpath])

            return ProportionalScale(imgpath, maxw, maxh)

        def get_img_from_cache(self, label):
            """
            Returns imgpath!!! from cache based on the label provided.
            """
            for entry in self.img_cache:
                if entry[1] == label:
                    return entry[2]

            return ""

        def get_vnsprite(self, mood=("indifferent")):
            """
            Returns VN sprite based on characters height.
            Useful for random events that use NV sprites, heigth in unique events can be set manually.
            ***This is mirrored in galleries testmode, this method is not acutally used.
            """
            return self.show("vnsprite", resize=self.get_sprite_size())

        ### Next Day Methods
        def restore(self):
            # Called whenever character needs to have on of the main stats restored.
            l = list()
            if self.autoequip:
                if self.health < 60:
                    l.extend(self.auto_equip(["health"]))
                if self.vitality < 50:
                    l.extend(self.auto_equip(["vitality"]))
                if self.mp < 20:
                    l.extend(self.auto_equip(["mp"]))
                if self.joy < 40:
                    l.extend(self.auto_equip(["joy"]))
            if l:
                self.txt.append("She used: %s %s during the day!" % (", ".join(l), plural("item", len(l))))
            return l

        def auto_rest(self):
            # Auto-Rest should return a well rested girl back to work (or send them auto-resting!):
            txt = ""
            if self.vitality >= self.get_max("vitality") - 50 and self.health >= self.get_max('health') - 5:
                if self.action == 'AutoRest':
                    txt = "She is now both well rested and healthy, so she goes back to work as %s!" % self.previousaction
                    self.action = self.previousaction
                    # We'll reequip items on return to the job!
                    if self.autoequip:
                        equip_for(self, self.action)
                    self.previousaction = None  # This is redundant...
            elif all([self.action not in ["Rest", "AutoRest"], (self.health < 60 or self.vitality < 35), self.autocontrol['Rest']]):
                self.previousaction = self.action
                self.action = 'AutoRest'
                txt = "\n\n{color=[blue]}She's going to take few days off to recover her health and stamina!{/color}\n\n"
            return txt

        def next_day(self):
            if self in hero.chars:
                # Local vars
                img = 'profile'
                txt = ''
                flag_red = False
                flag_green = False

                # Settle wages:
                self.fin.settle_wage()

                # If escaped
                if self in pytfall.ra:
                    self.health -= randint(3, 5)
                    txt += "\n{color=[red]}This girl has escaped! Assign guards to search for her or do so yourself.{/color}\n\n"
                    flag_red = True

                else:
                    # Front text
                    if not self.flag("daysemployed"):
                        txt += "{} has started working for you today! ".format(self.fullname)

                    else:
                        txt += "{} has been working for you for {} {}. ".format(self.nickname, self.flag("daysemployed"), plural("day", self.flag("daysemployed")))

                    self.up_counter("daysemployed")

                    if self.location == "Streets" and self.status == "slave":
                        self.health -= randint(3, 5)
                        txt += "\n{color=[red]}This girl is a slave and curretly has no shelter! Find a place for her to live.{/color}\n\n"
                        flag_red = True

                    elif self.location == "Own Dwelling":
                        flag_red = True
                        txt += "\nShe is taking a day off on your pay. She may manage to gain some skills and a bit of experience but it's not the right way to handle your business.\n\n"

                        for stat in self.STATS: # --- Resources hungry?
                            if stat != "luck":
                                if dice(7):
                                    self.mod_stat(stat, 1)

                        self.exp += self.adjust_exp(randint(10, 50))
                        self.health += randint(1, 5)
                        self.vitality += randint(5, 50)
                        self.mp += randint(1, 7)

                    elif self.action == "Exploring":
                        txt += "\n{color=[green]}She is currently on the exploration run!{/color}\n"

                    else:
                        self.health += randint(1, 3)
                        self.vitality += randint(5, 10)
                        self.mp += randint(1, 3)

                    # Finances:
                    # Upkeep:
                    if in_training_location(self):
                        txt += "Upkeep is included in price of the class your girl's taking. \n"

                    elif self.action == "Exploring":
                        pass

                    else:
                        amount = self.fin.get_upkeep()

                        if amount < 0:
                            txt += "She actually managed to save you some money ({color=[gold]}%d Gold{/color}) instead of requiring upkeep! Very convenient! \n" % (-amount)
                            hero.add_money(-amount, reason="Girls Upkeep")

                        elif hero.take_money(amount, reason="Girls Upkeep"):
                            self.fin.log_cost(amount, "Upkeep")

                            if hasattr(self.location, "fin"):
                                self.location.fin.log_work_expense(amount, "Girls Upkeep")

                            txt += "You paid {color=[gold]}%d Gold{/color} for her upkeep. \n" % amount

                        else:
                            if self.status != "slave":
                                self.joy -= randint(3, 5)
                                self.disposition -= randint(5, 10)
                                txt += "\nYou failed to pay her upkeep, she's a bit cross with your because of that... \n"

                            else:
                                self.joy -= 20
                                self.disposition -= 50
                                self.health -= 10
                                self.vitality -= 100
                                txt += "\nYou've failed to provide even the most basic needs for your slave. This will end badly... \n"

                    # Wages and tips:
                    if self.status != 'slave':
                        wage = self.fin.expects_wage()
                        got_paid = self.fin.daily_income_log["private"].get("Wages", 0) + self.fin.daily_income_log["private"].get("Arena", 0)
                        income = sum(val for val in self.fin.daily_income_log["work"].values())
                        tips = sum(val for val in self.fin.daily_income_log["tips"].values())

                        # Wages:
                        if self.fin.wage_conditions():
                            txt += choice(["She expects to be compensated for her services ( %d Gold). "%wage, "She expects to be payed a wage of %d Gold. "%wage])

                            if got_paid == wage:
                                txt += "And she got exactly that in wages! "
                                img = "profile"

                            elif got_paid > wage:
                                txt += choice(["You've payed her more than that (%d Gold)! "%got_paid, "She got %d Gold for her services. "%got_paid])
                                img = self.show("profile", "happy", resize=(500, 600))

                            elif got_paid < wage:
                                txt += choice(["She has received less than expected... (%d Gold) You should really pay your girls a fair wage if you expect them to be happy and loyal."%got_paid,
                                               "She got less than that in wages! (%d Gold)"%got_paid])
                                img = self.show("profile", "angry", resize=(500, 600))
                                self.disposition -= int(round((wage - got_paid)*0.1))
                                self.joy -= int(round((wage - got_paid)*0.05))

                            txt += "\n"

                            # Tips:
                            if tips:
                                txt += choice(["Total tips earned: %d Gold. " % tips, "%s got %d Gold in tips. " % (self.nickname, tips)])

                                if self.autocontrol["Tips"]:
                                    txt += choice(["As per agreement, your girl gets to keep all her tips! This is a very good motivator. ", "She's happy to keep it. "])
                                    self.add_money(tips, reason="Tips")
                                    self.fin.log_cost(tips, "Tips")
                                    factor = float(tips) / wage

                                    self.disposition += int(round(factor * 5))
                                    self.joy += int(round(factor * 2))

                                    if got_paid < wage and got_paid + tips >= wage:
                                        txt += "That made up for the difference between the wage she expected and what she's received, so you can expect her not to be cross with you. "
                                        # Recover from disposition/joy hits from paying to little:
                                        self.disposition += int(round((wage - got_paid)*0.1))
                                        self.joy += int(round((wage - got_paid)*0.05))

                                else:
                                    txt += choice(["You take all of her tips for yourself. ", "You keep all of it. "])
                                    hero.add_money(tips, reason="Girls Tips")

                    else:
                        wage = self.fin.expects_wage()
                        got_paid = self.fin.daily_income_log["private"].get("Wages", 0)
                        income = sum(val for val in self.fin.daily_income_log["work"].values())
                        tips = sum(val for val in self.fin.daily_income_log["tips"].values())

                        # Wages:
                        if self.fin.wage_conditions():
                            txt += choice(["Being a slave, she doesn't expect to get paid. ", "Slaves don't get paid. "])

                            if got_paid:
                                txt += "Yet, you've paid her and she's very grateful! "
                                img = self.show("profile", "happy", resize=(500, 600))

                                factor = float(got_paid) / wage
                                self.disposition += int(round(factor * 10))
                                self.joy += int(round(factor * 3))

                            txt += "\n"

                            # Tips:
                            if tips:
                                txt += choice(["Total tips earned: %d Gold! " % tips, "%s got %d Gold in tips! " % (self.nickname, tips)])

                                if self.autocontrol["Tips"]:
                                    txt += choice(["As per agreement, your girl gets to keep all her tips! This is a very good motivator. ", "She's happy to keep it. "])
                                    self.add_money(tips, reason="Tips")
                                    factor = float(tips) / wage

                                    self.disposition += int(round(factor * 5))
                                    self.joy += int(round(factor * 2))

                                else:
                                    txt += choice(["You take all of her tips for yourself. ", "You keep all of it. "])
                                    hero.add_money(tips, reason="Girls Tips")

                    # ----------------------------------------------------------------->

                    # The bit from here on will be disabled during exploration and other multi-day activities:

                    # Training with NPCs ---------------------------------------------->
                    if not self.action == "Exploring":

                        if self.flag("train_with_witch"):
                            if self.get_free_ap():
                                if hero.take_money(self.get_training_price(), "Training"):
                                    self.auto_training("train_with_witch")
                                    self.reservedAP += 1
                                    txt += "\nSuccessfully completed scheduled training with Abby the Witch!"

                                else:
                                    txt +=  "\nNot enought funds to train with Abby the Witch. Auto-Training will be disabled!"
                                    self.del_flag("train_with_witch")

                            else:
                                txt += "\nNot enough AP left in reserve to train with Abby the Witch. Auto-Training will not be disabled ({color=[red]}This character will start next day with 0 AP{/color})!"

                        if self.flag("train_with_aine"):
                            if self.get_free_ap():
                                if hero.take_money(self.get_training_price(), "Training"):
                                    self.auto_training("train_with_aine")
                                    self.reservedAP += 1
                                    txt += "\nSuccessfully completed scheduled training with Aine!"

                                else:
                                    txt +=  "\nNot enought funds to train with Aine. Auto-Training will be disabled!"
                                    self.del_flag("train_with_aine")

                            else:
                                txt += "\nNot enough AP left in reserve to train with Aine. Auto-Training will not be disabled ({color=[red]}This character will start next day with 0 AP{/color})!"

                        if self.flag("train_with_xeona"):
                            if self.get_free_ap():
                                if hero.take_money(self.get_training_price(), "Training"):
                                    self.auto_training("train_with_xeona")
                                    self.reservedAP += 1
                                    txt += "\nSuccessfully completed scheduled combat training with Xeona!"

                                else:
                                    txt +=  "\nNot enought funds to train with Xeona. Auto-Training will be disabled!"
                                    self.del_flag("train_with_xeona")

                            else:
                                txt += "\nNot enough AP left in reserve to train with Xeona. Auto-Training will not be disabled ({color=[red]}This character will start next day with 0 AP{/color})!"

                        # Shopping (For now will not cost AP):
                        if all([self.action in [None, "AutoRest", "Rest"], self.autobuy, self.flag("day_since_shopping") > 5, self.gold > 1000, self.status != "slave"]):
                            self.set_flag("day_since_shopping", 1)

                            txt += choice(["\n\n%s decided to go on a shopping tour :)\n" % self.nickname,
                                           "\n\n%s went to town to relax, take her mind of things and maybe even do some shopping!\n" % self.nickname])

                            result = self.auto_buy(amount=randint(3, 7))

                            if result:
                                txt += choice(["{color=[green]}She bought {color=[blue]}%s %s{/color} for herself. This brightend her mood a bit!{/color}\n\n"%(", ".join(result), plural("item",len(result))),
                                               "{color=[green]}She got her hands on {color=[blue]}%s %s{/color}! She's definetly in better mood because of that!{/color}\n\n"%(", ".join(result),
                                                                                                                                                                               plural("item", len(result)))])

                                flag_green = True
                                self.joy += 5 * len(result)

                            else:
                                txt += choice(["But she ended up not doing much else than windowshopping...\n\n", "But she could not find what she was looking for...\n\n"])

                        # --------------------------------->>>

                        self.restore()
                        self.auto_rest()

                        # Unhappiness and related:
                        if self.joy <= 30:
                            txt += "\n\nThis girl is unhappy :( "
                            self.img = self.show("profile", "sad", resize=(500, 600))
                            self.days_unhappy += 1

                        else:
                            if self.days_unhappy - 1 >= 0:
                                self.days_unhappy -= 1

                        if self.days_unhappy > 7 and self.status != "slave":
                            txt += "{color=[red]}She has left your employment cause you do not give a rats ass about how she feels!{/color}"
                            flag_red = True
                            hero.remove_char(self)
                            self.location = "city"

                        if self.disposition < -500:
                            if self.status != "slave":
                                txt += "{color=[red]}She has left your employment cause she no longer trusts or respects you!{/color}"
                                flag_red = True
                                self.img = self.show("profile", "sad", resize=(500, 600))
                                hero.remove_char(self)
                                self.location = "city"

                            else:
                                if self.days_unhappy > 7:
                                    if dice(50):
                                        txt += "\n\n{color=[red]}Took her own life because she could no longer live as your slave!{/color}"
                                        self.img = self.show("profile", "sad", resize=(500, 600))
                                        flag_red = True
                                        self.health = 0

                                    else:
                                        txt += "\n\n{color=[red]}Tried to take her own life because she could no longer live as your slave!{/color}"
                                        self.img = self.show("profile", "sad", resize=(500, 600))
                                        flag_red = True
                                        self.health = 1

                # Effects
                if self.effects['Poisoned']['active']:
                    txt += "\n{color=[red]}This girl is suffering from the effects of Poison!{/color}\n"
                    flag_red = True

                if all([not self.autobuy, self.status != "slave", self.disposition < 950]):
                    self.autobuy = True
                    txt += "She will go shopping whenever it may please here from now on!\n"

                if all([self.status != "slave", self.disposition < 850, not self.autoequip]):
                    self.autoequip = True
                    txt += "She will be handling her own equipment from now on!\n"

                # Here we change girl mod from local stat gathering to total daily change:
                girlmod = dict()
                for stat in self.stats.log:
                    if stat == "exp": girlmod[stat] = self.exp - self.stats.log[stat]
                    elif stat == "level": girlmod[stat] = self.level - self.stats.log[stat]
                    else: girlmod[stat] = self.stats[stat] - self.stats.log[stat]

                # Prolly a good idea to throw a red flag if she is not doing anything:
                # I've added another check to make sure this doesn't happen if a girl is in FG as there is always something to do there:
                if not self.action:
                    flag_red = True
                    txt += "\n\n  {color=[red]}Please note that she is not really doing anything productive!{/color}\n"

                # TODO:
                # This is temporary code, better and more reasonable system is needed, especially if we want different characters to befriend each other.
                # For now, Girls will simply remove MC from their sets:
                if self.disposition < -100 and hero in self.friends:
                    txt += "\n {} is no longer friends with you...".format(self.nickname)
                    end_friends(self, hero)
                if self.disposition < -500 and hero in self.lovers:
                    txt += "\n {} and you are no longer lovers...".format(self.nickname)
                    end_lovers(self, hero)

                txt += "{color=[green]}\n\n%s{/color}" % "\n".join(self.txt)

                # Create the event:
                evt = NDEvent()
                evt.red_flag = flag_red
                evt.charmod = girlmod
                evt.type = 'girlndreport'
                evt.char = self
                evt.img = img
                evt.txt = txt
                NextDayEvents.append(evt)

                # Finances related:
                self.fin.next_day()

                # Resets and Counters:
                self.restore_ap()
                self.reservedAP = 0
                self.item_counter()
                self.txt = list()
                self.img_cache = list()
                self.cache = list()
                self.set_flag("day_since_shopping", self.flag("day_since_shopping") + 1)

                self.effects['Food Poisoning']['activation_count'] = 0
                self.guard_relay = {
                                    "bar_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                    "whore_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                    "club_event": {"count": 0, "helped": list(), "stats": dict(), "won": 0, "lost": 0},
                                    }

                # Reset relays that use the RelayProxy.
                for p in pytRelayProxyStore:
                    p.reset(self)

                # And Finally, we run the parent next_day() method that should hold things that are native to all of it's children!
                super(Char, self).next_day()
            else:
                super(Char, self).next_day()


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

            self.gender = gender
            self.caste = caste
            self.rank = ilists.clientCastes.index(caste)
            self.regular = False # Regular clients do not get removed from building lists as those are updated.

            # Traits activation:
            if dice(2):
                self.apply_trait(traits['Aggressive'])

            # self.seenstrip = False  # Seen striptease at least once
            # self.stripsatisfaction = 0  # Range from 0 to 100, extra bonus of goes above

            # self.traitmatched = False  # Sets to true if checks on next day to avoid another loop during the job.
            # self.favtraits = set()
            # self.favgirls = set()
            # self.favacts = set()
            # Alex, we should come up with a good way to set portrait depending on caste
            self.portrait = "" # path to portrait
            self.questpic = "" # path to picture used in quests
            self.act = ""
            self.pronoun = ""

            # Should we use money? @ presently not...
            self.cash = 0 # carried cash
            self.cashtospend = 0 # cash the customer is willing to spend

            # class battle stats
            # self.attack = randint(5, 40)
            # self.magic = randint(5, 40)
            # self.defence = randint(5, 40)
            # self.mp = randint(5, 40)
            # self.agility = randint(5, 40)

            # if "Aggressive" in self.traits:
                # self.attack += randint(5,20)
                # self.defence += randint(5,20)
                # self.magic += randint(5,20)
                # self.agility += randint(5,20)
                # self.mp += randint(5,20)

            # determine act and pronoun
            if self.gender == 'male':
                self.act = choice(["sex", "anal", "blowjob"])
                self.pronoun = 'He'

            elif self.gender == 'female':
                # self.act = choice(pytWhoringActs.female.keys())
                self.act = "lesbian"
                self.pronoun = 'She'

            # @Review: Temporary disabled (until we are ready to do complex client modeling, all clients assumed to have infinite money)
            # if caste in ('Beggar'):
                # self.cash = randint(30, 50)
                # self.fame = randint(0, 10)

                # self.attack += randint(5, 10)
                # self.magic += randint(5, 10)
                # self.defence += randint(5, 10)
                # self.mp += randint(5, 10)
                # self.agility += randint(5, 10)
            # elif caste in ('Peasant', 'Nomad'):
                # self.cash = randint(50, 80)
                # self.fame = randint(10, 30)

                # self.attack += randint(5, 15)
                # self.magic += randint(5, 15)
                # self.defence += randint(5, 15)
                # self.mp += randint(5, 15)
                # self.agility += randint(5, 15)
            # elif caste in ('Merchant'):
                # self.cash = randint(80, 120)
                # self.fame = randint(25, 65)

                # self.attack += randint(10, 15)
                # self.magic += randint(10, 15)
                # self.defence += randint(10, 15)
                # self.mp += randint(10, 15)
                # self.agility += randint(10, 15)
            # elif caste in ('Wealthy Merchant', 'Clerk'):
                # self.cash = randint(120, 150)
                # self.fame = randint(65, 100)

                # self.attack += randint(10, 20)
                # self.magic += randint(10, 20)
                # self.defence += randint(10, 20)
                # self.mp += randint(10, 20)
                # self.agility += randint(10, 20)
            # elif caste in ('Noble'):
                # self.cash = randint(150, 200)
                # self.fame = randint(95, 150)

                # self.attack += randint(15, 30)
                # self.magic += randint(15, 30)
                # self.defence += randint(15, 30)
                # self.mp += randint(15, 30)
                # self.agility += randint(15, 30)
            # elif caste in ('Royal'):
                # self.cash = randint(200, 250)
                # self.fame = randint(120, 200)

                # self.attack += randint(25, 40)
                # self.magic += randint(25, 40)
                # self.defence += randint(25, 40)
                # self.mp += randint(25, 40)
                # self.agility += randint(25, 40)
            # else:
                # self.cash = 100
                # notify(u">>Warning<< Unknown caste: '%s'" % caste)
            # determine cash the customer is willing to spend
            # poor customers should be willing to spend all of it, or not go
            # into a brothel in the first place
            # self.cashtospend = min((self.cash/2 + 30), self.cash)

        # Want to see striptease method:
        def wts_strip(self, girl):
            # Just in the mood for striptease / Overlapping traits / Fame:
            if self.wtsstrip or self.favtraits.intersection(girl.traits) or girl.fame >= self.fame:
                # self.seenstrip = True
                return True
            else:
                return False


    class NPC(Char):
        """There is no point in this other than an ability to check for instances of NPCs
        """
        def __init__(self):
            super(NPC, self).__init__()


    ### ==>> Rest:
    class Trait(_object):
        def __init__(self):
            self.desc = ''
            self.icon = None
            self.hidden = False
            self.mod = dict() # To be removed!
            self.mod_stats = dict()
            self.mod_skills = dict()
            self.max = dict()
            self.min = dict()
            self.blocks = list()
            self.effects = list()

            # Occupations related:
            self.occupations = list() # So far I came up with SIW (Sex Industry worker), Server, Warrior...
            self.higher_tiers = list() # Required higher tier basetraits to enable this trait.

            self.sex = "unisex" # Untill we set this up in traits: this should be "unisex" by default.

            # Types:
            self.type = "" # Specific type if specified.
            self.basetrait = False
            self.personality = False
            self.race = False
            self.breasts = False
            self.body = False
            self.elemental = False

            self.mod_ap = 0 # Will only work on body traits!

            self.mob_only = False
            self.character_trait = False
            self.sexual = False
            self.client = False

            # Elemental:
            self.font_color = None
            self.resist = list()
            self.el_name = ""
            self.el_absorbs = dict() # Pure ratio, NOT a modificator to a multiplier like for dicts below.
            self.el_damage = dict()
            self.el_defence = dict()
            self.el_special = dict()

            # Weaponfocus:
            self.we_damage = dict()
            self.we_defence = dict()
            self.we_special = dict()

            # Base mods on init:
            self.init_mod = dict() # Mod value setting
            self.init_lvlmax = dict() # Mod value setting
            self.init_max = dict() # Mod value setting
            self.init_skills = dict() # {skill: [actions, training]}

            # Special BE Fields:
            # self.evasion_bonus = () # Bonuses in traits work differently from item bonuses, a tuple of (min_value, max_value, max_value_level) is expected (as a value in dict below) instead!
            # self.ch_multiplier = 0 # Critical hit multi...
            # self.damage_multiplier = 0

            # self.defence_bonus = {} # Delivery! Not damage types!
            # self.defence_multiplier = {}
            # self.delivery_bonus = {} Expects a k/v pair of type: multiplier This is direct bonus added to attack power.
            # self.delivery_multiplier = {}

            self.leveling_stats = dict() # {stat: [lvl_max, max **as mod values]}

        def __str__(self):
            return str(self.id)


    class Team(_object):
        def __init__(self, name="", implicit=None, free=False, max_size=3):
            if not implicit:
                implicit = list()
            self.name = name
            self.implicit = implicit
            self.max_size = max_size
            self._members = list()
            self._leader = None
            self.free = free # Free teams do not have any implicit members.

            # BE Assests:
            self.position = None # BE will set it to "r" or "l" short for left/right on the screen.

            if self.implicit:
                for member in self.implicit:
                    self.add(member)

        def __len__(self):
            return len(self._members)

        def __iter__(self):
            return iter(self._members)

        def __getitem__(self, index):
            return self._members[index]

        def __nonzero__(self):
            return bool(self._members)

        @property
        def members(self):
            return self._members

        @property
        def leader(self):
            try:
                return self.members[0]
            except:
                return self._leader

        def add(self, member):
            if member in self:
                notify("Impossible to join the same team twice")

            if len(self._members) >= self.max_size:
                notify("This team cannot have more than %d teammembers!"%self.max_size)
            else:
                if not self.free and not self.leader:
                    self._leader = member
                    if member not in self.implicit:
                        self.implicit.append(member)
                    self._members.append(member)
                else:
                    self._members.append(member)

        def remove(self, member):
            if member in self.implicit or member not in self._members:
                notify("%s is not a member of this team or an implicit member of this team!"%member.name)
            else:
                self._members.remove(member)

        def set_leader(self, member):
            if member not in self._members:
                notify("%s is not a member of this team!"%member.name)
                return
            if self.leader:
                self.implicit.remove(self.leader)
            self._leader = member
            self.implicit.insert(0, member)

        def get_level(self):
            """
            Returns an average level of the team as an integer.
            """
            av_level = 0
            for member in self._members:
                av_level += member.level
            return int(math.ceil(av_level/len(self._members)))

        def get_rep(self):
            """
            Returns average of arena reputation of a team as an interger.
            """
            arena_rep = 0
            for member in self._members:
                arena_rep += member.arena_rep
            return int(math.ceil(arena_rep/len(self._members)))

        # BE Related:
        def reset_controller(self):
            # Resets combat controller
            for m in self.members:
                m.controller = "player"
