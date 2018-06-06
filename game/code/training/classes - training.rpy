init -9 python:
    def in_training_location(girl):
        """
        Checks whether a girl is currently in a location that offers training.
        girl = The girl to check.
        """
        # girl.location while training should be the school building?
        return girl.location in schools or girl.location in schools.values()


    class RunawayManager(_object):
        """
        The class that handles runawawy logic.
        """

        STATUS_STATS = ["vitality", "intelligence", "agility"]

        ACTION = "Hiding"
        LOCATION = "Unknown"

        CAUGHT = "caught"
        DEFEATED = "defeated"
        FOUGHT = "fought"
        ESCAPED = "escaped"

        def __init__(self):
            """
            Creates a new RunawwayManager.
            """
            self.girls = dict()
            self.jail_cache = dict()
            self.look_cache = dict()

            self.retrieve_jail = False

            # Slavemarket stuff
            self.girl = None
            self.index = 0

        def __contains__(self, girl):
            """
            Checks whether a girl has runaway.
            """
            return girl in self.girls

        def add(self, girl, jail=False):
            """
            Adds a girl that has runaway.
            girl = The girl to add.
            jail = Whether to add straight to jail.
            """
            if girl not in self:
                self.girls[girl] = 0
                girl.action = RunawayManager.ACTION
                girl.location = RunawayManager.LOCATION
                if girl in hero.team: hero.team.remove(girl)
                girl_disobeys(girl, 10)

                if jail:
                    self.jail_cache[girl] = [4, False]
                    if self.girl is None:
                        self.girl = girl
                        self.index = 0

        def buy_girl(self):
            """
            Buys an escaped girl from the jail.
            """
            if hero.take_ap(1):
                if hero.take_money(self.get_price(), reason="Slave Repurchase"):
                    renpy.play("content/sfx/sound/world/purchase_1.ogg")
                    self.retrieve(self.girl)

                else:
                    renpy.call_screen('message_screen', "You don't have enough money for this purchase!")

            else:
                renpy.call_screen('message_screen', "You don't have enough AP left for this action!!")

            if not self.chars_list:
                renpy.hide_screen("slave_shopping")

        def can_escape(self, girl, location, guards=None, girlmod=None, pos_traits=None,
                       neg_traits=["Restrained"], use_be=True, simulate=True, be_kwargs=None):
            """
            Calculates whether a girl can the location.
            girl = The girl check.
            location = The location to check, or None to ignore security and go straight to combat.
            guards = A list of guards to use in combat. If None guards/warriors are pulled from the locaiton.
            girlmod = A dict to use to record the girls stats.
            pos_traits = A list of trait names that increase the girls chance.
            neg_trats = A list of trait names that decrease the girls chance.
            use_be = Whether to require a BE simulation at high security levels.
            simulate = Whether to simulate the battle or use the BE.
            be_kwargs = Keyword arguments to pass to the BE.
            """
            # This requires revision to be used in the future!

            # Ensure stats in girlmod
            if girlmod:
                if "health" not in girlmod: girlmod["health"] = 0
                if "vitality" not in girlmod: girlmod["vitality"] = 0
                if "joy" not in girlmod: girlmod["joy"] = 0
                if "disposition" not in girlmod: girlmod["dosposition"] = 0
                if "exp" not in girlmod: girlmod["exp"] = 0

            be_kwargs = dict() if be_kwargs is None else be_kwargs
            # Get traits
            p = 0
            if pos_traits:
                for i in pos_traits:
                    p += girl_training_trait_mult(girl, i)

            n = 0
            if neg_traits:
                for i in neg_traits:
                    n += girl_training_trait_mult(girl, i)

            # Get security
            if location:
                sec = self.location_security(location)
                runaway = (self.location_runaway(location) + p) < (sec - n)

            else:
                sec = 1
                runaway = True

            if runaway:
                # If no BE or low security
                if not use_be or sec < .5:
                    # Girl escaped without fighting
                    return True, self.ESCAPED

                # If girl is too injured to fight
                elif girl.health < girl.get_max("health")*0.25 or girl.vitality < girl.get_max("vitality")*0.25 :
                    # Girl was caight without fighting
                    return False, self.CAUGHT

                # BE simultaion
                else:
                    # If we need guards
                    if not guards:

                        # If we have no location, girl walks out
                        if not location:
                            return True, self.ESCAPED

                        else:
                            # Get guards if available action
                            if hasattr(location, "actions") and "Guard" in location.actions:
                                guards = [g for g in location.get_girls("Guard") if g.AP > 0 and g.health > 40 and g.vitality > 40]

                            # Get warriors
                            else:
                                guards = [g for g in location.get_girls(occupation="Combatant") if g.AP > 0 and g.health > 40 and g.vitality > 40]

                            if girl in guards: guards.remove(girl)

                            # Force simulation if hero not available
                            if not simulate: simulate = hero.location is not location

                            # If we are simulating
                            if simulate:
                                # Get amount according to location
                                gam = max(int(len(guards) * ((sec-0.5) * 2)), 1)
                                while len(guards) > gam: guards.remove(choice(guards))

                                # Add hero
                                if hero.location is location: guards.append(hero)

                            # Else we are BE
                            else:
                                # If we have more then 2, get the player and 2 random guards
                                if len(guards) > 2:
                                    g = randint(0, len(guards)-1)
                                    guards = [hero, guards[g], guards[g+1]]
                                    pt_ai = [False, True, True]

                                else:
                                    guards.insert(0, hero)
                                    pt_ai = [True for i in guards]
                                    pt_ai[0] = False

                    # If we want to simulate
                    if simulate:

                        # If we end up with no guards
                        if not guards:
                            return True, self.ESCAPED

                        result, exp = s_conflict_resolver(guards, [girl], new_results=True)

                        # Remove hero from guards to avoid event
                        if hero in guards: guards.remove(hero)

                        # Overwhelming victory
                        # Girl was caught without fighting
                        if result == "OV":
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.stats(g, dict(exp=randint(15, 25)))
                                guard_escape_event.win(g, 1)

                            return False, self.CAUGHT

                        # Desisive victory
                        # Girl was caught easily while fighting
                        elif result == "DV":
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.stats(g, dict(health=randint(-10, -20),
                                                                 vitality=randint(-10, -20),
                                                                 exp=exp
                                                                 ))
                                guard_escape_event.win(g, 1)

                            if girlmod:
                                girlmod["health"] -= randint(20, 30)
                                girlmod["vitality"] -= randint(20, 30)
                                girlmod["joy"] -= choice([0,2,2,4,6])

                            else:
                                girl.health = max(1, girl.health - randint(20, 30))
                                girl.vitality -= randint(20, 30)
                                girl.joy -= choice([0,2,2,4,6])

                            return False, self.DEFEATED

                        # Victory
                        # Girl was caught while fighting
                        elif result == "V":
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.stats(g, dict(health=randint(-10, -20),
                                                                 vitality=randint(-10, -20),
                                                                 exp=exp
                                                                 ))
                                guard_escape_event.win(g, 1)

                            if girlmod:
                                girlmod["health"] -= randint(10, 20)
                                girlmod["vitality"] -= randint(10, 20)
                                girlmod["joy"] -= choice([0,1,1,2,3])

                            else:
                                girl.health = max(1, girl.health - randint(10, 20))
                                girl.vitality -= randint(10, 20)
                                girl.joy -= choice([0,1,2,2,3])

                            return False, self.DEFEATED

                        # Lucky victory
                        # Girl was bearly caught while fighting
                        elif result == "LV":
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.stats(g, dict(health=randint(-20, -30),
                                                                 vitality=randint(-20, -30),
                                                                 ))
                                guard_escape_event.win(g, 1)

                            if girlmod:
                                girlmod["health"] -= randint(10, 20)
                                girlmod["vitality"] -= randint(10, 20)
                                girlmod["exp"] += exp

                            else:
                                girl.health = max(1, girl.health - randint(10, 20))
                                girl.vitality -= randint(10, 20)
                                girl.exp += exp

                            return False, self.DEFEATED

                        # Defeat
                        # Girl was able to escape while fighting
                        elif result == "D":
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.stats(g, dict(health=randint(-20, -30),
                                                                 vitality=randint(-20, -30),
                                                                 ))
                                guard_escape_event.loss(g, 1)

                            if girlmod:
                                girlmod["health"] -= randint(10, 20)
                                girlmod["vitality"] -= randint(10, 20)
                                girlmod["exp"] += exp
                                girlmod["joy"] += choice([0,1,1,2,3])

                            else:
                                girl.health = max(1, girl.health - randint(10, 20))
                                girl.vitality -= randint(10, 20)
                                girl.exp += exp
                                girl.joy += choice([0,1,1,2,3])

                            return True, self.FOUGHT

                        # Overwhelming defeat
                        # Girl was able to escape without fighting
                        elif result == "OD":
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.loss(g, 1)

                            if girlmod:
                                girlmod["exp"] += exp
                                girlmod["joy"] += choice([0,2,2,4,6])

                            else:
                                girl.exp += exp
                                girl.joy += choice([0,2,2,4,6])

                            return True, self.ESCAPED

                    else:
                        # Fight!
                        # TODO lt training (Alex) Check out what this is/does:
                        result, dead = start_battle(guards, [girl], pt_ai=pt_ai, **be_kwargs)

                        exp = (girl.attack + girl.defence + girl.agility + girl.magic) / 10

                        # Remove hero from guards to avoid event
                        if hero in guards: guards.remove(hero)

                        # If the guards won
                        if result:
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.stats(g, dict(vitality=-randint(-10, -20),
                                                                 exp=exp
                                                                 ))
                                guard_escape_event.win(g, 1)

                            if girlmod:
                                girlmod["vitality"] -= randint(10, 20)
                                girlmod["joy"] -= choice([0,1,1,2,3])

                            else:
                                girl.health = max(1, girl.health - randint(10, 20))
                                girl.joy -= choice([0,1,1,2,3])

                            return True, self.DEFEATED

                        # Else the girl won
                        else:
                            for g in guards:
                                guard_escape_event.count(g, 1)
                                guard_escape_event.against(g, [girl])
                                guard_escape_event.stats(g, dict(vitality=-randint(-10, -20),
                                                                 exp=exp
                                                                 ))
                                guard_escape_event.loss(g, 1)

                            if girlmod:
                                girlmod["vitality"] -= randint(10, 20)
                                girlmod["exp"] += exp
                                girlmod["joy"] += choice([0,1,1,2,3])

                            else:
                                girlmod.vitality -= randint(10, 20)
                                girlmod.exp += exp
                                girl.joy += choice([0,1,1,2,3])

                            return False, self.FOUGHT

            else:
                return False

        def get_look_around_girl(self, event):
            """
            Gets the girl for the event.
            event = The event to return the girl for.
            """
            return self.look_cache.pop(event.name, None)

        def get_price(self):
            """
            Returns the price to retieve the girl.
            """
            # In case non-slaves escape, use 3000 as base price
            base = self.girl.fin.get_price() or 3000
            time = float(self.jail_cache[self.girl][0])
            return int(base * (.75 - (.125 * time)))

        def get_upkeep(self):
            """
            Return the upkeep cost for the girl.
            """
            return self.girl.fin.get_upkeep()

        @property
        def girlfin(self):
            """
            The property to return the proper financial data for the girl.
            """
            return self

        @property
        def chars_list(self):
            """
            The list to use for the slavemarket interface.
            """
            if self.jail_cache: return self.jail_cache.keys()
            else: return []

        def location_runaway(self, location, sutree=None):
            """
            Returns a runaway chance for the location.
            location = The location to calculate the chance for.
            sutree = The name of the security upgrade tree to use if not default.

            Calculates the chance using:
            - The mod_runaway function if it exists.
            - The sutree current / total, if it exists.
            - The amount of guards in the location, if the action exists.
            - The amount of warriors in the location

            Returns:
            0 = high chance.
            1 = low chance
            """
            # Get runaway modifier
            mod = 0

            # If location has own function, use it
            if hasattr(location, "mod_runaway"):
                mod = location.mod_runaway()

            # Else if location is upgradable, use its sutree @ Review: Alex: What the fuck is a sutree????
            # elif isinstance(location, UpgradableBuilding):
            #     if sutree is None: sutree = location.security_upgrade_tree
            #     mod = self.get_upgrade_mod(sutree) / len(self.upgrades[sutree])

            # Else if has guard action, use amount over total
            elif hasattr(location, "actions") and "Guard" in location.actions:
                girls = [g for g in hero.chars if g.location == location]
                if girls:
                    mod = float(len(location.get_girls("Guard"))) / float(len(girls))
                else:
                    mod = 0

            # Else use warriors over total
            else:
                girls = [g for g in hero.chars if g.location == location]
                if girls:
                    mod = float(len(location.get_girls(occupation="Combatant"))) / float(len(girls))
                else:
                    mod = 0

            return mod

        def location_security(self, location, modifier=1):
            """
            Returns the security modifier for the location.
            location = The location to get the modifier for.
            modifier = A multiplier for the final modifier.

            Returns:
            1 = low chance
            2 = high chance
            """
            # Handled differently now.
            return 1 # (random.random() * (2 - location.security_mult())) * modifier

        def next_day(self):
            """
            Solves the next day logic for the girls.
            """
            girls = self.girls.keys()
            cdb = config.developer
            type = "schoolndreport"
            txt = ["Escaped girls:"]

            # Replace with better code to prevent mass-creation/destruction of events?
            # Clean look_cache
            for i in self.look_cache.keys():
                pytfall.world_events.kill_event(i, cached=True)
                del self.look_cache[i]

            # Clean jail_cache
            for i in self.jail_cache.keys():
                if self.jail_cache[i][0] == 0:
                    del self.jail_cache[i]

                else:
                    self.jail_cache[i][0] -= 1

            # Loop through girls
            while girls:
                girl = choice(girls)
                girls.remove(girl)
                cdb = config.developer
                txt.append("    %s"%girl.fullname)

                # Increase girls escape time
                self.girls[girl] += 1

                # Get status
                status = self.status(girl)
                if cdb: txt.append("{color=[blue]}        status: %s{/color}"%status)

                # If girl is free
                if girl not in self.jail_cache:
                    # Chance to escape for good
                    if self.girls[girl] > 20:
                        if dice(status) and dice(self.girls[girl]):
                            del self.girls[girl]
                            hero.remove_char(girl)
                            if girl in hero.team:
                                hero.team.remove(girl)

                            if cdb: txt.append("{color=[blue]}        escaped for good{/color}")
                            continue

                    # Chance to go to jail
                    if self.girls[girl] > 10:
                        if dice(status) and len(self.jail_cache) < 10:
                            self.jail_cache[girl] = [4, False]

                            if cdb: txt.append("{color=[blue]}        sent to jail for 4 days (%s days till escape){/color}"%(20-self.girls[girl]))
                            continue

                    # Chance to find in look_around
                    if dice(status) and len(self.look_cache) < 5:
                        ev = "runaway_look_around_%s"%str(girl)
                        self.look_cache[ev] = girl
                        # Add event for girl (do we want high priority?)
                        register_event_in_label(ev, label=girl.runaway_look_event, trigger_type="look_around", locations=["all"], dice=status, max_runs=1, start_day=day+1, priority=999)

                        if cdb: txt.append("{color=[blue]}        in look around (%s days till escape){/color}"%(20-self.girls[girl]))
                        continue

                    if cdb: txt.append("{color=[blue]}        %s days till escape{/color}"%(20-self.girls[girl]))

                # Else if girl is jailed
                else:
                    # If we know they're in jail
                    if self.jail_cache[girl][1]:
                        txt.append("    %s, in jail for %s days"%(girl.fullname, self.jail_cache[girl][0]))
                        if cdb: txt.append("{color=[blue]}    (%s days till escape){/color}"%(20-self.girls[girl]))

                    # Else
                    else:
                        txt.append("    %s"%girl.fullname)
                        if cdb: txt.append("{color=[blue]}        in jail for %s days (%s days till escape){/color}"%(self.jail_cache[girl], (20-self.girls[girl])))

            # Slavemarket update
            self.index = 0
            if self.jail_cache:
                self.girl = self.chars_list[0]

            # If we have escaped girls, post the event
            if self.girls:
                ev = NDEvent()
                ev.type = type
                ev.char = None
                ev.img = im.Scale("content/gfx/bg/locations/dungeoncell.webp", int(config.screen_width*0.6), int(config.screen_height*0.8))
                ev.txt = "\n".join(txt)
                NextDayEvents.append(ev)

        def next_index(self):
            """
            Sets the next index for the slavemarket.
            """
            self.index = (self.index+1) % len(self.chars_list)
            self.girl = self.chars_list[self.index]

        def previous_index(self):
            """
            Sets the previous index for the slavemarket.
            """
            self.index = (self.index-1) % len(self.chars_list)
            self.girl = self.chars_list[self.index]

        def retrieve(self, girl):
            """
            Returns a girl to the player.
            girl = The girl to return.
            """
            if girl in self:
                del self.girls[girl]

                ev = "runaway_look_around_%s"%str(girl)
                if ev in self.look_cache:
                    del self.look_cache[ev]
                    pytfall.world_events.kill_event(ev)

                if girl in self.jail_cache:
                    del self.jail_cache[girl]

                    if self.jail_cache:
                        self.index %= len(self.jail_cache)
                        self.girl = self.chars_list[self.index]

                    else:
                        self.index = 0
                        self.girl = None

                girl.action = None

                if False: #schools[TrainingDungeon.NAME] in hero.buildings:
                    girl.location = schools[TrainingDungeon.NAME]
                else:
                    girl.location = hero

        def set_girl(self, girl):
            """
            Sets the girl to be the index for the slavemarket.
            girl = The girl to set.
            """
            if self.chars_list and girl in self.chars_list:
                self.girl = girl
                self.index = self.chars_list.index(self.girl)

        def status(self, girl):
            """
            Returns the "runaway status" of the girl.
            girl = The girl to get the status for.
            """
            a = 0
            b = 0
            for i in self.STATUS_STATS:
                a += girl.stats[i]
                b += girl.stats.max[i]

            status = (float(a) / float(b)) * 100
            status *= girl_training_trait_mult(girl, "Restrained")
            if girl.status == "slave": status *= .75

            return 100-status
