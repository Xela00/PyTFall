init python:
    # OLD CLASSES!
    # Fighters Guild Jobs =========================================>>>
    # Note that simpler jobs are part of the FG classes next day method itself!

    # Temporary I'll Put Exploration code here:
    def launch_exploration_run(team, area, guild):
        #### NO LONGER IN USE ####
        # Making sure that the team can explore the area.
        # Ask if player wants to send the team exploring:
        # I think this needs to be moved somewhere... it's a good fit for the class:
        if not renpy.call_screen("yesno_prompt",
                                 message="Are you sure that you wish to send %s exploring %s?" % (team.name, area.name),
                                 yes_action=Return(True),
                                 no_action=Return(False)):
            return

        for char in team:
            char.action = "Exploring" # We effectively remove char from the game so this is prolly ok.
            char.set_flag("loc_backup", char.location)
            if char in hero.team:
                hero.team.remove(char)

            # TODO: Remove char from every possible team setup in any of the buildings?!?
            for t in guild.teams:
                if t != team:
                    for c in t:
                        if c == char:
                            t.remove(char)

    # This all should prolly be adapted to serve SimPy soon.
    class FG_Rest(_object):
        """Resting in the Fighting Guild.
        """
        def __init__(self, girl):
            """
            Creates a new FG_Rest.
            girl = The girl who the job is for.
            """
            self.txt = list()
            self.girl = girl
            self.img = None
            self.girlmod = {
                'health': 0,
                'vitality': 0,
                'disposition': 0,
                'mp': 0,
                'reputation': 0,
                "charisma": 0,
                'constitution': 0,
                'intelligence': 0,
                "strip": 0,
                "joy": 0,
                "service": 0}

            if fg.upgrades["healing onsen"][0]:
                while self.girl.AP and not all([(self.girl.vitality + self.girlmod['vitality'] >= self.girl.get_max("vitality") - 50),
                                                (self.girl.health + self.girlmod['health'] >= self.girl.get_max('health') - 5)]):

                    self.girlmod['health'] += randint(5, 8)
                    self.girlmod['vitality'] += randint(55, 70)
                    self.girlmod['mp'] += randint(3, 6)
                    self.girlmod['joy'] += randint(3, 6)
                    self.girl.AP -= 1

                self.img = Fixed(ProportionalScale(fg.upgrades["healing onsen"][1], 740, 685, align=(0.5, 0.5)),
                                 HBox(self.girl.show("onsen", "rest", exclude=["sex"], type="any", resize=(300, 250)), align=(0.5, 1.0)),
                                 xysize=(740, 685))

                self.img = self.girl.show("onsen", "rest", exclude=["sex"], type="any", resize=(740, 685))
                self.txt.append("%s spent some time resting and recovering in the healing onsens! " % self.girl.name)

            else:
                while self.girl.AP and not all([(self.girl.vitality + self.girlmod['vitality'] >= self.girl.get_max("vitality") - 50),
                                                (self.girl.health + self.girlmod['health'] >= self.girl.get_max('health') - 5)]):

                    self.girlmod['health'] += randint(2, 3)
                    self.girlmod['vitality'] += randint(35, 40)
                    self.girlmod['mp'] += randint(1, 3)
                    self.girlmod['joy'] += randint(1, 2)
                    self.girl.AP -= 1

                self.img = self.girl.show("rest", resize=(740, 685))
                self.txt.append("%s rested for the day! " % self.girl.name)

            # If girl is down with cold
            if self.girl.effects['Down with Cold']['active']:
                self.girl.effects['Down with Cold']['count'] += 2
                self.txt.append("Allowing her to rest is a really good idea considering that she has a cold!\n")

            if self.girl.effects['Food Poisoning']['active']:
                self.girl.effects['Food Poisoning']['count'] += 2
                self.txt.append("Allowing her to rest is a really good idea considering that she has food poisoning!\n")

            if fg.upgrades["bar"] and list(g for g in fg.get_girls() if g.action == "BarGirl") and dice(50) and self.girl.health > 50:
                self.txt.append(choice(["She spent some time relaxing in the bar afterwards.", "Some rest in the bar afterwards really brightend her mood!"]))
                self.girlmod['vitality'] += 10
                self.girlmod['joy'] += randrange(4)
                self.girlmod['disposition'] += randrange(3)
                self.girlmod['health'] += randrange(2)

            if self.girl.previousaction in fg.ACTIONS:
                if (self.girl.vitality >= self.girl.get_max("vitality") - 50) and (self.girl.health >= self.girl.get_max('health') - 5):
                    self.txt.append("\n\nShe is now both well rested and healthy, so she goes back to work as %s!" % self.girl.previousaction)
                    self.girl.action = self.girl.previousaction
                    self.girl.previousaction = None  # This is redundant but just in case
                    if self.girl.autoequip:
                        equip_for(self.girl, self.girl.action)

            # Finishing up:
            for stat in self.girlmod:
                if stat == "exp":
                    self.girlmod[stat] = char.adjust_exp(self.girlmod[stat])
                    self.girl.exp += self.girlmod[stat]

                else:
                    self.girl.mod_stat(stat, self.girlmod[stat])

            evt = NDEvent()
            # evt.red_flag = self.flag_red
            # evt.green_flag = self.flag_green
            evt.charmod = self.girlmod
            evt.type = 'fg_job'
            evt.char = self.girl
            self.loc = fg
            evt.img = self.img
            evt.txt = "".join(self.txt)
            NextDayEvents.append(evt)


    class FG_CombatTraining(_object):
        """
        The class that solves combat training.
        (All FG jobs should be functions...)
        """
        def __init__(self, girl):
            """
            Creates a new FG_CombatTraining.
            girl = The girl who the job is for.
            """
            self.girlmod = dict()
            self.txt = list()
            self.girl = girl
            self.img = None

            if fg.upgrades["sparring quarters"][0]:
                self.txt.append(choice(["%s Report:\n\n" % self.girl.name, "%s spent the day training:\n\n" % self.girl.name]))

                guardlist = list(girl for girl in fg.get_girls() if girl.action == "Training")
                guards = len(guardlist)

                if guards > 0:
                    if guards >= 3:
                        self.txt.append(", ".join(girl.name for girl in guardlist[:guards-1]))
                        self.txt.append(" and %s "%guardlist[guards-1].nickname)
                        self.txt.append("spent the day dualing eachother in Sparring Quarters. \n")

                        while self.girl.AP > 0:
                            self.girlmod['attack'] = self.girlmod.get('attack', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['defence'] = self.girlmod.get('defence', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['magic'] = self.girlmod.get('magic', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['joy'] = self.girlmod.get('joy', 0) + choice([0, 1, 2, 3])
                            self.girlmod['vitality'] = self.girlmod.get('vitality', 0) - randint(15, 20)
                            self.girl.AP -=  1

                        self.girlmod['exp'] = self.girlmod.get('exp', 0) + self.girl.AP * randint(8, 12) + 5 * (guards-1)

                        if guards <= 9:
                            args = list(g.show("battle", resize=(233, 200)) for g in guardlist)

                        else:
                            args = list(g.show("battle", resize=(115, 100)) for g in guardlist)

                        self.img = Fixed(ProportionalScale(fg.upgrades["sparring quarters"][1], 740, 685, align=(0.5, 1.0)),
                                         HBox(*args, spacing=10, align=(0, 0), box_wrap=True, xysize=(740, 685)),
                                         xysize=(740, 685))

                    elif guards == 2:
                        self.txt.append("%s and %s spent time dualing eachother! \n"%(guardlist[0].name, guardlist[1].name))

                        while self.girl.AP > 0:
                            self.girlmod['attack'] = self.girlmod.get('attack', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['defence'] = self.girlmod.get('defence', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['magic'] = self.girlmod.get('magic', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['joy'] = self.girlmod.get('joy', 0) + choice([0, 1, 2, 3])
                            self.girlmod['vitality'] = self.girlmod.get('vitality', 0) - randint(15, 20)
                            self.girl.AP -=  1

                        self.girlmod['exp'] = self.girlmod.get('exp', 0) + self.girl.AP * randint(8, 12) + 5

                        self.img = Fixed(ProportionalScale(fg.upgrades["sparring quarters"][1], 820, 705, align=(0.5, 1.0)),
                                         HBox(*[g.show("battle", resize=(200, 200)) for g in guardlist], spacing=10, align=(0.5, 0)),
                                         xysize=(820, 705))

                    elif guards == 1:
                        self.txt.append("%s had the whole Sparring Quarters to herself! \n"%(guardlist[0].name))

                        while self.girl.AP > 0:
                            self.girlmod['attack'] = self.girlmod.get('attack', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['defence'] = self.girlmod.get('defence', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['magic'] = self.girlmod.get('magic', 0) + choice([0, 0, 0, 0, 1, guards])
                            self.girlmod['joy'] = self.girlmod.get('joy', 0) + choice([0, 1, 2, 3])
                            self.girlmod['vitality'] = self.girlmod.get('vitality', 0) - randint(15, 20)
                            self.girl.AP -=  1

                        self.girlmod['exp'] = self.girlmod.get('exp', 0) + self.girl.AP * randint(8, 12)

                        self.img = Fixed(ProportionalScale(fg.upgrades["sparring quarters"][1], 740, 685, align=(0.5, 1.0)),
                                         HBox(*[g.show("battle", resize=(200, 200)) for g in guardlist], spacing=10, align=(0.5, 0)),
                                         xysize=(740, 685))

                else:
                    # Weird Stuff:
                    raise Exception, "Training job called without any training girls! (Fighters Guild)"

            else:
                self.txt.append("%s did some rudamentory training. \n"  % self.girl.name)

                self.girlmod['attack'] = self.girlmod.get('attack', 0) + choice([0, 0, 0, 0, 1])
                self.girlmod['defence'] = self.girlmod.get('defence', 0) + choice([0, 0, 0, 0, 1])
                self.girlmod['magic'] = self.girlmod.get('magic', 0) + choice([0, 0, 0, 0, 1])
                self.girlmod['joy'] = self.girlmod.get('joy', 0) + choice([0, 1, 1, 1])
                self.girlmod['exp'] = self.girlmod.get('exp', 0) +  randint(15, 25)
                self.girlmod['vitality'] = self.girlmod.get('vitality', 0) - randint(15, 20)
                self.girl.AP = 0

                self.img =self.girl.show("battle", resize=(740, 685))

            if fg.upgrades["bar"] and list(g for g in fg.get_girls() if g.action == "BarGirl") and dice(50):
                self.txt.append(choice(["She spent some time relaxing in the bar afterwards.", "Some rest in the bar afterwards really brightend her mood!"]))

                self.girlmod['vitality'] = self.girlmod.get('vitality', 0) + 10
                self.girlmod['joy'] = self.girlmod.get('joy', 0) + randrange(4)
                self.girlmod['disposition'] = self.girlmod.get('disposition', 0) + randrange(3)
                self.girlmod['health'] = self.girlmod.get('health', 0) + randrange(2)

            # Finishing up:
            for stat in self.girlmod:
                if stat == "exp":
                    self.girlmod[stat] = self.girl.adjust_exp(self.girlmod[stat])
                    self.girl.exp += self.girlmod[stat]

                else:
                    self.girl.mod_stat(stat, self.girlmod[stat])

            evt = NDEvent()
            evt.charmod = self.girlmod
            evt.type = 'fg_job'
            evt.char = self.girl
            self.loc = fg
            evt.img = self.img
            evt.txt = "".join(self.txt)
            NextDayEvents.append(evt)


    class FG_ExplorationJob(_object):
        """The class that solves exploration jobs.

        Doesn't inherit from Job class for being too unique for it's generalization.

        This sadly will have to be rewritten for SimPy almost completely :(        """
        def __init__(self, team, area):
            """
            Creates a new FG_ExplorationJob.
            team = The team that is exploring.
            area = The area that is being explored.
            """
            # Ask if player wants to send the team exploring:
            if not renpy.call_screen("yesno_prompt",
                                     message="Are you sure that you wish to send %s exploring?" % team.name,
                                     yes_action=Return(True),
                                     no_action=Return(False)):
                return

            for char in team:
                if char.action == "Exploring":
                    renpy.show_screen("message_screen", "Team Member: %s is already on exploration run!" % char.name)
                    return

            for char in team:
                char.action = "Exploring"
                char.set_flag("loc_backup", char.location)
                if char in hero.team:
                    hero.team.remove(char)

            # Shitty loops to remove characters from other exploration teams.
            for t in fg.teams:
                if t != team:
                    for char in team:
                        for c in t:
                            if c == char:
                                t.remove(char)

            self.area = deepcopy(area)
            self.team = team
            self.mobs = self.area.mobs
            self.cash = list()
            self.risk = self.area.risk
            self.cash_limit = self.area.cash_limit
            self.items_limit = self.area.items_limit
            self.items = list(item.id for item in items.values() if "Exploration" in item.locations and item.price < self.items_limit) # and "Exploration" in item.locations)
            self.found_items = list()
            self.travel_time = self.area.travel_time + 0
            self.hazard = self.area.hazard
            self.captured_girl = None

            self.day = 0
            self.days = self.area.days + 0

            self.unlocks = dict()
            for key in self.area.unlocks:
                self.unlocks[key] = 0

            self.flag_red = False
            self.flag_green = False
            self.stats = dict(attack=0,
                              defence=0,
                              agility=0,
                              magic=0,
                              exp=0
                              )

            self.txt = list()

            fg.exploring.append(self)
            renpy.show_screen("message_screen", "Team %s was sent out on %d days exploration run!" % (team.name, area.days))
            jump("fg_management")

        def start_day(self):
            """
            Sets up the day.
            """
            restore = False

            for char in self.team:
                if char.health < char.get_max("health")*0.5 or char.vitality < char.get_max("vitality")*0.5 or char.AP < 1:
                    restore = True
                    break

            if restore:
                for char in self.team:
                    char.health = char.get_max("health")
                    char.vitality = char.get_max("vitality")
                    char.mp = char.get_max("mp")

                self.txt.append("Day 0: \n\n")
                self.txt.append("The team rested in one of the frontier encampments prepearing for the run!")
                self.txt.append("\n\n")
                self.days += 1
                self.day += 1

                return True

            else:
                return False

        def next_day(self):
            """
            Solves next day logic.
            """
            # Check start:
            if not self.day:
                if self.start_day():
                    return

            if self.travel_time:
                if self.travel_time == self.area.travel_time:
                    self.txt.append(choice(["{color=[blue]}It took %s %s of travel time for expedition to get to/back from %s!\n{/color}"%(self.travel_time,
                                                                                                                                           plural("day", self.travel_time),
                                                                                                                                           self.area.id),
                                            "{color=[blue]}%s %s to travel to and back from %s!{/color}\n"%(self.travel_time,
                                                                                                            plural("day", self.travel_time),
                                                                                                            self.area.id)]))

                    self.days += self.travel_time + self.travel_time

                self.travel_time -= 1
                self.day += 1
                return

            self.day += 1
            if self.day == 1:
                self.txt.append("Exploring {i}%s{/e}:\n\n" % self.area.id)

            self.txt.append("\n\n{b}Day %d:{/b} \n" % self.day)
            # self.txt.append("Exploring 'Meow'\n")
            stop = False

            if self.hazard:
                self.txt.append("{color=[blue]}Hazardous area!{/color}\n")
                for char in self.team:
                    for stat in self.hazard:
                        char.mod_stat(stat, -self.hazard[stat])

            ap = sum(list(girl.AP for girl in self.team))

            items = list()
            attacked = False
            cash = 0
            mob_power = 0

            #Day 1 Risk 1 = 0.213, D 15 R 1 = 0.287, D 1 R 50 = 0.623, D 15 R 50 = 0.938, D 1 R 100 = 1.05, D 15 R 100 = 1.75
            risk_a_day_multiplicator = ((0.2 + (self.area.risk*0.008))*(1 + self.day*(0.025*(1+self.area.risk/100))))

            for i in xrange(ap):
                if not stop:
                    if self.items and dice(self.area.risk*0.2 + self.day + self.day + self.day):
                        items.append(choice(self.items))

                    # Second round of items for those specifically specified for this area:
                    for i in self.area.items:
                        if dice((self.area.items[i]*risk_a_day_multiplicator)):
                            items.append(i)
                            # break   #too hard to calculate chances for json with that

                    if dice(self.area.risk + self.day*2):
                        cash += randint(int(self.cash_limit/50*self.day), int(self.cash_limit/15*self.day))

                    #  =================================================>>>
                    # Girls capture (We break off exploration run in case of success):
                    if fg.capture_girls:
                        for g in self.area.girls:
                            if g in chars and dice(self.area.girls[g] + self.day*0.1) and g.location == "se":
                                self.captured_girl = chars[g]
                                stop = True
                                break

                            # TODO: g in rchars looks like broken code!
                            elif g in rchars and dice(self.area.girls[g] + self.day*0.1):
                                new_random_girl = build_rc()
                                self.captured_girl = new_random_girl
                                stop = True
                                break

                    if not attacked:
                        attacked = False
                        # Lets get some enemies:
                        mob = None

                        for key in self.mobs:
                            if dice(((self.mobs[key][0]*risk_a_day_multiplicator)/(ap/2))):
                                enemies = choice([self.mobs[key][2][0], self.mobs[key][2][1], self.mobs[key][2][2]])
                                mob = key
                                attacked = True
                                self.txt.append("The Party was attacked by ")
                                self.txt.append("%d %s" % (enemies, plural(mob, enemies)))
                                break

                        #ChW: testing the variant no mob found = no fight
                        # if not mob:
                            # mob = max(self.mobs.iteritems(), key=itemgetter(1))[0]
                            # self.area.known_mobs.add(mob)
                            # enemies = randint(1, self.mobs[key][2])
                            # self.txt.append("%d %s!" % (enemies, plural(mob, enemies)))

                        if attacked:
                            self.txt.append("\n")

                            # Object mobs and combat resolver:
                            mob = deepcopy(mobs[mob]) # Get the actual instance instead of a string!

                            for stat in ilists.battlestats:
                                stat_value = int(getattr(mob, stat) * min(self.mobs[mob.name][1][2], (self.mobs[mob.name][1][0] + int(round(self.mobs[mob.name][1][1] * self.day)))))
                                setattr(mob, stat, stat_value)
                                mob_power += stat_value

                            mob_power * enemies
                            ep = Team()

                            for i in range(enemies):
                                ep.add(mob)

                            result = s_conflict_resolver(self.team, ep, new_results=False)

                            if result[0] == "victory":
                                self.stats["attack"] += randrange(3)
                                self.stats["defence"] += randrange(3)
                                self.stats["agility"] += randrange(3)
                                self.stats["magic"] += randrange(3)
                                self.stats["exp"] += mob_power/10

                                self.txt.append("{color=[green]}Exploration Party beat the crap out of those damned mobs! :){/color}\n")

                                for member in self.team:
                                    damage = randint(3, 10)

                                    if member.health - damage <= 0:
                                        if self.risk > 75:
                                            self.txt.append("\n{color=[red]}%s has died during this skirmish!{/color}\n" % member.name)
                                            stop = True
                                            member.health -= damage

                                        else:
                                            self.txt.append("\n{color=[red]}%s nearly died during this skirmish... it's time for the party to fall back!{/color}\n")
                                            stop = True
                                            member.health = 1

                                    else:
                                        member.health -= damage

                                    member.mp -= randint(3, 7)

                            elif result[0] == "defeat":
                                self.stats["attack"] += randrange(2)
                                self.stats["defence"] += randrange(2)
                                self.stats["agility"] += randrange(2)
                                self.stats["magic"] += randrange(2)
                                self.stats["exp"] += mob_power/15

                                self.txt.append("{color=[red]}Exploration Party was defeated!{/color}\n")

                                for member in self.team:
                                    damage = randint(20, 30)

                                    if member.health - damage <= 0:
                                        if self.risk > 60:
                                            self.flag_red = True
                                            self.txt.append("\n{color=[red]}%s has died during this skirmish!{/color}\n" % member.name)
                                            stop = True
                                            member.health -= damage

                                        else:
                                            self.txt.append("\n{color=[red]}%s nearly died during this skirmish... it's time for the party to fall back!{/color}\n"%member.name)
                                            stop = True
                                            member.health = 1

                                    else:
                                        member.health -= damage

                                    member.mp -= randint(10, 17)

                            else: # (Overwhelming defeat)
                                self.stats["attack"] += randrange(2)
                                self.stats["defence"] += randrange(2)
                                self.stats["agility"] += randrange(2)
                                self.stats["magic"] += randrange(2)
                                self.stats["exp"] += mob_power/20

                                self.txt.append("{color=[red]}Exploration Party was destroyed by the monsters!{/color}\n")

                                for member in self.team:
                                    damage = randint(50, 100)

                                    if member.health - damage <= 0:
                                        if self.risk > 25:
                                            self.flag_red = True
                                            self.txt.append("\n{color=[red]}%s has died during this skirmish!{/color}\n" % member.name)
                                            stop = True
                                            member.health -= damage

                                        else:
                                            self.txt.append("\n{color=[red]}%s nearly died during this skirmish... it's time for the party to fall back!{/color}\n"%member.name)
                                            stop = True
                                            member.health = 1

                                    else:
                                        member.health -= damage

                                    member.mp -= randint(20, 37)

            if items and cash:
                self.txt.append("The team has found: %s %s" % (", ".join(items), plural("item", len(items))))
                self.found_items.extend(items)
                self.txt.append(" and {color=[gold]}%d Gold{/color} in loot" % cash)
                self.cash.append(cash)

            if cash and not items:
                self.txt.append("The team has found: {color=[gold]}%d Gold{/color} in loot" % cash)
                self.cash.append(cash)

            if items or cash:
                self.txt.append("!\n")

            if not items and not cash:
                self.txt.append("It was a quite day of exploration, nothing of interest happened...")

            self.stats["agility"] += randrange(2)
            self.stats["exp"] += randint(5, max(15, self.risk/4))

            invlist = list(g.inventory for g in self.team)
            random.shuffle(invlist)

            for g in self.team:
                l = list()

                if g.health < g.get_max("health")*0.5:
                    for inv in invlist:
                        l.extend(g.auto_equip(["health"], inv=inv))

                if g.vitality < g.get_max("vitality")*0.5:
                    for inv in invlist:
                        l.extend(g.auto_equip(["vitality"], inv=inv))

                if g.mp < g.get_max("mp")*0.5:
                    for inv in invlist:
                        l.extend(g.auto_equip(["mp"], inv=inv))

                if l:
                    self.txt.append("\n%s used: {color=[blue]}%s %s{/color} to recover!\n" % (g.nickname, ", ".join(l), plural("item", len(l))))

            if not stop and self.day == self.days:
                self.txt.append("\n\n {color=[green]}The party has finished their exploration run!{/color}")
                stop = True

            if not stop:
                for member in self.team:
                    if member.health <= (member.get_max("health") / 100.0 * (100 - self.risk)) or member.health < 15:
                        self.txt.append("\n{color=[blue]}Your party falls back to base due to risk factors!{/color}")
                        stop = True
                        break

            if stop:
                self.finish_exploring()

        def finish_exploring(self):
            """
            Finishes the exploring job.
            """
            # Create a dict of characters to enable im.Sepia (=dead)) when constructing the image.
            # False for alive and True for dead.
            characters = {c: False for c in self.team}
            dead = 0

            for char in self.team:
                if char.location != "After Life":
                    char.action = None
                    char.location = char.flag("loc_backup")
                    char.del_flag("loc_backup")

                    for stat in self.stats:
                        if stat == "exp":
                            self.stats[stat] = char.adjust_exp(self.stats[stat])
                            char.exp += self.stats[stat]
                        else:
                            char.mod_stat(stat, self.stats[stat])

                else:
                    characters[char] = True
                    dead = dead + 1

            # Handle the dead chars:
            skip_rewards = False

            if dead:
                if len(self.team) == dead:
                    self.txt.append("\n{color=[red]}The entire party was wiped out (Those poor girlz...)! This can't be good for your reputation (and you obviously not getting any rewards))!{/color}\n")
                    hero.reputation -= 30
                    skip_rewards = True

                else:
                    self.txt.append("\n{color=[red]}You get reputation penalty as %d of your girls never returned from the expedition!\n{/color}" % dead)
                    hero.reputation -= 7*dead

            if not skip_rewards:
                # Rewards + logging in global area
                cash = sum(self.cash)
                hero.add_money(cash, "Fighters Guild")
                fg.fin.log_logical_income(cash, "Fighters Guild")

                for item in self.items:
                    hero.inventory.append(items[item])

                self.cash = sum(self.cash)
                if self.captured_girl:
                    # We place the girl in slave pens (general jail of pytfall)
                    jail.add_prisoner(self.captured_girl, flag="SE_capture")
                    self.txt.append("{color=[green]}\nThe team has captured a girl, she's been sent to City Jail for 'safekeeping'!{/color}\n")

                area = fg_areas[self.area.id]
                area.known_items |= set(self.found_items)
                area.cash_earned += self.cash
                area.known_mobs |= self.area.known_mobs

                for key in area.unlocks.keys():
                    area.unlocks[key] += randrange(1, int(max(self.day, (self.day * self.risk/25), 2)))

                    if dice(area.unlocks[key]):
                        if key in fg_areas:
                            fg_areas[key].unlocked = True
                            self.txt.append("\n {color=[blue]}Team found Area: %s, it is now unlocked!!!{/color}" % key)

                        del area.unlocks[key]

            fg.exploring.remove(self)

            if not self.flag_red:
                self.flag_green = True
                fg.flag_green = True

            if self.flag_red:
                fg.flag_red = True

            # Create the event:
            evt = NDEvent()
            evt.red_flag = self.flag_red
            evt.green_flag = self.flag_green
            evt.charmod = self.stats
            evt.type = 'exploration_report'
            evt.char = None
            self.loc = fg

            # New style:
            args = list()
            for g in characters:
                if characters[g]:
                    # Dead:
                    args.append(im.Sepia(g.show("battle_sprite", resize=(200, 200), cache=True)))

                else:
                    # Alive!
                    args.append(g.show("battle_sprite", resize=(200, 200), cache=True))

            # args = list(g.show("battle_sprite", resize=(200, 200), cache=True) for g in self.team)
            img = Fixed(ProportionalScale(self.area.img, 820, 705, align=(0.5, 0.5)),
                        Text("%s"%self.team.name, style="agrevue", outlines=[ (1, crimson, 3, 3) ], antialias=True, size=30, color=red, align=(0.5, 0)),
                        HBox(*args, spacing=10, align=(0.5, 1.0)),
                        xysize=(820, 705))

            evt.img = img
            evt.txt = "".join(self.txt)
            NextDayEvents.append(evt)
