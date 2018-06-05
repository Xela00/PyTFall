init -9 python:
    #################################################################
    # UNIQUE BUILDING CLASSES
    # The classes for actual buildings with the customizations they require.
    #
    class CityJail(BaseBuilding):
        """
        The jail where escaped slaves can turn up. May do other things later.
        """

        # TODO lt: Needs recoding!

        def __init__(self):
            super(CityJail, self).__init__()
            self.focused = None
            self.index = 0
            self.chars_list = []
            self.auto_sell_captured = False # Do we auto-sell SE captured slaves?

        def __contains__(self, char):
            return char in self.chars_list

        def add_prisoner(self, char, flag=None):
            """Adds a char to the jail.

            char: Character to throw into Jail
            flag: Sentence type (reason to put in Jail)
            """
            if char not in self:
                if char in hero.team:
                    hero.team.remove(char)
                self.chars_list.append(char)

                # Flag to determine how the girl is handled in the jail:
                if flag:
                    char.set_flag("sentence_type", flag)
                    if flag == "SE_capture":
                        char.set_flag("days_in_jail", 0)

                if self.focused is None:
                    self.focused = char
                    self.index = 0

        def buy_girl(self):
            """Buys an escaped girl from the jail.
            """
            if hero.take_ap(1):
                if hero.take_money(self.get_price(), reason="Slave Repurchase"):
                    renpy.play("content/sfx/sound/world/purchase_1.ogg")
                    self.remove_prisoner(self.worker)
                else:
                    renpy.call_screen('message_screen', "You don't have enough money for this purchase!")

            else:
                renpy.call_screen('message_screen', "You don't have enough AP left for this action!")

            if not self.chars_list:
                renpy.hide_screen("slave_shopping")

        def get_price(self):
            """
            Returns the price to retrieve the girl.
            """
            # In case of non-slave girl, use 3000 as base price
            return (self.worker.fin.get_price() or 3000) / 2

        def get_upkeep(self):
            """
            Return the upkeep cost for the girl.
            """
            return self.worker.fin.get_upkeep()

        @property
        def girlfin(self):
            """
            The property to return the proper financial data for the girl.
            """
            return self

        def next_index(self):
            """
            Sets the next index for the slavemarket.
            """
            self.index = (self.index+1) % len(self.chars_list)
            self.worker = self.chars_list[self.index]

        def previous_index(self):
            """
            Sets the previous index for the slavemarket.
            """
            self.index = (self.index-1) % len(self.chars_list)
            self.worker = self.chars_list[self.index]

        def remove_prisoner(self, char, set_location=True):
            """
            Returns an actor to the player.
            char = The char to return.
            """
            if char in self:
                char.del_flag("sentence_type")
                char.del_flag("days_in_jail")
                self.chars_list.remove(char)

                if self.chars_list:
                    self.index %= len(self.chars_list)
                    self.worker = self.chars_list[self.index]
                else:
                    self.index = 0
                    self.worker = None

                if set_location:
                    if False: #schools[TrainingDungeon.NAME] in hero.buildings:
                        char.location = schools[TrainingDungeon.NAME]
                        char.home = schools[TrainingDungeon.NAME]
                    else:
                        char.home = locations["Streets"]
                        char.action = None
                        char.workplace = None

        def set_girl(self, girl):
            """
            Sets the girl to be the index for the slavemarket.
            girl = The girl to set.
            """
            if self.chars_list and girl in self.chars_list:
                self.worker = girl
                self.index = self.chars_list.index(self.worker)

        # Deals with girls captured during SE:
        def sell_captured(self, girl=None, auto=False):
            # Flat price of 1500 Gold - the fees:
            """
            Sells off captured girl from the jail.
            auto: Auto Selloff during next day.
            """
            if not girl:
                girl = self.worker

            if auto or hero.take_ap(1):
                if not auto:
                    renpy.play("content/sfx/sound/world/purchase_1.ogg")
                hero.add_money(1500 - self.get_fees4captured(girl), "SlaveTrade")
                self.remove_prisoner(girl)
                girl.location = pytfall.sm
                girl.home = pytfall.sm
                girl.action = None
            else:
                renpy.call_screen('message_screen', "You don't have enough AP left for this action!")

            if not auto:
                if not self.chars_list:
                    renpy.hide_screen("slave_shopping")

        def next_day(self):
            for i in self.chars_list:
                if i.flag("sentence_type") == "SE_capture":
                    i.mod_flag("days_in_jail")
                    if self.auto_sell_captured:
                        # Auto-selloff through flag set in SE module
                        # TODO se: Implement the button in SE!
                        self.sell_captured(auto=True)
                        pytfall.temp_text.append("Jail keepers sold off: {color=[red]}%s{/color}!" % i.name)
                    if i.flag("days_in_jail") > 20:
                        # Auto-Selloff in case of 20+ days:
                        self.sell_captured(auto=True)
                        pytfall.temp_text.append("Jail keepers sold off: {color=[red]}%s{/color}!" % i.name)

        def get_fees4captured(self, girl=None):
            # 200 for registration with city hall + 30 per day for "rent"
            if not girl:
                girl = self.worker
            return 200 + girl.flag("days_in_jail") * 30

        def retrieve_captured(self, direction=None):
            """
            Retrieve a captured character (during SE).
            We handle simple sell-off in a different method (self.sell_captured)
            """
            if hero.take_ap(1):
                if hero.take_money(self.get_fees4captured(), reason="Jail Fees"):
                    renpy.play("content/sfx/sound/world/purchase_1.ogg")
                    self.worker.del_flag("sentence_type")
                    self.worker.del_flag("days_in_jail")
                    if direction == "STinTD":
                        self.remove_prisoner()
                    elif direction == "Blue":
                        if hero.take_money(2000, reason="Blue's Fees"):
                            pytfall.sm.blue_girls[self.worker] = 0
                            self.remove_prisoner(set_location=False)
                        else:
                            hero.add_money(self.get_fees4captured(), reason="Jail Fees")
                            renpy.call_screen('message_screen', "You don't have enough money for upfront payment for Blue's services!")
                else:
                    renpy.call_screen('message_screen', "You don't have enough money!")
            else:
                renpy.call_screen('message_screen', "You don't have enough AP left for this action!")

            if not self.chars_list:
                renpy.hide_screen("slave_shopping")


    class Building(UpgradableBuilding, AdvertableBuilding, FamousBuilding, BuildingStats):
        """
        The building that represents Business Buildings.
        """
        def __init__(self, *args, **kwargs):
            """
            Creates a new Building.
            # maxrank = The maximum rank this brothel can achieve.
            """
            super(Building, self).__init__(*args, **kwargs)
            BuildingStats.__init__(self)

            self.fin = Finances(self)

            # ND Report
            self.nd_events_report = list()
            self.logged_clients = False

        def next_day(self):
            """
            Solves the next day logic for the Building.
            """
            # Local vars
            type = 'buildingreport'
            img = self.img

            txt = self.nd_events_report

            evtlist = []
            char = None
            tmodrep = 0 # Total of rep changed on next day, girl's mod are not included here.
            tmodfame = 0 # Total of fame, same rules.
            spentcash = 0

            # Applies effects of advertisements:
            if self.can_advert:
                for advert in self.adverts:
                    if advert['active']:
                        if 'fame' in advert:
                            modf = randint(*advert['fame'])
                            self.modfame(modf)
                            tmodfame += modf
                        if 'reputation' in advert:
                            modr = randint(*advert['reputation'])
                            self.modrep(modr)
                            tmodrep += modr

                        spentcash += advert['upkeep']
                        if advert['name'] == 'Celebrity':
                            advert['active'] = False
                            txt.append("A celebrity came into your building, raising it's reputation by %d and fame by %d\n" % (modr, modf))

                txt.append("In total you got a bill of %d Gold in advertising fees, reputation was increased through advertising by %d, fame by %d." % (spentcash, tmodrep, tmodfame))

                if spentcash and not hero.take_money(spentcash, reason="Building Ads"):
                    rep_hit = max(10, spentcash/10)
                    self.modrep(-rep_hit)
                    txt.append("{color=[red]}And yet, you did not have enough money to pay your advertisers! They took it out on you by promoting %s as a shitty dump...{/color}" % self.name)
                    self.flag_red = True

                self.fin.log_expense(spentcash, "Ads")

            charmod = self.nd_log_stats()

            evt = NDEvent()
            evt.type = type
            evt.charmod = charmod
            evt.red_flag = self.flag_red
            evt.loc = self
            evt.char = char
            evt.img = img
            evt.txt = txt
            NextDayEvents.append(evt)

            self.nd_events_report = list()
            self.logged_clients = False

        def nd_log_income(self):
            """
            Log the next day income for this building.
            """
            self.fin.next_day()
