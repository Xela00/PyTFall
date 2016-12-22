init -9 python:
    #################################################################
    # UNIQUE BUILDING CLASSES
    # The classes for actual buildings with the customisations they require.
    #
    class CityJail(BaseBuilding):
        """
        The jail where escaped slaves can turn up. May do other things later.
        """
        
        def __init__(self):
            super(CityJail, self).__init__()
            self.worker = None
            self.index = 0
            self.workers_list = list()
            self.auto_sell_captured = False # Do we auto-sell SE captured slaves?
        
        def __contains__(self, girl):
            """
            Checks whether a girl has runaway.
            """
            return girl in self.workers_list
        
        def add_prisoner(self, girl, flag=None):
            """
            Adds a girl to the jail.
            girl = The girl to add.
            """
            if girl not in self:
                if girl in hero.team: hero.team.remove(girl)
                self.workers_list.append(girl)
                
                # Flag to determine how the girl is handled in the jail:
                if flag:
                    girl.set_flag("sentence_type", flag)
                    if flag == "SE_capture":
                        girl.set_flag("days_in_jail", 0)
                
                if self.worker is None:
                    self.worker = girl
                    self.index = 0
        
        def buy_girl(self):
            """
            Buys an escaped girl from the jail.
            """
            if hero.take_ap(1):
                if hero.take_money(self.get_price(), reason="Slave Repurchase"):
                    renpy.play("content/sfx/sound/world/purchase_1.ogg")
                    self.remove_prisoner(self.worker)
                else:
                    renpy.call_screen('message_screen', "You don't have enough money for this purchase!")
            
            else:
                renpy.call_screen('message_screen', "You don't have enough AP left for this action!")
            
            if not self.workers_list:
                renpy.hide_screen("slave_shopping")
        
        def get_price(self):
            """
            Returns the price to retrieve the girl.
            """
            # In case of non-slave girl, use 3000 as base price
            return (self.worker.fin.get_price() or 3000) / 2
        
        def get_whore_price(self):
            """
            Return the whore cost for the girl.
            """
            return self.worker.fin.get_whore_price()
        
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
            self.index = (self.index+1) % len(self.workers_list)
            self.worker = self.workers_list[self.index]
        
        def previous_index(self):
            """
            Sets the previous index for the slavemarket.
            """
            self.index = (self.index-1) % len(self.workers_list)
            self.worker = self.workers_list[self.index]
        
        def remove_prisoner(self, girl, set_location=True):
            """
            Returns a girl to the player.
            girl = The girl to return.
            """
            if girl in self:
                girl.del_flag("sentence_type")
                girl.del_flag("days_in_jail")
                self.workers_list.remove(girl)
                
                if self.workers_list:
                    self.index %= len(self.workers_list)
                    self.worker = self.workers_list[self.index]
                
                else:
                    self.index = 0
                    self.worker = None
                
                if set_location:
                    if schools[TrainingDungeon.NAME] in hero.buildings:
                        girl.location = schools[TrainingDungeon.NAME]
                    else:
                        girl.location = hero
        
        def set_girl(self, girl):
            """
            Sets the girl to be the index for the slavemarket.
            girl = The girl to set.
            """
            if self.workers_list and girl in self.workers_list:
                self.worker = girl
                self.index = self.workers_list.index(self.worker)
        
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
                girl.location = None
                # TODO: What do we do with the girl sold? Let her fall into the void or become availible in SM after a while.
            else:
                renpy.call_screen('message_screen', "You don't have enough AP left for this action!")
            
            if not auto:    
                if not self.workers_list:
                    renpy.hide_screen("slave_shopping")
        
        def next_day(self):
            for i in self.workers_list:
                if i.flag("sentence_type") == "SE_capture":
                    i.mod_flag("days_in_jail")
                    if self.auto_sell_captured:
                        # Auto-selloff through flag set in SE module
                        # TODO: Implement the button in SE!
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
                            hero.give_money(self.get_fees4captured(), reason="Jail Fees")
                            renpy.call_screen('message_screen', "You don't have enough money for upfront payment for Blue's services!")
                else:
                    renpy.call_screen('message_screen', "You don't have enough money!")
            else:
                renpy.call_screen('message_screen', "You don't have enough AP left for this action!")
            
            if not self.workers_list:
                renpy.hide_screen("slave_shopping")
        
    class Apartment(BaseBuilding):
        """Useless class really, but I may require to check for this during interation in the future."""
        #
        # Do we want to remove this to completely replace it with the Training Dungeon?
        # *Alex: Nope, this will be at some point expanded into a Harem-like structure with it's own bonuses. Player may want to get an apartment but never a TD (Like CW for example :D )
        def __init__(self):
            super(Apartment, self).__init__()
            # Once again, for the Items transfer:
            self.status = "slave"
            self.given_items = dict()
            
            # We'll add inventory here at Dark's request.
            self.inventory = Inventory(15)
            
        # Mimicing the show method expected from character classes for items transfer:
        def show(self, *tags, **kwargs):
            return ProportionalScale(self.img, 205, 205)
        
    class Building(NewStyleUpgradableBuilding, NewStyleAdvertableBuilding, DirtyBuilding, FamousBuilding):
        """
        The building that represents Business Buildings.
        """
        
        ACTIONS = ['Prostitute', 'ServiceGirl', 'Rest', 'Stripper', 'Guard']
        
        def __init__(self, *args, **kwargs):
            """
            Creates a new Building.
            maxrank = The maximum rank this brothel can achieve.
            """
            super(Building, self).__init__(*args, **kwargs)
            
            self.fin = Finances(self)
            
            # Stat mod dict:
            # Should be used for recording and displaying information only
            self.stats_mod = {}
            self.nd_events_report = list()
            
            self.maxrank = kwargs.pop("maxrank", 0)
            
            self.baseclients = 2
            self.actions = Building.ACTIONS
            
            # Upgrades
            self.used_upgrade_slots = 0
            self.upgrade_slots = 3
            
            # self.upgrades['bar'] =  {
                # '1': {'id': 1, 'active': False, 'available': False, 'price': 500, 'name': 'Bar', 'desc': 'Serve drinks and snacks to your customers! ',
                      # 'img': 'content/buildings/upgrades/bar.jpg'},
                # '2': {'id': 2, 'active': False, 'available': False, 'price': 200, 'name': 'Draught Beer', 'desc': 'Chilled brew served in cold glassware, like a nectar from gods themselves. ', 
                      # 'img': 'content/buildings/upgrades/beer.jpg'},
                # '3': {'id': 3, 'active': False, 'available': False, 'price': 300, 'name': 'Tapas', 'desc': 'Tasty snacks that are just perfect with cold draught beer. ',
                      # 'img': 'content/buildings/upgrades/tapas.jpg'}
                # }
             
            # self.upgrades['garden'] = {
                # '1': {'id': 1, 'active': False, 'available': False, 'price': 150, 'name': 'Flowerbeds', 'desc': 'Live Flowers for your girls to improve the grim designs of work in brothel. ',
                      # 'img': 'content/buildings/upgrades/flowers.jpg'},
                # '2': {'id': 2, 'active': False, 'available': False, 'price': 500, 'name': 'Garden', 'desc': 'Beautiful garden to relax in for your girls and customers. Will have positive effect on Rest and Costumer Satisfaction',
                      # 'img': 'content/buildings/upgrades/garden.jpg'},
                # '3': {'id': 3, 'active': False, 'available': False, 'price': 1000, 'name': 'Landscape Design', 'desc': 'Create a landscape filled with the most beautiful flora for amusement and enjoyment of your girls and customers alike!',
                      # 'img': 'content/buildings/upgrades/landscape.jpg'}
                # }
             
            # self.upgrades['room_upgrades'] = {
                # '1': {'id': 1, 'active': False, 'available': False, 'price': 400, 'name': 'Improved Interior', 'desc': "Every room in brothel will be decorated in proper fashion! (+1/10 of the price for every room in the brothel)",
                      # 'img': 'content/buildings/upgrades/room.jpg', "room_dependant": True, "room_upgrade": 40},
                # '2': {'id': 2, 'active': False, 'available': False, 'price': 800, 'name': 'Luxury Rooms', 'desc': "Room design farther improved to provide the best atmosphere imaginable! (+1/10 of the price for every room in the brothel)",
                      # 'img': 'content/buildings/upgrades/luxury_room.jpg', "room_dependant": True, "room_upgrade": 40},
                # '3': {'id': 3, 'active': False, 'available': False, 'price': 2000, 'name': 'VIP Rooms', 'desc': "Bit of an overkill if you ask me. Royalty would not look out of place in one of these rooms! (+1/10 of the price for every room in the brothel)",
                      # 'img': 'content/buildings/upgrades/vip_room.jpg', "room_dependant": True, "room_upgrade": 120}
                # }
             
            # self.upgrades['guards'] = {
                # '1': {'id': 1, 'active': False, 'available': False, 'price': 1000, 'name': 'Guard Quarters', 'desc': "Comforable locale for warriors guarding the building. (5 girls max)",
                      # 'img': 'content/buildings/upgrades/guard_qt.jpg', "security_bonus": 30},
                # '2': {'id': 2, 'active': False, 'available': False, 'price': 1500, 'name': 'Training Quarters', 'desc': "Place for your guards to improve their skills when there is nothing else to do. ",
                      # 'img': 'content/buildings/upgrades/training_qt.jpg', "security_bonus": 25},
                # '3': {'id': 3, 'active': False, 'available': False, 'price': 2000, 'name': 'Sparring Quarters', 'desc': "Your guards can harness their skills by safely fighting one another. ",
                      # 'img': 'content/buildings/upgrades/sparring_qt.jpg', "security_bonus": 25}
                # }
             
            # self.upgrades['stripclub'] = {
                # '1': {'id': 1, 'active': False, 'available': False, 'price': 1000, 'name': 'Strip Club', 'desc': 'Skilled and beautiful Strippers are the key to filling your Club and Bar with Costumers! ',
                      # 'img': 'content/buildings/upgrades/strip_club.jpg'},
                # '2': {'id': 2, 'active': False, 'available': False, 'price': 700, 'name': 'Large Podium', 'desc': 'Equip your club with a better podium for your girls to dance on! ',
                      # 'img': 'content/buildings/upgrades/podium.jpg'},
                # '3': {'id': 3, 'active': False, 'available': False, 'price': 2000, 'name': 'Golden Cages', 'desc': 'Girls now can strip inside golden cages, truly a show to behold! ',
                      # 'img': 'content/buildings/upgrades/golden_cage.jpg'}
                # }
             
            # self.upgrades['mainhall'] = {
                # '1': {'id': 1, 'active': False, 'available': False, 'price': 500, 'name': 'Main Hall', 'desc': 'All customers will have to go through this beautiful hall! This can increase reputation, customer satisfaction as well as improve security. ',
                      # 'img': 'content/buildings/upgrades/main_hall.jpg', "security_bonus": 30, "whore_mult": 0.1},
                # '2': {'id': 2, 'active': False, 'available': False, 'price': 700, 'name': 'Reception', 'desc': 'Reception to improve income and customer satisfaction through good organization and service. ',
                      # 'img': 'content/buildings/upgrades/reception.jpg', "security_bonus": 50, "whore_mult": 0.1},
                # '3': {'id': 3, 'active': False, 'available': False, 'price': 1000, 'name': 'Statue of Sex Goddess', 'desc': 'Great way to improve fame and income of your brothel! ',
                      # 'img': 'content/buildings/upgrades/statue_sexgoddess.jpg', "whore_mult": 0.2}
                # }

            # Guard events delimiters
            # self.guardevents = dict(prostituteattackedevents = 0, barbrawlevents = 0)
            
            # ND Report
            self.logged_clients = False
        
        def free_rooms(self):
            """
            Returns amount of free rooms, considering Guard Quarters for Warriors if those are active.
            @Review: Updated:
            """
            return 0
        
        def get_clients(self):
            """
            Get the amount of clients that will visit the brothel the next day.
            """
            self.flag_red = False # Dev Note: This is being set and reset here and only here!
            
            self.txt += "OLD CODE THAT NEEDS TO DIE OFF:\n\n"
            
            if not self.fame and not self.rep and self.hasattr('toggle_advert') and not adverts['Sign'].active:
                no_clients = True
                self.flag_red = True
            else:
                no_clients = False
            
            clients = self.baseclients*int(round(self.mod*1.5))
            if config.debug:
                if not self.logged_clients:
                    self.txt += "\n Adding 10 Clients in the debug mode!"
                clients = clients + 10
            
            if not self.logged_clients and no_clients:
                self.txt += "{color=[red]}Noone came to your brothel today... You should at least put up a sign!{/color}"
                self.logged_clients = True
                return 0
            
            elif not self.logged_clients:
                self.txt += "%d clients came to brothel just because its there... " % clients
            
            if not no_clients:
                add_clients = int(self.fame*0.2)
                
                if add_clients and not self.logged_clients:
                    self.txt += "%d because of it's Fame... " % add_clients
                
                clients += add_clients
                
                # Adding bonuses for girls in this brothel
                gfamebonus = 0
                
                for girl in self.get_girls(["Guard", "AutoRest", "Rest"], True): gfamebonus += 1 + int(girl.fame/20)
                
                if not self.logged_clients and gfamebonus:
                    self.txt += "and another %d attracted by your girlz :) \n" % gfamebonus
                
                clients = clients + gfamebonus
                
                self.logged_clients = True
            
            #TODO: Add girl's customer-magnet traits.
            if no_clients:
                return 0
            
            else:
                return clients
        
        def get_upkeep(self):
            """
            Get the daily upkeep.
            """
            pass
        
        def create_customer(self, name=""):
            """
            Returns a customer for this brothel.
            If name is an empty string, a random customer is returned.
            If name is given, the returning customer with that name is returned
            by this method. A NameError will be raised if the given name is not
            associated with a returning customer.
            @ Review: TODO: Move this to a function?
            """
            if name:
                raise NotImplementedError("Returning customers are not implemented yet")

            # determine gender of random customer
            gender = choice(['male', 'male', 'male', 'male', "male", 'female', "female"])
            
            # determine caste of random customer 
            if self.rep < 50: caste = choice(['Peasant', 'Merchant'])
            elif 50 <= self.rep <= 150: caste = choice(['Peasant', 'Merchant', 'Nomad'])
            elif 151 <= self.rep <= 400: caste = choice(['Nomad', 'Merchant', 'Wealthy Merchant'])
            elif 401 <= self.rep <= 600:caste = choice(['Merchant', 'Wealthy Merchant', 'Clerk'])
            elif 601 <= self.rep <= 800: caste = choice(['Wealthy Merchant', 'Clerk', 'Noble'])
            else: caste = choice(['Clerk', 'Noble', 'Royal'])
            
            # create random customer
            customer = build_client(gender=gender, caste=caste, level=randint(2, 70))
            
            # @ Review: Jobs, Traits and other should plainly be added to likes and dislikes. 
            # if customer.gender == 'female' and dice(60): customer.favtraits.add(choice(['Lesbian', 'Bisexual']))
            # if not customer.favtraits and dice(50):
                # customer.favtraits.add(choice(['Great Arse', 
                                                               # 'Nymphomaniac', 'Sexy Air', 'Great Figure',
                                                               # 'Abnormally Large Boobs', 'Not Human', 'Meek',
                                                               # 'Nerd', 'Famous',
                                                               # 'Well-mannered', 'Long Legs',
                                                               # 'Kind', 'Energetic', 'Shy',
                                                               # 'Average Boobs', 'Strange Eyes', 'MILF', 'Sensitive',
                                                               # 'Protective', 'Serious', 'Noble', 'Tomboy',
                                                               # 'Tough', 'Athletic', 'Lolita', 'Exhibitionist',
                                                               # 'Small Boobs', 'Aggressive', 'Outgoing', 'Big Boobs', 'Elegant']))
            # if not customer.favtraits and dice(20):
                # customer.favtraits.add(choice(['Genius',  'Smart', 'Ill-mannered', 'Merciless', 'Yandere', 'Fearless', 'Kuudere',  'Masochist',
                                               # 'Dandere', 'Clumsy',  'Old Scars', 'Pessimist', 'Sadistic', 'Heavy Drinker', 'Tsundere', 'Optimist', 'Impersonal']))
            # if not customer.favtraits and dice(10):
                # customer.favtraits.add(choice(['Psychic', 'Artificial Body', 'Adventurous', 'Broken Will', 'Frigid', 'Silly', 'Fragile', 'Alien', 'Manly', 'Mind Fucked']))
            
            return customer
        
        def next_day(self):
            """
            Solves the next day logic for the brothel.
            TODO: Split this over parent classes!
            """
            # Local vars
            type = 'buildingreport'
            img = self.img
            
            # txt = self.txt # We no longer store any data previous to the reports list and use vbox + interation instead of one huge text.
            txt = self.nd_events_report
            
            evtlist = []
            char = None
            tmodrep = 0 # Total of rep changed on next day, girl's mod are not included here.
            tmodfame = 0 # Total of fame, same rules.
            spentcash = 0
            
            # Taking care of security rating:
            # Without logging for now
            # TODO: Move to WarriorQuarters!
            # if self.upgrades['mainhall']['2']['active']: self.security_rating -= self.get_clients()
            # elif self.upgrades['mainhall']['1']['active']: self.security_rating -= self.get_clients() * 2
            self.security_rating -= self.total_clients * 3
            if self.security_rating < 0: self.security_rating = 0
            
            security_power = 0
            guardslist = self.get_girls("Guard")
            
            for guard in guardslist:
                security_power += (guard.attack + guard.defence + guard.magic) / 3
            
            self.security_rating += int(security_power * ((self.security_presence/10)+1))
            if self.security_rating < 0: self.security_rating = 0
            if self.security_rating > 1000: self.security_rating = 1000
            
            txt.append("Security Rating in now %d out of 1000, you currently have %d guards on duty with security presence of %d %%. \n\n"% (self.security_rating, len(guardslist), self.security_presence))  
            
            # Effects from upgrades:
            # TODO: Upgrade to new style!
            # if self.upgrades['mainhall']['3']['active']:
                # txt += "Statue in your main hall streads mystical energy, your brothel will soon be known throught out the whole word! \n"
                # self.modfame(1)
                # tmodrep += 1
                # self.modrep(1)
                # tmodfame += 1
            
            # if self.upgrades['mainhall']['2']['active']:
                # txt += "Clients loved having a reception where they could enquire about girls, prices and possibilieties. \n"
                # repinc = choice([0, 0, 1])
                # self.modrep(repinc)

            # Applies effects of adverticement:
            if self.can_advert:

                for advert in self.adverts:

                    if advert['active']:
                        if 'fame' in advert:
                            modf = randint(*advert['fame'])
                            self.modfame(modf)
                            tmodfame = tmodfame + modf

                        if 'reputation' in advert:
                            modr = randint(*advert['reputation'])
                            self.modreputation(modr)
                            tmodrep = tmodrep + modr

                        spentcash = spentcash + advert['upkeep']

                        if advert['name'] == 'Celebrity':
                            advert['active'] = False
                            txt.append("A celebrity came into your brothel, raising it's reputation by %d and fame by %d\n" % (modr,modf))

            
            txt.append("In total you got a bill of %d Gold in advertising fees, reputation was increased through advertising by %d, fame by %d." % (spentcash, tmodfame, tmodrep))
            
            if spentcash and not hero.take_money(spentcash, reason="Building Ads"):
                rep_hit = max(10, spentcash/10)
                self.modrep(-rep_hit)
                txt.append("{color=[red]}And yet, you did not have enought money to pay your advertisers! They rook it out on you by promoting %s as a shitty dump...{/color}" % self.name)
                self.flag_red = True
            
            self.fin.log_expense(spentcash, "Ads")
            
            evt = NDEvent()
            evt.type = type
            evt.red_flag = self.flag_red
            evt.loc = self
            evt.char = char
            evt.img = img
            evt.txt = txt
            NextDayEvents.append(evt)
            
            # Resetting all logs and relays:
            # Relay resets:
            # for key in self.servicer:
                # self.servicer[key] = False
            
            # Reset
            # self.guardevents = dict(prostituteattackedevents = 0, barbrawlevents = 0)
            self.nd_events_report = list()
            self.txt = ""
            self.logged_clients = False
        
        def nd_log_income(self):
            """
            Log the next day income for this building.
            """
            self.fin.next_day()
        
    
    class TrainingDungeon(UpgradableBuilding):
        """
        Building that represents the hero's dungeon to train girls in.
        """
        
        NAME = "Training Dungeon"
        
        def __init__(self, courses):
            """
            Creates a new TrainingDungeon.
            """
            super(TrainingDungeon, self).__init__(id=self.NAME, name=self.NAME, desc="A personal dungeon for training and punishing slaves.",
                                                  price=7500, minrooms=5, maxrooms=50, roomprice=500, upgrade_slots=18)
            
            self.img = "content/buildings/dungeon.jpg"
            
            self.actions = ["Guard", "Train", "Take Course", "Search"]
            
            self.fin = Finances(self)
            self.income = 0
            
            # Dict
            self.all_courses = courses
            
            # List
            self.courses = [courses[i] for i in courses]
            
            self.events_relay = {
                "runaway": [0, 0], # successful, prevented
                "disobey": [0, 0], # successful, prevented
                "obey": [0, 0], # from training success, random
                "finish": [0, 0] # end of course, no longer eligible 
            }
            
            self.one_off_events = list()
            
            # Give the girls bonus' to obedience
            self.upgrades["Rewards"] = {
                "1": {"id": 1, "active": False, "available": True, "price": 10, "name": "Comfortable Beds", "desc": "Give the girls a comfortable place to rest during training.",
                      "img": "content/buildings/dungeon/girlhouse.jpg"},
                "2": {"id": 2, "active": False, "available": True, "price": 10, "name": "Garden", "desc": "Create a secured garden to allow the girls outside while training.",
                      "img": "content/buildings/dungeon/garden.jpg"},
                "3": {"id": 3, "active": False, "available": True, "price": 10, "name": "Baths", "desc": "Allow the girls to wash off after training.",
                      "img": "content/buildings/dungeon/bath.jpg"}
            }
            
            # Give the girls penalties to disobedience
            self.upgrades["Punishments"] = {
                "1": {"id": 1, "active": False, "available": True, "price": 10, "name": "Cells", "desc": "Give the trouble makers barren cells to lower their activity.",
                      "img": "content/buildings/dungeon/cells.jpg"},
                "2": {"id": 2, "active": False, "available": True, "price": 10, "name": "Stocks", "desc": "Ensure that those thinking of disobeying know the consequences.",
                      "img": "content/buildings/dungeon/stocks.jpg"},
                "3": {"id": 3, "active": False, "available": True, "price": 10, "name": "Whips and Chains", "desc": "Allow those working in the dungeon some respite from their hard work.",
                      "img": "content/buildings/dungeon/chains.png"}
            }
            
            # Give the girls penalties to running away
            self.upgrades["Security"] = {
                "1": {"id": 1, "active": False, "available": True, "price": 10, "name": "Manacles", "desc": "Helps prevent the escape of slaves by restricting their movement.",
                      "img": "content/buildings/dungeon/manacles.jpg", "security_bonus": 30},
                "2": {"id": 2, "active": False, "available": True, "price": 10, "name": "Better Locks", "desc": "Ensure that the locks on all the doors are sturdy and harder to break.",
                      "img": "content/buildings/dungeon/key.png", "security_bonus": 25},
                "3": {"id": 3, "active": False, "available": True, "price": 10, "name": "Guard House", "desc": "Allow the guards a place to rest during their off-hours.",
                      "img": "content/buildings/dungeon/guardhouse.jpg", "security_bonus": 25}
            }
            
            # Give the trainers bonus' to their ability to train (+Skill, +Knowledge)
            self.upgrades["Trainers"] = {
                "1": {"id": 1, "active": False, "available": True, "price": 10, "name": "Personal Rooms", "desc": "Give the trainers personal rooms to allow them to rest better.",
                      "img": "content/buildings/dungeon/trainerhouse.jpg"},
                "2": {"id": 2, "active": False, "available": True, "price": 10, "name": "Training Rooms", "desc": "Allow the trainers to use dedicated training rooms.",
                      "img": "content/buildings/dungeon/classroom.png"},
                "3": {"id": 3, "active": False, "available": True, "price": 10, "name": "Equipment", "desc": "Furnish the rooms with specialised equipment.",
                      "img": "content/buildings/dungeon/equipment.jpg"},
            }
            
            # Give bonus' to exp
            self.upgrades["Equipment"] = {
                "1": {"id": 1, "active": False, "available": True, "price": 10, "name": "Motivational Aids", "desc": "Equipment to help motivate the girls when training.",
                      "img": "content/buildings/dungeon/motivation.png"},
                "2": {"id": 2, "active": False, "available": True, "price": 10, "name": "Relaxation Aids", "desc": "Equipment to help motivate the girls after training.",
                      "img": "content/buildings/dungeon/relaxation.jpg"},
                "3": {"id": 3, "active": False, "available": True, "price": 10, "name": "Punishment Aids", "desc": "Equipment to help prevent girls from disobeying.",
                      "img": "content/buildings/dungeon/punishment.jpg"},
            }
            
            # Give the player benefits (+AP)
            self.upgrades["Housing"] = {
                "1": {"id": 1, "active": False, "available": True, "price": 10, "name": "Bedroom Refurbishment", "desc": "Refurbish your bedroom to better rest yourself during the night.",
                      "img": "content/buildings/dungeon/bedroom.jpg"},
                "2": {"id": 2, "active": False, "available": True, "price": 10, "name": "Facilities Refurbishment", "desc": "Refurbish your facilities to better improve your quality of living.",
                      "img": "content/buildings/dungeon/facilities.jpg"},
                "3": {"id": 3, "active": False, "available": True, "price": 10, "name": "Decoration", "desc": "Decorate your house to make your home more pleasent to live in.",
                      "img": "content/buildings/dungeon/decoration.jpg"},
            }
        
        @property
        def available(self):
            """
            Whether this building is available. Used in training screen.
            """
            return self in hero.buildings
        
        def get_girls(self, type=None):
            """
            Override get_girls to include proper trainer support.
            """
            if type == "Training":
                return [girl_training_with(girl) for girl in super(TrainingDungeon, self).get_girls("Course")]
            
            else:
                return super(TrainingDungeon, self).get_girls(type)
        
        def get_upkeep(self):
            """
            The upkeep cost of the building.
            """
            pass
        
        @property
        def is_school(self):
            """
            Whether or not this building is a school. Used in training screen.
            """
            return False
        
        def log_income(self, char, value):
            """
            Logs the training cost.
            char = The character who the income is being spent for.
            value = The amount being spent.
            """
            hero.take_money(value, reason=self.name)
            self.income += value
            char.fin.log_cost(value, "Training")
        
        def mod_disobey(self):
            """
            The modifier for disobeying.
            """
            return self.get_upgrade_mod("Punishments") / len(self.upgrades["Punishments"])
        
        def mod_exp(self):
            """
            The modifier for experience.
            """
            return self.get_upgrade_mod("Equipment") / len(self.upgrades["Equipment"])
        
        def mod_housing(self):
            """
            The modifier for the hero's AP.
            """
            return self.get_upgrade_mod("Housing") / len(self.upgrades["Housing"])
        
        def mod_obey(self):
            """
            The modifier for obeying.
            """
            return self.get_upgrade_mod("Rewards") / len(self.upgrades["Rewards"])
        
        def mod_runaway(self):
            """
            The modifier for running away.
            """
            return self.get_upgrade_mod("Security") / len(self.upgrades["Security"])
        
        def mod_skill(self):
            """
            The modifier for trainer ability.
            """
            return self.get_upgrade_mod("Trainers") / len(self.upgrades["Trainers"])
        
        def next_day(self):
            """
            Solves the next day logic for the training girls.
            """
            # Logic
            type = "schoolndreport"
            img = im.Scale(self.img, int(config.screen_width*0.6), int(config.screen_height*0.8))
            txt = "%s Report: \n"%self.name
            evtlist = []
            char = None
            
            girls = self.get_girls("Course")
            
            if not girls:
                txt += "Your dungeon is currently going unused, maybe some of your girls require training? \n"
            
            else:
                txt += "You currently have %d %s training in your dungeon. \n"%(len(girls), plural("girl", len(girls)))
            
            # Checking if girls have completed their courses
            for girl in girls:
                course = char_is_training(girl)
                trainer = girl_training_with(girl)
                
                if course.daysLeft(girl) > 0:
                    girl_training_left.set(girl, -1, True) # Decrease
                
                else:
                    stop_training(girl)
                    self.events_relay["finish"][0] += 1
                    
                    # Final stat increase
                    course.primary(girl, mult=course.get_scaling(girl))
                    course.secondary(girl, mult=course.get_scaling(girl))
                    
                    # Bonus stat increase
                    if dice(20) and course.primary.mod is not None:
                        for stat in course.primary.mod:
                            girl.stats.max[stat] += choice([0, 1])
                    
                    txt += "\n\n{color=[lawngreen]}%s has completed her %s training. \n{/color}"%(girl.name, course.type)
            
            # Security
            self.security_rating -= len(girls) * (1+self.mod_runaway())
            if self.security_rating < 0: self.security_rating = 0
            
            security_power = 0
            guards = self.get_girls("Guard")
            for guard in guards: security_power += (guard.attack + guard.defence + guard.magic) / 3
            
            self.security_rating += int(security_power * ((self.security_presence/10)+1))
            
            if self.security_rating < 0: self.security_rating = 0
            elif self.security_rating > 1000: self.security_rating = 1000
            
            txt += "Security Rating is now %d out of 1000, you currently have %d guards on duty with security presence of %d%%. \n\n"% (self.security_rating, len(guards), self.security_presence)
            
            # Event summery
            for i in self.events_relay:
                j,k = self.events_relay[i]
                
                if i == "obey":
                    if j > 0: txt += "%d %s obeyed their trainers perfectly. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s did extra well because of the facilities and equipment. \n"%(k, plural("girl", k))
                
                elif i == "disobey":
                    if j > 0: txt += "%d %s disobeyed their trainers without punishment. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s disobeyed their trainers and were punished for it. \n"%(k, plural("girl", k))
                
                elif i == "runaway":
                    if j > 0: txt += "%d %s ran away from their lessons, wasting their day. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s tried to run away, but were caught and punished. \n"%(k, plural("girl", k))
                
                elif i == "finish":
                    if j > 0: txt += "%d %s have completed their training. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s are no longer eligible for their training. \n"%(k, plural("girl", k))
                
                self.events_relay[i][0] = 0
                self.events_relay[i][1] = 0
            
            # Do one off events
            while self.one_off_events:
                NextDayEvents.append(self.one_off_events.pop())
            
            evt = NDEvent()
            evt.type = type
            evt.char = char
            evt.img = img
            evt.txt = txt
            NextDayEvents.append(evt)
        
    
    class School(BaseBuilding):
        """
        Building that represents the school.
        """
        
        #"primary": [1,1,1,0,1,1,1,1,1,1,1,1,2,0],
        #"secondary": [0,0,0,1,1,1,1,1,1,0,0,0,1,1,1,1,0,0,0,0,0,2],
        #"tprimary": [1,1,1,0,1,1,1,1,1,1,1,1,2,3],
        #"tsecondary": [0,0,0,1,1,1,1,1,1,0,0,0,1,1,1,1,0,0,0,0,2,2],
        #"sprimary": [1,1,0,0,1,1,1,1,1,1,0,1,0,2],
        #"ssecondary": [0,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,0,0,0,0,1,2],
        
        def __init__(self, id="-PyTFall Educators-", image="content/schools/school.jpg", primary=0, secondary=0, skillPrimary=None, skillSecondary=None, options=None, file=None):
            """
            Creates a new schoool.
            id = The name of the school.
            image = The image for the school.
            primary = The primary stat increase.
            secondary = The secondary stat increase.
            options = The courses available.
            file = The json file this school was loaded from.
            """
            super(School, self).__init__(id=id, name=id)
            
            self.img = image
            
            self.primary = primary
            self.secondary = secondary
            self.skill_primary = skillPrimary or primary
            self.skill_secondary = skillSecondary or secondary
            
            self.fin = Finances(self)
            self.income = 0
            
            # Dict
            self.all_courses = options
            
            # List
            self.courses = []
            
            self.income = 0
            
            self.events_relay = {
                "runaway": [0, 0], # successful, prevented
                "disobey": [0, 0], # successful, prevented
                "obey": [0, 0], # from training success, random
                "finish": [0, 0] # end of course, no longer eligible
            }
            
            # For one off events
            self.one_off_events = list()
            
            # For debugging purposes
            self.file = None
        
        @property
        def available(self):
            """
            Whether this building is available.
            """
            return True
        
        def create_course(self):
            """
            Creates a random course from the courses dictionary.
            """
            key = choice(self.all_courses.keys())
            course = deepcopy(self.all_courses[key])
            
            x = dict()
            for i in course["primary"]:
                if i in PytCharacter.SKILLS: x[i] = self.skill_primary
                else: x[i] = self.primary
            
            course["primary"] = PytStatChanges(mod=x)
            
            x = dict()
            for i in course["secondary"]:
                if i in PytCharacter.SKILLS: x[i] = self.skill_secondary
                else: x[i] = self.secondary
            
            course["secondary"] = PytStatChanges(mod=x)
            
            course = SchoolLesson(key, **course)
            
            self.courses.append(course)
        
        @property
        def is_school(self):
            """
            Whether or not this building is a school.
            """
            return True
        
        def log_income(self, char, value):
            """
            Logs the schools income.
            char = The character who the income is being spent for.
            value = The amount being spent.
            """
            hero.take_money(value, reason=self.name)
            self.income += value
            char.fin.log_cost(value, "Training")
        
        def next_day(self):
            """
            Solves the next day notifications for schooling.
            """
            # Logic
            type = "schoolndreport"
            img = im.Scale(self.img, int(config.screen_width*0.6), int(config.screen_height*0.8))
            txt = "%s Report: \n"%self.name
            evtlist = []
            char = None
            
            girls = [girl for girl in hero.chars if girl.location == self.name]
            
            if not girls:
                txt += "Exellent courses are availible today! Remember our Motto: Education is Gold! \n"
            
            else:
                txt += choice(["You currently have %d girls training with us! \n" % len(girls), "Exellent courses are availible today! Remember our Motto: Education is Gold! \n"])
            
            # Add courses
            tempval = len(self.courses)
            if len(self.courses) < 10:
                self.create_course()
            
            if dice(50):
                if len(self.courses) < randint(10, 20):
                    self.create_course()
            
            if dice(10):
                if len(self.courses) < 30:
                    self.create_course()
            
            if tempval < len(self.courses):
                txt += "We inform you about fresh courses starting today. Please check in with us if you are interested. \n"
            
            # Checking if girl has completed the course:
            for course in self.courses:
                for girl in girls:
                    if str(girl) in course.chars:
                        cdays = int(course.duration*0.7)
                        
                        if course.chars[str(girl)] >= cdays:
                            if str(girl) in course.complete:
                                pass
                            
                            else:
                                course.complete[str(girl)] = True
                                self.events_relay["finish"][0] += 1
                                
                                # Final increase
                                course.primary(girl, mult=course.get_scaling(girl))
                                course.secondary(girl, mult=course.get_scaling(girl))
                                
                                if dice(20):
                                    for stat in course.primary.mod:
                                        girl.stats.max[stat] += choice([0, 1])
                                
                                txt += "\n\n{color=[lawngreen]}%s has successfully completed %s and got a nice extra bonus to her stats! \n{/color}"%(girl.name, course.action)
            
            # Day Count
            for course in self.courses:
                course._daysLeft -= 1
            
            # End courses and remove girls
            for course in self.courses:
                if course.daysLeft() <= 0:
                    for girl in girls:
                        if girl_course_id(girl) == course.id:
                            txt += "Course that %s is attending is at it's end! "%girl.name
                            stop_training(girl)
                    
                    self.courses.remove(course)
            
            # Event summery
            for i in self.events_relay:
                j,k = self.events_relay[i]
                
                if i == "obey":
                    if j > 0: txt += "%d %s obeyed their trainers perfectly. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s did extra well because of the facilities and equipment. \n"%(k, plural("girl", k))
                
                elif i == "disobey":
                    if j > 0: txt += "%d %s disobeyed their trainers without punishment. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s disobeyed their trainers and were punished for it. \n"%(k, plural("girl", k))
                
                elif i == "runaway":
                    if j > 0: txt += "%d %s ran away from their lessons, wasting their day. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s tried to run away, but were caught and punished. \n"%(k, plural("girl", k))
                
                elif i == "finish":
                    if j > 0: txt += "%d %s have completed their training. \n"%(j, plural("girl", j))
                    if k > 0: txt += "%d %s are no longer eligible for their training. \n"%(k, plural("girl", k))
                
                self.events_relay[i][0] = 0
                self.events_relay[i][1] = 0
            
            # Do one off events
            while self.one_off_events:
                NextDayEvents.append(self.one_off_events.pop())
            
            evt = NDEvent(type=type, txt=txt, img=img, char=char)
            NextDayEvents.append(evt)
