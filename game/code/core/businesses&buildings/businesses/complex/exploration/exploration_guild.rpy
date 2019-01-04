init -9 python: # FG Area
    class FG_Area(_object):
        """Dummy class for areas (for now).

        Tracks the progress in SE areas as well as storing their data.
        """
        def __init__(self):
            self.stage = 0 # For Sorting.
            self.tier = .2 # Difficulty
            self.days = 3
            self.max_days = 15
            self.risk = 50
            self._explored = 0

            self.main = False
            self.area = None

            self.travel_time = 0
            self.hazard = dict()
            self.items = dict()
            self.mobs = dict()

            # Special fields for quests, keys are chars or items and values are
            # exploration progress required to get them. Later we might add
            # some complex conditions instead, like fighting mobs.
            self.special_items = dict()
            self.special_chars = dict()

            # Chars capture:
            self.capture_chars = False
            self.chars = dict() # id: [explored, chance_per_day]
            self.rchars = dict() # id can be 'any' here, meaning any rChar.

            self.items_price_limit = 0

            # Use dicts instead of sets as we want counters:
            self.mobs_defeated = dict()
            self.found_items = dict()
            self.chars_captured = 0
            self.cash_earned = 0

            # Flags for exploration tasks on "area" scope.
            self.camp = None
            self.building_camp = False
            self.camp_build_points_current = 0
            self.camp_build_points_required = 1000

            # Generated Content:
            self.logs = collections.deque(maxlen=15)

            # Trackers exploring the area at any given time, this can be used for easy access!
            self.trackers = set()

        @property
        def camp_build_status(self):
            return "%d%%" % (100.0*self.camp_build_points_current/self.camp_build_points_required)

        @property
        def teams(self):
            # Teams presently exploring this area:
            return [t.team for t in self.trackers]

        @property
        def explored(self):
            return self._explored

        @explored.setter
        def explored(self, value):
            if value >= 100:
                self._explored = 100
            else:
                self._explored = value


init -6 python: # Guild, Tracker and Log.
    # ======================= (Simulated) Exploration code =====================>>>
    class ExplorationTracker(Job):
        # Added inheritance for Job so we can use the required methods.
        """The class that stores data for an exploration job.

        *Not really a Job, it stores data and doesn't write any reports to ND. **Maybe it should create ND report once the run is done!
        Adapted from old FG, not sure what we can keep here..."""
        def __init__(self, team, area, guild):
            """Creates a new ExplorationJob.

            team = The team that is exploring.
            area = The area that is being explored.
            """
            super(ExplorationTracker, self).__init__()
            self.id = "Exploration"
            self.type = "Combat"

            # Traits/Job-types associated with this job:
            self.occupations = ["Combatant"] # General Strings likes SIW, Combatant, Server...
            self.occupation_traits = [traits["Warrior"], traits["Mage"]] # Corresponding traits...

            self.base_stats = {"attack": 20, "defence": 20,
                               "agility": 60, "magic": 20}
            self.base_skills = {"exploration": 100}

            self.desc = "Explore the world, find new places, meet new people... and take their shit!"

            # We do this because this data needs to be tracked separately and
            # area object can only be updated once team has returned.
            # There is a good chance that some of these data must be updated in real time.
            self.area = deepcopy(area)
            self.team = team
            self.guild = guild # Guild this tracker was initiated from...

            # Features:
            self.basecamp = False
            self.base_camp_health = 0 # We call it health in case we allow it to be attacked at some point...

            # This is the general items that can be found at any exploration location,
            # Limited by price:
            self.exploration_items = list(item.id for item in store.items.values() if
                                          "Exploration" in item.locations and
                                          area.items_price_limit >= item.price)

            # Traveling to and from + Status flags:
            # We may be setting this directly in the future.
            # Distance in KM as units. 25 is what we expect the
            # team to be able to travel in a day.
            # This may be offset through traits and stats/skills.
            self.distance = area.travel_time * 25
            # We assume that it's never right outside of the
            # freaking city walls, so we do this:
            if not self.distance:
                self.distance = randint(4, 10)

            self.traveled = 0 # Distance traveled in "KM"...
            self.arrived = False # Set to True upon arrival to the location.
            self.finished_exploring = False # Set to True after exploration is finished.

            # Exploration:
            self.points = 0 # Combined JP. Replaces AP, but we get this from the whole team.
            # Used to be effectiveness, but that would collide with a method of parent class
            self.ability = 0 # How well the team can perform any given exploration task.
            self.travel_points = 0 # travel point we use during traveling to offset JP correctly.

            self.state = "traveling to" # Instead of a bunch of properties, we'll use just the state as string and set it accordingly.
            # Use dicts instead of sets as we want counters:
            self.mobs_defeated = defaultdict(int)
            self.found_items = list()
            self.captured_chars = list()
            self.cash = list()

            self.day = 1 # Day since start.
            self.total_days = 0 # Total days, travel times excluded!
            # Days team is expected to be exploring (without travel times)!
            self.days = self.area.days
            if self.days < 3:
                self.days = 3
            self.days_in_camp = 0 # Simple counter for the amount of days team is spending at camp. This is set back to 0 when team recovers inside of the camping method.

            self.unlocks = dict()
            for key in self.area.unlocks:
                self.unlocks[key] = 0

            self.flag_red = False
            self.flag_green = False
            self.logs = list() # List of all log object we create during this exploration run.
            self.died = list()

            # And we got to make copies of chars stat dicts so we can show
            # changes in ND after the exploration run is complete!
            self.init_stats = dict()
            for i in self.team:
                self.init_stats[i] = i.stats.stats.copy()

            if not DEBUG:
                renpy.show_screen("message_screen", "Team %s was sent out on %d days exploration run!" % (team.name, area.days))

        @property
        def obj_area(self):
            # "Global" area object, we usually update this where we're done.
            return fg_areas[self.area.id]

        @property
        def mobs(self):
            return self.area.mobs

        @property
        def risk(self):
            # TODO se: Remove 50 after testing and interface adjustments.
            return self.area.risk or 50

        @property
        def cash_limit(self):
            return self.area.cash_limit

        @property
        def items_limit(self):
            return self.area.items_limit

        @property
        def hazard(self):
            return self.area.hazard

        def log(self, txt, name="", nd_log=True, ui_log=False, **kwargs):
            if DEBUG_SE:
                msg = "{}: {} at {}\n    {}".format(self.area.name,
                                    self.team.name, self.guild.env.now, txt)
                se_debug(msg, mode="info")

            obj = ExplorationLog(name, txt, nd_log, ui_log, **kwargs)
            self.logs.append(obj)
            return obj

        def finish_exploring(self):
            """
            Build one major report for next day!
            Log all the crap to Area and Main Area!
            Make sure that everything is cleaned up.
            """
            global fg_areas
            global items
            area = self.obj_area

            # Main and Sub Area Stuff:
            area.logs.extend([l for l in self.logs if l.ui_log])
            area.trackers.remove(self)

            # Update data and settle rewards:
            area.mobs_defeated = add_dicts(area.mobs_defeated, self.mobs_defeated)
            found_items = collections.Counter(self.found_items)
            area.found_items = add_dicts(area.found_items, found_items)
            for i in self.found_items:
                item = items[i]
                hero.add_item(item)

            area.chars_captured += len(self.captured_chars)

            main_area = fg_areas[area.area]
            main_area.mobs_defeated = add_dicts(area.mobs_defeated, main_area.mobs_defeated)
            main_area.found_items = add_dicts(area.found_items, main_area.found_items)

            # Restore Chars and Remove from guild:
            self.guild.explorers.remove(self)
            for char in self.team:
                char.action = char.flag("loc_backup")
                char.del_flag("loc_backup")

            # Next Day Stuff:
            # Not sure if this is required... we can add log objects and build
            # reports from them in real-time instead of replicating data we already have.
            txt = []
            event_type = "jobreport"

            # Build an image combo for the report:
            img = Fixed(xysize=(820, 705))
            img.add(Transform(area.img, size=(820, 705)))
            vp = vp_or_fixed(self.team, ["fighting"],
                             {"exclude": ["sex"],
                             "resize": (150, 150)}, xmax=820)
            img.add(Transform(vp, align=(.5, .9)))

            # We need to create major report for nd to keep track of progress:
            for log in [l for l in self.logs if l.nd_log]:
                txt.append("\n".join(log.txt))

            evt = NDEvent(type=event_type,
                          img=img,
                          txt=txt,
                          char=self.team[0],
                          team=self.team,
                          charmod={},
                          loc=self.guild.building,
                          locmod={},
                          green_flag=self.flag_green,
                          red_flag=self.flag_red)
            NextDayEvents.append(evt)


    class ExplorationLog(Action):
        """Stores resulting text and data for SE.

        Also functions as a screen action for future buttons. Maybe...
        """
        def __init__(self, name="", txt="", nd_log=True, ui_log=False, item=None):
            """
            nd_log: Printed in next day report upon arrival.
            ui_log: Only reports worth of ui interface in FG.
            """
            self.name = name # Name of the event, to be used as a name of a button in gui. (maybe...)
            self.suffix = "" # If there is no special condition in the screen, we add this to the right side of the event button!

            self.nd_log = nd_log
            self.ui_log = ui_log
            self.txt = [] # I figure we use list to store text.
            if txt:
                self.txt.append(txt)

            self.battle_log = [] # Used to log the event.
            self.found_items = []
            self.item = item # Item object for the UI log if one was found!

        def add(self, text, newline=True):
            # Adds a text to the log.
            self.txt.append(text)

        def __call__(self):
            renpy.show_screen("...") # Whatever the pop-up screen with info in gui is gonna be.

        def is_sensitive(self):
            # Check if the button has an action.
            return self.battle_log or self.found_items


    class ExplorationGuild(TaskBusiness):
        SORTING_ORDER = 10
        COMPATIBILITY = []
        MATERIALS = {"Wood": 70, "Bricks": 50, "Glass": 5}
        NAME = "Exploration Guild"
        IMG = "content/gfx/bg/buildings/Chorrol_Fighters_Guild.webp"
        DESC = "Travel to exotic places, meet new monsters and people... and take their shit!"

        def __init__(self, **kwargs):
            super(ExplorationGuild, self).__init__(**kwargs)

            # Global Values that have effects on the whole business.
            self.teams = list() # List to hold all the teams formed in this guild. We should add at least one team or the guild will be useless...
            self.explorers = list() # List to hold all the (active) exploring trackers.

            self.teams.append(Team("Avengers", free=True))
            if DEBUG_SE:
                for i in range(5):
                    self.teams.append(Team("Team " + str(i), free=True))

            self.workable = True
            self.focus_team = None
            self.team_to_launch_index = 0

        # Teams control/sorting/grouping methods:
        def teams_to_launch(self):
            # Returns a list of teams that can be launched on an exploration run.
            # Must have at least one member and NOT already running exploration!
            return [t for t in self.idle_teams() if t]

        def prev_team_to_launch(self):
            teams = self.teams_to_launch()
            index = self.team_to_launch_index

            index = (index-1) % len(teams)

            self.team_to_launch_index = index
            self.focus_team = teams[index]

        def next_team_to_launch(self):
            teams = self.teams_to_launch()
            index = self.team_to_launch_index

            index = (index+1) % len(teams)

            self.team_to_launch_index = index
            self.focus_team = teams[index]

        def exploring_teams(self):
            # Teams that are busy with exploration runs.
            return [tracker.team for tracker in self.explorers]

        def idle_teams(self):
            # Teams avalible for setup in order to set them on exploration runs.
            return [t for t in self.teams if t not in self.exploring_teams()]

        def idle_explorers(self):
            # Returns a list of idle explorers:
            return list(chain.from_iterable(t.members for t in self.idle_teams()))

        def launch_team(self, area, _team=None):
            # Moves the team to appropriate list, removes from main one and makes sure everything is setup right from there on out:
            team = self.focus_team if not _team else _team
            # self.teams.remove(team) # We prolly do not do this?

            # Setup Explorers:
            for char in team:
                # We effectively remove char from the game so this is prolly ok.
                char.action = "Exploring"
                char.set_flag("loc_backup", char.location)
                if char in hero.team:
                    hero.team.remove(char)

            # Remove Explorers from other teams:
            for t in self.teams:
                if t != team:
                    for char in team:
                        if char in t:
                            t.remove(char)

            tracker = ExplorationTracker(team, area, self)
            area.trackers.add(tracker)
            self.explorers.append(tracker)

            if not _team:
                self.focus_team = None
                self.team_to_launch_index = 0

        # SimPy methods:
        def business_control(self):
            """SimPy business controller.
            """
            for tracker in self.explorers:
                self.env.process(self.exploration_controller(tracker))

            while 1:
                yield self.env.timeout(100)

        def exploration_controller(self, tracker):
            # Controls the exploration by setting up proper simpy processes.
            # Prep aliases:
            process = self.env.process
            area = tracker.obj_area
            team = tracker.team

            # Convert AP to exploration points:
            self.convert_AP(tracker)

            if DEBUG_SE:
                msg = "Entered exploration controller for {}.".format(team.name)
                se_debug(msg, mode="info")

            # Log the day:
            temp = "{color=[green]}Day: %d{/color} | {color=[green]}%s{/color} is exploring %s!\n" % (tracker.day, tracker.team.name, tracker.area.name)
            if tracker.day != 1:
                temp = "\n" + temp
            tracker.log(temp)

            # Set the state to traveling back if we're done:
            if tracker.day > tracker.days:
                tracker.state = "traveling back"
            elif area.building_camp:
                tracker.state = "setting_up_basecamp"

            while self.env.now < 99:
                if tracker.state == "traveling to":
                    yield process(self.travel_to(tracker))
                elif tracker.state == "exploring":
                    result = yield process(self.explore(tracker))
                    if result == "captured char":
                        tracker.state = "traveling back"
                elif tracker.state == "camping":
                    yield process(self.camping(tracker))
                elif tracker.state == "traveling back":
                    result = yield process(self.travel_back(tracker))
                    if result == "back2guild":
                        tracker.finish_exploring() # Build the ND report!
                        self.env.exit() # We're done...
                elif tracker.state == "setting_up_basecamp":
                    yield process(self.setup_basecamp(tracker))

            # if DEBUG_SE:
                # tracker.log("Debug: The day has come to an end for {}.".format(tracker.team.name))
            self.overnight(tracker)
            tracker.day += 1

        def travel_to(self, tracker):
            # Env func that handles the travel to routine.
            team = tracker.team
            area = tracker.area

            if DEBUG_SE:
                msg = "{} is traveling to {}.".format(team.name, area.id)
                se_debug(msg, mode="info")

            # Figure out how far we can travel in steps of 5 DU:
            # Understanding here is that any team can travel 25 KM per day on average. This can be offset by traits and stats in the future.
            # tacker.tp = int(round(tracker.points / 20.0))
            travel_points = round_int(tracker.points / 20.0) # local variable just might do the trick...

            if not tracker.traveled:
                temp = "{} is on route to {}!".format(tracker.team.name, tracker.area.id)
                tracker.log(temp)

            while 1:
                yield self.env.timeout(5) # We travel...

                tracker.points -= tracker.travel_points
                tracker.traveled += 1.25

                # Team arrived:
                if tracker.traveled <= tracker.distance:
                    if DEBUG_SE:
                        msg = "{} arrived at {}.".format(team.name, area.id)
                        se_debug(msg, mode="info")

                    temp = "{} arrived at {}!".format(team.name, area.id)
                    if tracker.day > 1:
                        temp = temp + " It took {} {} to get there.".format(tracker.day, plural("day", tracker.day))
                    else:
                        temp = temp + " The trip took less then one day!"
                    tracker.log(temp, name="Arrival")
                    tracker.state = "exploring"
                    tracker.traveled = 0 # Reset for traveling back.
                    self.env.exit("arrived")

                if self.env.now >= 99: # We couldn't make it there before the days end...
                    temp = "{} spent the entire day on route to {}! ".format(team.name, area.id)
                    tracker.log(temp)
                    if DEBUG_SE:
                        se_debug(temp, mode="info")
                    self.env.exit("not_arrived")

        def travel_back(self, tracker):
            # Env func that handles the travel to routine.
            team = tracker.team

            if DEBUG_SE:
                msg = "{} is traveling back.".format(team.name)
                se_debug(msg, mode="info")

            # Figure out how far we can travel in 5 du:
            # Understanding here is that any team can travel 25 KM per day on average.
            # This can be offset by traits and stats in the future.
            # tacker.tp = int(round(tracker.points / 20.0))
            travel_points = round_int(tracker.points / 20.0) # local variable just might do the trick...

            if not tracker.traveled:
                temp = "{} is traveling back home!".format(tracker.team.name)
                tracker.log(temp)

            while 1:
                yield self.env.timeout(5) # We travel...

                tracker.points -= tracker.travel_points
                tracker.traveled += 1.25

                # Team arrived:
                if tracker.traveled <= tracker.distance:
                    temp = "{} returned to the guild!".format(tracker.team.name)
                    tracker.log(temp, name="Return")
                    # tracker.state = "exploring"
                    # tracker.traveled = 0 # Reset for traveling back.
                    self.env.exit("back2guild")

                if self.evn.now >= 99: # We couldn't make it there before the days end...
                    temp = "{} spent the entire day traveling back to the guild from {}! ".format(tracker.team.name, tracker.area.id)
                    tracker.log(temp)
                    self.env.exit("on the way back")

        def camping(self, tracker):
            """Camping will allow restoration of health/mp/agility and so on. Might be forced on low health.
            """
            team = tracker.team
            area = tracker.area
            auto_equip_counter = 0 # We don't want to run over autoequip on every iteration, two times is enough.

            if DEBUG_SE:
                msg = "{} is Camping. State: {}".format(team.name, tracker.state)
                se_debug(msg, mode="info")

            if not tracker.days_in_camp:
                temp = "{} setup a camp to get some rest and recover!".format(team.name)
                tracker.log(temp)

            while 1:
                yield self.env.timeout(5) # We camp...

                # Base stats:
                for c in team:
                    c.health += randint(8, 12)
                    c.mp += randint(8, 12)
                    c.vitality += randint(20, 50)

                # Apply items:
                if auto_equip_counter < 2:
                    invlist = list(c.inventory for c in team)
                    random.shuffle(invlist)
                    for explorer in team:
                        l = list()
                        if explorer.health <= explorer.get_max("health")*.8:
                            for inv in invlist:
                                l.extend(explorer.auto_equip(["health"], inv=inv))
                        if explorer.vitality <= explorer.get_max("vitality")*.8:
                            for inv in invlist:
                                l.extend(explorer.auto_equip(["vitality"], inv=inv))
                        if explorer.mp <= explorer.get_max("mp")*.8:
                            for inv in invlist:
                                l.extend(explorer.auto_equip(["mp"], inv=inv))
                        if l:
                            temp = "%s used: {color=[lawngreen]}%s %s{/color} to recover!\n" % (explorer.nickname, ", ".join(l), plural("item", len(l)))
                            self.log(temp)
                    auto_equip_counter += 1

                for c in team:
                    if c.health <= c.get_max("health")*.9:
                        break
                    if c.mp <= c.get_max("mp")*.9:
                        break
                    if c.vitality <= c.get_max("vitality")*.8:
                        break
                else:
                    tracker.days_in_camp = 0
                    temp = "{} are now ready for more action in {}! ".format(team.name, area.id)
                    tracker.log(temp)
                    tracker.state = "exploring"
                    self.env.exit("restored after camping")

                if self.env.now >= 99:
                    tracker.days_in_camp += 1

                    if DEBUG_SE:
                        msg = "{} finished Camping. (Day Ended)".format(team.name)
                        se_debug(msg, mode="info")

                    self.env.exit("still camping")

                # if not stop:
                    # for member in self.team:
                        # if member.health <= (member.get_max("health") / 100.0 * (100 - self.risk)) or member.health < 15:
                            # temp = "{color=[blue]}Your party falls back to base due to risk factors!{/color}"
                            # tracker.log(temp)

            if DEBUG_SE:
                msg = "{} finished Camping.".format(team.name)
                se_debug(msg, mode="info")

        def overnight(self, tracker):
            # overnight: More effective heal. Spend the night resting.
            # Do we run this? This prolly doesn't need to be a simpy process...
            # or maybe schedule this to run at 99.
            team = tracker.team

            if DEBUG_SE:
                msg = "{} is overnighting. State: {}".format(team.name, tracker.state)
                se_debug(msg, mode="info")

            if tracker.state == "exploring":
                temp = "{} are done with exploring for the day and will now rest and recover! ".format(tracker.team.name)
                tracker.log(temp)
            elif tracker.state == "camping":
                temp = "{} cozied up in their camp for the night! ".format(tracker.team.name)
                tracker.log(temp)

            for c in team:
                c.health += randint(30, 40)
                c.mp += randint(30, 40)
                c.vitality += randint(100, 120)

        def explore(self, tracker):
            """SimPy process that handles the exploration itself.

            Idea is to keep as much of this logic as possible and adapt it to work with SimPy...
            """
            items = list()
            cash = 0
            area = tracker.obj_area
            carea = tracker.area
            team = tracker.team
            fought_mobs = 0
            encountered_opfor = 0

            if DEBUG_SE:
                msg = "{} is stating an exploration scenario.".format(team.name)
                se_debug(msg, mode="info")

            # Effectiveness (Ability):
            abilities = list()
            # Difficulty is tier of the area explored + 1/10 of the same value / 100 * risk.
            difficulty = area.tier+(area.tier*.001*area.risk)
            for char in team:
                # Set their exploration capabilities as temp flag
                a = tracker.effectiveness(char, difficulty, log=None, return_ratio=False)
                abilities.append(a)
            tracker.ability = get_mean(abilities)

            # Let's run the expensive item calculations once and just give
            # Items as we explore. This just figures what items to give.
            # Get the max number of items that can be found in one day:
            max_items = int(round((tracker.ability+tracker.risk)*.01+(tracker.day*.2)))
            if DEBUG_SE:
                msg = "Max Items ({}) to be found on Day: {}!".format(max_items, tracker.day)
                se_debug(msg, mode="info")

            chosen_items = [] # Picked items:
            # Local Items:
            local_items = []
            for i, d in area.items.iteritems():
                if dice(d):
                    local_items.append(i)

            if DEBUG_SE:
                msg = "Local Items: {}|Area Items: {}".format(len(local_items), len(tracker.exploration_items))
                se_debug(msg, mode="info")

            while len(chosen_items) <= max_items and (tracker.exploration_items or local_items):
                # always pick from local item list first!
                if local_items and len(chosen_items) <= max_items:
                    chosen_items.append(choice(local_items))

                if tracker.exploration_items and len(chosen_items) <= max_items:
                    chosen_items.append(choice(tracker.exploration_items))

            if DEBUG_SE:
                msg = "({}) Items were picked for choice!".format(len(chosen_items))
                se_debug(msg, mode="info")

            # Max cash to be found this day:
            max_cash = tracker.cash_limit + tracker.cash_limit*.1*tracker.day

            shuffle(chosen_items)

            while 1:
                yield self.env.timeout(5) # We'll go with 5 du per one iteration of "exploration loop".

                # Hazzard:
                if area.hazard:
                    temp = "{color=[yellow]}Hazardous area!{/color} The team has been effected."
                    tracker.log(temp)
                    for char in team:
                        for stat, value in area.hazard:
                            # value, because we calculated effects on daily base in the past...
                            var = max(1, round_int(value*.05))
                            char.mod_stat(stat, -var)

                # Items:
                # Handle the special items (must be done here so it doesn't collide with other teams)
                special_items = []
                if area.special_items:
                    for item, explored in area.special_items.items():
                        if area.explored >= explored:
                            special_items.append(item)

                if (chosen_items or special_items) and not self.env.now % 5:
                    if self.env.now < 50:
                        chance = self.env.now/5
                    elif self.env.now < 80:
                        chance = self.env.now
                    else:
                        chance = 100

                    if dice(chance):
                        if special_items:
                            item = special_items.pop()
                            temp = "Found a special item %s!" % item
                            temp = set_font_color(temp, "orange")
                            tracker.log(temp, "Item", ui_log=True, item=store.items[item])
                            if DEBUG_SE:
                                msg = "{} Found a special item {}!".format(team.name, item)
                                se_debug(msg, mode="info")
                        else:
                            item = chosen_items.pop()
                            temp = "Found an item %s!" % item
                            temp = set_font_color(temp, "lawngreen")
                            tracker.log(temp, "Item", ui_log=True, item=store.items[item])
                            if DEBUG_SE:
                                msg = "{} Found an item {}!".format(team.name, item)
                                se_debug(msg, mode="info")
                        items.append(item)

                # Cash:
                if max_cash > 0 and not self.env.now % 20:
                    if dice(tracker.risk):
                        give = round_int(max_cash/5.0)
                        max_cash -= give
                        cash += give

                        temp = "{color=[gold]}Found %d Gold!{/color}" % give
                        tracker.log(temp)
                        if DEBUG_SE:
                            msg = "{} Found {} Gold!".format(team.name, give)
                            se_debug(msg, mode="info")

                #  =================================================>>>
                # Copied area must be used for checks here as it preserves state.
                if carea.capture_chars and not self.env.now % 10:
                    # Special Chars:
                    if area.special_chars:
                        for char, explored in area.special_chars.items():
                            if area.explored >= explored:
                                del(area.special_chars[char])
                                tracker.captured_chars.append(char)

                                temp = "Your team has captured a 'special' character: {}!".format(char.name)
                                temp = set_font_color(temp, "orange")
                                tracker.log(temp)
                                if DEBUG_SE:
                                    msg = "{} has finished an exploration scenario. (Captured a special char {})".format(team.name, char.id)
                                    se_debug(msg, mode="info")

                                self.env.exit("captured char")

                    # uChars (also from Area):
                    if area.chars:
                        for id, data in area.chars.items():
                            explored, chance = data
                            if area.explored >= explored and dice(chance*.1):
                                del(area.chars[id])

                                char = store.chars[id]
                                tracker.captured_chars.append(char)
                                temp = "Your team has captured a character: {}!".format(char.name)
                                temp = set_font_color(temp, "lawngreen")
                                tracker.log(temp)
                                if DEBUG_SE:
                                    msg = "{} has finished an exploration scenario. (Captured a uChar {})".format(team.name, char.id)
                                    se_debug(msg, mode="info")

                                self.env.exit("captured char")

                    # rChars:
                    if area.rchars:
                        for id, data in area.rchars.items():
                            explored, chance = data
                            if area.explored >= explored and dice(chance*.1):
                                # Get tier:
                                if area.tier == 0:
                                    tier = random.uniform(.1, .3)
                                else:
                                    tier = random.uniform(area.tier*.8, area.tier*1.2)
                                tier = min(.1, tier)
                                tier = max(8, tier) # never build rChars over tier 8?

                                kwargs = {"tier": tier, "set_status": True}
                                if id != "any":
                                    kwargs["id"] = id

                                char = build_rc(**kwargs)
                                tracker.captured_chars.append(char)
                                temp = "Your team has captured a character: {}!".format(char.name)
                                temp = set_font_color(temp, "lawngreen")
                                tracker.log(temp)
                                if DEBUG_SE:
                                    msg = "{} has finished an exploration scenario. (Captured an rChar {})".format(team.name, char.id)
                                    se_debug(msg, mode="info")

                                self.env.exit("captured char")

                if not fought_mobs and tracker.mobs:
                    # Never fight anyone with risk lower than 25..
                    encounter_chance = dice(carea.risk-25)
                    if encounter_chance:
                        fought_mobs = 1

                        mob = choice(tracker.mobs)

                        min_enemies = max(1, len(team) - 1)
                        max_ememies = max(3, len(team) + randrange(2))
                        enemies = randint(min_enemies, max_ememies)

                        temp = "\n{} were attacked by ".format(team.name)
                        temp = temp + "%d %s!" % (enemies, plural(mob, enemies))
                        log = tracker.log(temp, "Combat!", ui_log=True)

                        result = self.combat_mobs(tracker, mob, enemies, log)
                        if result == "defeat":
                            tracker.state = "camping"
                            if DEBUG_SE:
                                msg = "{} has finished an exploration scenario. (Lost a fight)".format(team.name)
                                se_debug(msg, mode="info")
                            self.env.exit()


                # This basically means that team spent the day exploring and ready to go to rest.
                if self.env.now >= 99:
                    if items and cash:
                        tracker.log("The team has found: %s %s" % (", ".join(items), plural("item", len(items))))
                        tracker.found_items.extend(items)
                        tracker.log(" and {color=[gold]}%d Gold{/color} in loot!" % cash)
                        tracker.cash.append(cash)

                    if cash and not items:
                        tracker.log("The team has found: {color=[gold]}%d Gold{/color} in loot." % cash)
                        tracker.cash.append(cash)

                    if items and not cash:
                        tracker.log("The team has found: %s %s" % (", ".join(items), plural("item", len(items))))
                        tracker.found_items.extend(items)

                    if not items and not cash:
                        tracker.log("Your team has not found anything of interest...")

                    if DEBUG_SE:
                        msg = "{} has finished an exploration scenario. (Day Ended)".format(team.name)
                        se_debug(msg, mode="info")
                    self.env.exit()

                # self.stats["agility"] += randrange(2)
                # self.stats["exp"] += randint(5, int(max(15, self.risk/4)))

                # TODO: This should be a part of camping method.
                # inv = list(g.inventory for g in self.team)
                # for g in self.team:
                    # l = list()
                    # if g.health < 75:
                        # l.extend(g.auto_equip(["health"], source=inv))
                    # if g.vitality < 100:
                        # l.extend(g.auto_equip(["vitality"], source=inv))
                    # if g.mp < 30:
                        # l.extend(g.auto_equip(["mp"], source=inv))
                    # if l:
                        # self.txt.append("\n%s used: {color=[blue]}%s %s{/color} to recover!\n" % (g.nickname, ", ".join(l), plural("item", len(l))))

                # if not stop:
                    # for member in self.team:
                        # if member.health <= (member.get_max("health") / 100.0 * (100 - self.risk)) or member.health < 15:
                            # temp = "{color=[blue]}Your party falls back to base due to risk factors!{/color}"
                            # tracker.log(temp)

        def combat_mobs(self, tracker, mob, opfor_team_size, log):
            # log is the Exploration Log object we add be reports to!
            # Do we really need to pass team size to this method instead of figuring everything out here?
            team = tracker.team
            opfor = Team(name="Enemy Team", max_size=opfor_team_size)

            if DEBUG_SE:
                msg = "{} is stating a battle scenario.".format(team.name)
                se_debug(msg, mode="info")

            # Get a level we'll set the mobs to:
            level = tracker.area.tier*20
            minl = max(1, level-3)
            maxl = max(5, level+3+tracker.day)
            level = randint(minl, maxl)

            # raise Exception(mob, tracker.area.mobs)
            for i in xrange(opfor_team_size):
                temp = build_mob(id=mob, level=level)
                temp.controller = BE_AI(temp)
                opfor.add(temp)

            for i in team:
                i.controller = BE_AI(i)

            # Logical battle scenario:
            battle = BE_Core(logical=True)
            store.battle = battle # Making battle global... I need to make sure this is not needed.
            battle.teams.append(team)
            battle.teams.append(opfor)
            battle.start_battle()

            # Add the battle report to log!:
            log.battle_log = list(reversed(battle.combat_log))

            for i in team:
                i.controller = "player"

            tracker.points -= 100*len(team)

            # No death below risk 40:
            if tracker.risk > 40 and dice(tracker.risk):
                for member in team:
                    if member in battle.corpses:
                        tracker.flag_red = True
                        tracker.died.append(member)
                        team.remove(member)

            for mob in opfor:
                if mob in battle.corpses:
                    tracker.mobs_defeated[mob.id] += 1

            if battle.winner == team:
                log.suffix = "{color=[lawngreen]}Victory{/color}"
                for member in team:
                    if member in battle.corpses:
                        continue
                    member.attack += randrange(3)
                    member.defence + randrange(3)
                    member.agility += randrange(3)
                    member.magic += randrange(3)
                    member.exp += exp_reward(member, opfor)

                # Death needs to be handled based off risk factor: TODO:
                # self.txt.append("\n{color=[red]}%s has died during this skirmish!{/color}\n" % member.name)
                temp = "{color=[lawngreen]}Your team won!!{/color}\n"
                log.add(temp)

                if DEBUG_SE:
                    msg = "{} finished a battle scenario. Result: victory".format(team.name)
                    se_debug(msg, mode="info")

                return "victory"
            else: # Defeat here...
                log.suffix = "{color=[red]}Defeat{/color}"
                temp = "{color=[red]}Your team got their asses kicked!!{/color}\n"
                log.add(temp)

                if DEBUG_SE:
                    msg = "{} finished a battle scenario. Result: defeat".format(team.name)
                    se_debug(msg, mode="info")

                return "defeat"

        def setup_basecamp(self, tracker):
            # New type of shit, trying to get teams to coop here...
            area = tracker.obj_area
            team = tracker.team
            teams = [t.team for t in area.trackers if t.state == "setting_up_basecamp"]

            if DEBUG_SE:
                msg = "Team {} is setting up basecamp.".format(team.name)
                se_debug(msg, mode="info")

            # TODO: Make sure this is adapted to building skill(s) once we have it!
            build_power = max(1, tracker.ability/20)

            if len(teams) > 1:
                temp = "Teams: {} are setting up basecamp!".format(", ".join([t.name for t in teams]))
            else:
                temp = "Team {} is setting up basecamp!".format(teams[0].name)
            tracker.log(temp)

            while 1:
                if area.camp_build_points_current >= area.camp_build_points_required:
                    # Team done setting up the encampment:
                    temp = "Encampment is finished! Team is moving onto exploration!"
                    area.camp = True
                    tracker.log(temp)
                    self.env.exit()

                area.camp_build_points_current += build_power
                yield self.env.timeout(5) # We build...

                if not self.env.now % 25:
                    temp = "Basecamp is {} complete!".format(area.camp_build_status)
                    tracker.log(temp)

                if self.env.now >= 99:
                    self.env.exit()

            if DEBUG_SE:
                msg = "Team {} finished setting up basecamp.".format(team.name)
                se_debug(msg, mode="info")

        # AP:
        def convert_AP(self, tracker):
            # Convert teams AP to Job points:
            # The idea here is that teammates will help each other to carry out
            # any task and act as a unit, so we don't bother tracking individual AP.
            team = tracker.team
            AP = 0
            for m in team:
                AP += m.AP
            tracker.points = AP * 100
