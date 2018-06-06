init python:
    # For now a dedicated sorting funcs, maybe this should be turned into something more generic in the future?
    def all_chars_for_se():
        # We expect a global var building to be set for this!
        return [w for w in building.get_workers() if w not in all_idle_explorers()]

    def all_idle_explorers():
        # returns a list of all idle characters that are set exploration teams but not exploring:
        # This may be an overkill cause we should really remove workers from teams when we change their locations!
        idle_explorers = set()
        for building in hero.buildings:
            if isinstance(building, UpgradableBuilding):
                fg = building.get_business("fg")
                if fg:
                    idle_explorers = idle_explorers.union(fg.idle_explorers())
        return idle_explorers

    class CharsSortingForGui(_object):
        """Class we use to sort and filter character for the GUI.

        - Reset is done by a separate function we bind to this class.
        """
        def __init__(self, reset_callable, container=None):
            """
            reset_callable: a funcion to be called without arguments that would return a full, unfiltered list of items to be used as a default.
            container: If not None, we set this contained to self.sorted every time we update. We expect a list with an object and a field to be used with setattr.
            """
            self.reset_callable = reset_callable
            self.target_container = container
            self.sorted = list()
            self.status_filters = set()
            self.action_filters = set()
            self.class_filters = set()
            self.location_filters = set()
            self.home_filters = set()
            self.work_filters = set()

            self.sorting_order = None

        def clear(self):
            self.update(self.reset_callable())
            self.status_filters = set()
            self.action_filters = set()
            self.class_filters = set()
            self.location_filters = set()
            self.home_filters = set()
            self.work_filters = set()

        def update(self, container):
            self.sorted = container
            if self.target_container:
                setattr(self.target_container[0], self.target_container[1], container)

        def filter(self):
            filtered = self.reset_callable()

            # Filters:
            if self.status_filters:
                filtered = [c for c in filtered if c.status in self.status_filters]
            if self.action_filters:
                filtered = [c for c in filtered if c.action in self.action_filters]
            if self.class_filters:
                filtered = [c for c in filtered if c.traits.basetraits.intersection(self.class_filters)]
            if self.location_filters:
                filtered = [c for c in filtered if c.location in self.location_filters]
            if self.home_filters:
                filtered = [c for c in filtered if c.home in self.home_filters]
            if self.work_filters:
                filtered = [c for c in filtered if c.workplace in self.work_filters]

            # Sorting:
            if self.sorting_order == "alphabetical":
                filtered.sort(key=attrgetter("name"))
            elif self.sorting_order == "level":
                filtered.sort(key=attrgetter("level"))

            self.update(filtered)

label building_management:
    python:
        # Reset screen settings, we do this only if we left this screen directly (No jump to char profile/equip)
        if reset_building_management:
            reset_building_management = False
            bm_mid_frame_mode = "building"
            bm_mid_frame_focus = None
            bm_exploration_view_mode = "explore"
            selected_log_area = None

    python:
        # Some Global Vars we use to pass data between screens:
        if hero.upgradable_buildings:
            try:
                index = index
            except:
                index = 0

            if index >= len(hero.upgradable_buildings):
                index = 0

            # Looks pretty ugly... this might be worth improving upon just for the sake of esthetics.
            building = hero.upgradable_buildings[index]
            char = None
            workers = CoordsForPaging(all_chars_for_se(), columns=6, rows=3,
                            size=(80, 80), xspacing=10, yspacing=10, init_pos=(56, 15))
            fg_filters = CharsSortingForGui(all_chars_for_se)
            fg_filters.status_filters.add("free")
            fg_filters.target_container = [workers, "content"]
            fg_filters.filter()

            try:
                temp = building.get_business("fg")
                guild_teams = CoordsForPaging(temp.idle_teams(), columns=2, rows=3, size=(310, 83), xspacing=3, yspacing=3, init_pos=(-2, 420))
            except:
                pass

    scene bg scroll

    $ renpy.retain_after_load()
    show screen building_management
    with fade

    $ pytfall.world_quests.run_quests("auto") # Added for completion, unnecessary?
    $ pytfall.world_events.run_events("auto")

    $ global_flags.set_flag("keep_playing_music")

label building_management_loop:

    $ last_label = "building_management" # We need this so we can come back here from screens that depends on this variable.

    if not global_flags.flag("4_tutorial") and hero.upgradable_buildings:
        $ global_flags.set_flag("4_tutorial")
        show screen tutorial(4)

    while 1:
        if hero.upgradable_buildings:
            $ building = hero.upgradable_buildings[index]

        $ result = ui.interact()
        if not result or not isinstance(result, (list, tuple)):
            jump building_management_loop

        if result[0] == "fg_team":
            if result[1] == "rename":
                $ n = renpy.call_screen("pyt_input", result[2].name, "Enter Name", 8)
                if len(n):
                    $ result[2].name = n
            elif result[1] == "clear":
                python:
                    for i in result[2]._members[:]:
                        workers.add(i)
                        result[2]._members.remove(i)
        elif result[0] == "building":
            # if result[1] == 'buyroom':
            #     python:
            #         if building.rooms < building.maxrooms:
            #             if hero.take_money(building.get_room_price(), reason="Building"):
            #                 building.modrooms(1)
            #             else:
            #                 renpy.call_screen('message_screen', "Not enough funds to buy new room!")
            #         else:
            #             renpy.call_screen('message_screen', "No more rooms can be added to this building!")
            if result[1] == 'items_transfer':
                python:
                    it_members = list(building.get_all_chars())
                    it_members.sort(key=attrgetter("name"))
                hide screen building_management
                $ items_transfer(it_members)
                show screen building_management
            elif result[1] == "sign":
                python:
                    ad = result[2]

                    if building.flag('bought_sign'):
                        price = ad['price']/10
                    else:
                        price = ad['price']

                    if hero.take_money(price, reason="Building Ads"):
                        building.set_flag('bought_sign', True)
                        ad['active'] = not ad['active']
                    else:
                        renpy.show_screen("message_screen", "Not enough cash on hand!")
            elif result[1] == "celeb":
                python:
                    ad = result[2]
                    if hero.take_money(ad['price'], reason="Building Ads"):
                        ad['active'] = True
                    else:
                        renpy.show_screen("message_screen", "Not enough cash on hand!")
            elif result[1] == "sell":
                python:
                    price = int(building.price*0.9)

                    if renpy.call_screen("yesno_prompt",
                                         message="Are you sure you wish to sell %s for %d Gold?" % (building.name, price),
                                         yes_action=Return(True), no_action=Return(False)):
                        if hero.home == building:
                            hero.home = locations["Streets"]
                        if hero.workplace == building:
                            hero.action = None
                            hero.workplace = None
                        if hero.location == building:
                            set_location(hero, hero.home)

                        retire_chars_from_location(hero.chars, building)

                        hero.add_money(price, reason="Property")
                        hero.remove_building(building)

                        if hero.upgradable_buildings:
                            index = 0
                            building = hero.upgradable_buildings[index]
                        else:
                            jump("building_management_end")
        # Upgrades:
        elif result[0] == 'upgrade':
            if result[1] == "build":
                python hide:
                    temp = result[2]()
                    if isinstance(temp, BusinessUpgrade):
                        result[3].add_upgrade(temp, pay=True)
                    elif isinstance(temp, Business):
                        building.add_business(temp, pay=True)
                    elif isinstance(temp, BuildingUpgrade):
                        building.add_upgrade(temp, pay=True)
                    else:
                        raise Exception("Unknown extension class detected: {}".format(result[2]))
        elif result[0] == "maintenance":
            python:
                # Cleaning controls
                if result[1] == "clean":
                    price = building.get_cleaning_price()
                    if hero.take_money(price, reason="Pro-Cleaning"):
                        building.fin.log_expense(price, "Pro-Cleaning")
                        building.dirt = 0
                    else:
                        renpy.show_screen("message_screen", "You do not have the required funds!")
                elif result[1] == "clean_all":
                    if hero.take_money(result[2], reason="Pro-Cleaning"):
                        for i in hero.dirty_buildings:
                            i.fin.log_expense(i.get_cleaning_price(), "Pro-Cleaning")
                            i.dirt = 0
                    else:
                        renpy.show_screen("message_screen", "You do not have the required funds!")
                elif result[1] == "rename_building":
                    building.name = renpy.call_screen("pyt_input", default=building.name, text="Enter Building name:")
                elif result[1] == "retrieve_jail":
                    pytfall.ra.retrieve_jail = not pytfall.ra.retrieve_jail
        elif result[0] == 'control':
            if result[1] == 'left':
                $ index = (index - 1) % len(hero.upgradable_buildings)
            elif result[1] == 'right':
                $ index = (index + 1) % len(hero.upgradable_buildings)

            if result[1] == 'return':
                jump building_management_end

label building_management_end:
    hide screen building_management

    # Reset the vars on next reentry:
    $ reset_building_management = False
    jump mainscreen

init: # Screens:
    screen building_management():
        $ tt = Tooltip(getattr(building, "desc", ""))

        if hero.upgradable_buildings:
            # Main Building mode:
            if bm_mid_frame_mode == "building":
                use building_management_midframe_building_mode
            else: # Upgrade mode:
                use building_management_midframe_businesses_mode

            ## Stats/Upgrades - Left Frame
            frame:
                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                xysize (330, 720)
                # xanchor .01
                ypos 40
                style_group "content"
                has vbox
                if bm_mid_frame_mode == "building":
                    use building_management_leftframe_building_mode
                else: # Upgrade mode:
                    use building_management_leftframe_businesses_mode

            ## Right frame:
            frame:
                xysize (330, 720)
                ypos 40
                xalign 1.0
                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                has vbox spacing 1
                if bm_mid_frame_mode == "building":
                    use building_management_rightframe_building_mode
                else: # Upgrade mode:
                    use building_management_rightframe_businesses_mode

        else:
            text "You don't own any buildings.":
                size 50
                color ivory
                align .5, .5
                style "TisaOTM"

        use top_stripe(True)
        if not bm_mid_frame_mode == "building":
            key "mousedown_3" action SetVariable("bm_mid_frame_mode", "building")
        else:
            key "mousedown_4" action Return(["control", "right"])
            key "mousedown_5" action Return(["control", "left"])

    screen building_management_rightframe_building_mode:
        # Buttons group:
        frame:
            xalign .5
            style_prefix "wood"
            xpadding 0
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.9), 5, 5)
            has hbox xalign .5 spacing 5 xsize 315
            null height 16
            vbox:
                spacing 5
                button:
                    xysize (135, 40)
                    action Show("building_adverts")
                    hovered tt.action('Advertise this building to attract more and better customers')
                    sensitive building.can_advert and building.workable
                    text "Advertise"
                button:
                    xysize (135, 40)
                    action Return(['building', "items_transfer"])
                    hovered tt.action('Transfer items between characters in this building')
                    sensitive (len(building.get_all_chars()) >= 2)
                    text "Transfer Items"
                button:
                    xysize (135, 40)
                    action Show("building_maintenance")
                    hovered tt.action('Perform maintenance of this building')
                    sensitive isinstance(building, BuildingStats) and building.workable
                    text "Maintenance"
            vbox:
                spacing 5
                button:
                    xysize (135, 40)
                    action SetField(hero, "location", building)
                    hovered tt.action('Place [hero.name] in this building')
                    sensitive False # We prolly want better conditioning to use this!
                    text "Settle"
                button:
                    xysize (135, 40)
                    action Show("finances", None, building, mode="logical")
                    hovered tt.action('Show finance log for this building')
                    sensitive building.workable
                    text "Finance Log"
                button:
                    xysize (135, 40)
                    action Return(["building", "sell"])
                    hovered tt.action('Get rid of this building')
                    text "Sell"

        # Slots for New Style Upgradable Buildings:
        if isinstance(building, UpgradableBuilding):
            frame:
                xalign .5
                style_group "wood"
                xpadding 0
                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.9), 5, 5)
                has vbox xalign .5 spacing 2 xsize 315
                hbox:
                    xoffset 5
                    xalign .5
                    xsize 300
                    spacing 3
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.7), 5, 5)
                        has vbox xysize (130, 40)
                        text "Indoor Slots:" size 10 color yellow xalign .5
                        text "%d/%d" % (building.in_slots, building.in_slots_max) color beige size 12 xalign .5 style_suffix "value_text"
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.7), 5, 5)
                        has vbox xysize (130, 40)
                        text "Outdoor Slots:" size 10 color yellow xalign .5
                        text "%d/%d" % (building.ex_slots, building.ex_slots_max) color beige size 12 xalign .5 style_suffix "value_text"
                # frame:
                #     xysize (145, 40)
                #     xalign .5
                #     # has vbox
                #     text "Construction" size 10 color yellow align .5, .5
                    # text "%d/%d" % (building.ex_slots, building.ex_slots_max) color beige size 12 xalign .5 style_suffix "value_text"

        # Tooltip related:
        frame:
            background Frame(Transform("content/gfx/frame/ink_box.png"), 10, 10)
            xalign .5
            xpadding 10
            xysize (310, 200)
            text (u"{=content_text}{size=20}{color=[goldenrod]}%s" % tt.value) yalign .02 size 14

        # Manager?
        if isinstance(building, UpgradableBuilding):
            vbox:
                xalign .5
                frame:
                    xmaximum 220
                    ymaximum 220

                    xalign .5
                    background Frame(Transform("content/gfx/frame/MC_bg3.png", alpha=.95), 10, 10)
                    if building.manager:
                        add building.manager.show("profile", resize=(190, 190), add_mood=True, cache=True) align .5, .5
                    else:
                        xysize (190, 190)
                        text "No manager" align (.5, .5) size 25 color goldenrod drop_shadow [(1, 2)] drop_shadow_color black antialias True style_prefix "proper_stats"
                if building.manager:
                    text "Current manager" align (.5, .5) size 25 color goldenrod drop_shadow [(1, 2)] drop_shadow_color black antialias True style_prefix "proper_stats"

    screen building_management_rightframe_businesses_mode:
        $ frgr = Fixed(xysize=(315, 680))
        $ frgr.add(ProportionalScale("content/gfx/images/e1.png", 315, 600, align=(.5, .0)))
        $ frgr.add(ProportionalScale("content/gfx/images/e2.png", 315, 600, align=(.5, 1.0)))
        frame:
            style_prefix "content"
            xysize (315, 680)
            background Null()
            foreground frgr
            frame:
                pos 25, 20
                xysize (260, 40)
                background Frame("content/gfx/frame/namebox5.png", 10, 10)
                label (u"__ [bm_mid_frame_mode.name] __") text_size 18 text_color ivory align (.5, .6)
            null height 5

            frame:
                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                align (.5, .5)
                xpadding 10
                ypadding 10
                vbox:
                    style_group "wood"
                    align (.5, .5)
                    spacing 10
                    button:
                        xysize (150, 40)
                        yalign .5
                        action SetVariable("bm_mid_frame_mode", "building")
                        hovered tt.action("Here you can invest your gold and resources for various improvements.\nAnd see the different information (reputation, rank, fame, etc.)")
                        text "Building" size 15
                    if False and isinstance(bm_mid_frame_mode, ExplorationGuild):
                        button:
                            xysize (150, 40)
                            yalign .5
                            action NullAction()
                            hovered tt.action("All the meetings and conversations are held in this Hall. On the noticeboard, you can take job that available for your rank. Sometimes guild members or the master himself and his Council, can offer you a rare job.")
                            text "Main Hall" size 15
                    if isinstance(bm_mid_frame_mode, ExplorationGuild):
                        button:
                            xysize (150, 40)
                            yalign .5
                            action SetVariable("bm_exploration_view_mode", "team")
                            hovered tt.action("You can customize your team here or hire Guild members.")
                            text "Team" size 15
                        button:
                            xysize (150, 40)
                            yalign .5
                            action SetVariable("bm_exploration_view_mode", "explore")
                            hovered tt.action("On this screen you can organize the expedition. Also, there is a possibility to see all available information on the various places, enemies and items drop.")
                            text "Exploration" size 15
                        button:
                            xysize (150, 40)
                            yalign .5
                            action SetVariable("bm_exploration_view_mode", "log")
                            hovered tt.action("For each of your teams, recorded one last adventure, which you can see here in detail.")
                            text "Log" size 15

            # Tooltip Frame
            frame:
                background Frame("content/gfx/frame/ink_box.png", 10, 10)
                xysize (307, 190)
                padding 10, 10
                align .5, .99
                text (u"{=proper_stats_text}{color=[bisque]}%s" % tt.value) outlines [(1, "#3a3a3a", 0, 0)]

    screen building_management_leftframe_building_mode:
        frame:
            background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
            style_group "proper_stats"
            xsize 316
            padding 10, 10
            has vbox spacing 1

            # We are not really using this anymore?
            # Security Rating:
            # frame:
            #     xysize (296, 27)
            #     text "Security Rating:" xalign .02 color ivory
            #     text "%s/1000" % building.security_rating xalign .98 style_suffix "value_text" yoffset 4
            # INSTEAD: Report quarter location.
            frame:
                xysize (296, 27)
                text "Location:" xalign .02 color ivory
                text "[building.location]" xalign .98 style_suffix "value_text" yoffset 4

            # Dirt:
            if isinstance(building, BuildingStats):
                frame:
                    xysize (296, 27)
                    text "Dirt:" xalign .02 color ivory
                    text "%s (%s %%)" % (building.get_dirt_percentage()[1], building.get_dirt_percentage()[0]) xalign .98 style_suffix "value_text" yoffset 4
                frame:
                    xysize (296, 27)
                    text "Threat:" xalign .02 color ivory
                    text "%s %%" % (building.threat * 100 / building.max_stats["threat"]):
                        xalign .98
                        style_suffix "value_text"
                        yoffset 4
            if hasattr(building, "tier"):
                frame:
                    xysize (296, 27)
                    text "Tier:" xalign .02 color ivory
                    text "%s" % (building.tier) xalign .98 style_suffix "value_text" yoffset 4

            # Fame/Rep:
            if isinstance(building, FamousBuilding):
                frame:
                    xysize (296, 27)
                    text "Fame:" xalign .02 color ivory
                    text "%s/%s" % (building.fame, building.maxfame) xalign .98 style_suffix "value_text" yoffset 4
                frame:
                    xysize (296, 27)
                    text "Reputation:" xalign .02 color ivory
                    text "%s/%s" % (building.rep, building.maxrep) xalign .98 style_suffix "value_text" yoffset 4

        null height 5
        frame:
            background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
            xysize (317, 480)
            if isinstance(building, UpgradableBuilding):
                frame:
                    align .5, .02
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                    xysize (180, 40)
                    label 'Constructed:' text_color ivory xalign .5 text_bold True
                viewport:
                    pos 3, 55
                    xysize 310, 406
                    mousewheel True
                    scrollbars "vertical"
                    draggable True
                    has vbox
                    for u in building.all_extensions():
                        frame:
                            xalign .6
                            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 5, 5)
                            has fixed xysize 290, 80
                            frame:
                                align .05, .1
                                background Frame(Transform("content/gfx/frame/MC_bg3.png", alpha=.95), 10, 10)
                                if hasattr(u, "img"):
                                    add im.Scale(u.img, 100, 65) align .5, .5
                                else:
                                    add Solid(black, xysize=(100, 65)) align .5, .5
                            vbox:
                                xpos 125
                                yalign .5
                                xysize 150, 60
                                text "[u.name]" xalign .5 style "proper_stats_text" size 20
                                null height 2
                                textbutton "{size=15}{font=fonts/TisaOTM.otf}{color=[goldenrod]}Details":
                                    background Transform(Frame("content/gfx/interface/images/story12.png"), alpha=.8)
                                    hover_background Transform(Frame(im.MatrixColor("content/gfx/interface/images/story12.png", im.matrix.brightness(.15))), alpha=1)
                                    hovered tt.action("View details or expand {}.".format(u.name))
                                    xalign .5
                                    action SetVariable("bm_mid_frame_mode", u)

        # frame:
            # background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
            # xysize (317, 160)
            # style_group "stats"
            # label "Active Advertisements:" text_color ivory xalign .5
            # if hasattr(building, "use_adverts") and building.use_adverts:
                # vbox:
                    # null height 35
                    # spacing -6
                    # for advert in building.adverts:
                        # if advert['active']:
                            # frame:
                                # xysize (305, 27)
                                # text (u"%s" % advert['name']) size 16 xalign (.02)

    screen building_management_leftframe_businesses_mode:
        $ show_slots = not any([(isinstance(bm_mid_frame_mode, ExplorationGuild) and bm_exploration_view_mode in ("log", "team", "explore"))])
        if show_slots:
            frame:
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                style_group "proper_stats"
                xsize 310
                padding 12, 12
                margin 0, 0
                has vbox spacing 1
                # Slots:
                frame:
                    xysize (290, 27)
                    xalign .5
                    text "Indoor Slots:" xalign .02 color ivory
                    text "[bm_mid_frame_mode.in_slots]"  xalign .98 style_suffix "value_text" yoffset 4
                frame:
                    xysize (290, 27)
                    xalign .5
                    text "Exterior Slots:" xalign .02 color ivory
                    text "[bm_mid_frame_mode.ex_slots]"  xalign .98 style_suffix "value_text" yoffset 4

            $ c0 = isinstance(bm_mid_frame_mode, CoreExtension)
            if c0 and bm_mid_frame_mode.expands_capacity:
                null height 5
                frame:
                    background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                    style_prefix "proper_stats"
                    xsize 310
                    padding 12, 12
                    margin 0, 0
                    has vbox spacing 1
                    frame:
                        xysize (290, 27)
                        xalign .5
                        text "Capacity:" xalign .02 color ivory
                        text "[bm_mid_frame_mode.capacity]"  xalign .98 style_suffix "value_text" yoffset 4
                    null height 5
                    text "To Expand:"
                    frame:
                        xysize (290, 27)
                        xalign .5
                        text "Indoor Slots Required:" xalign .02 color ivory
                        text "[bm_mid_frame_mode.exp_cap_in_slots]"  xalign .98 style_suffix "value_text" yoffset 4
                    frame:
                        xysize (290, 27)
                        xalign .5
                        text "Exterior Slots Required:" xalign .02 color ivory
                        text "[bm_mid_frame_mode.exp_cap_ex_slots]"  xalign .98 style_suffix "value_text" yoffset 4
                    frame:
                        xysize (290, 27)
                        xalign .5
                        text "Cost:" xalign .02 color ivory
                        text "[bm_mid_frame_mode.exp_cap_cost]"  xalign .98 style_suffix "value_text" yoffset 4
                    null height 1
                    textbutton "Expand Capacity":
                        style "pb_button"
                        xalign .5
                        if bm_mid_frame_mode.can_extend_capacity():
                            action [Function(bm_mid_frame_mode.expand_capacity),
                                    Play("audio", "content/sfx/sound/world/purchase_1.ogg")]
                            hovered tt.action("Add more space to this business!")
                        else:
                            action NullAction()
                            hovered tt.action("Can't add more space to this business at this time!")

            if getattr(bm_mid_frame_mode, "upgrades", []):
                null height 5
                frame:
                    align .5, .02
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                    xysize (180, 40)
                    label 'Constructed:' text_color ivory xalign .5 text_bold True
                viewport:
                    pos 3, 10
                    xysize 310, 406
                    mousewheel True
                    scrollbars "vertical"
                    has vbox
                    for u in bm_mid_frame_mode.upgrades:
                        button:
                            xsize 309
                            style "pb_button"
                            text "[u.name]":
                                align .5, .5
                                color ivory
                            action NullAction()
                            tooltip u.desc

        if isinstance(bm_mid_frame_mode, ExplorationGuild):
            use building_management_leftframe_exploration_guild_mode

    screen building_management_leftframe_exploration_guild_mode:
            if bm_exploration_view_mode == "log":
                default focused_area_index = 0
                $ temp = sorted([a for a in fg_areas.values() if a.main and a.unlocked])
                vbox:
                    xsize 310 spacing 1

                    # Maps sign:
                    frame:
                        style_group "content"
                        xalign .5
                        xysize (200, 50)
                        background Frame("content/gfx/frame/namebox5.png", 10, 10)
                        label (u"Maps") text_size 23 text_color ivory align (.5, .8)

                    # Main Area
                    # We assume that there is always at least one area!
                    $ area = temp[focused_area_index]
                    $ img = im.Scale(area.img, 200, 130)
                    frame:
                        xalign .5
                        background Frame(Transform("content/gfx/frame/MC_bg3.png", alpha=.9), 10, 10)
                        padding 5, 6
                        margin 0, 0
                        xysize 200, 130
                        button:
                            align .5, .5
                            xysize 200, 130
                            background Frame(img)
                            hover_background Frame(im.MatrixColor(img, im.matrix.brightness(.10)))
                            action NullAction()
                            frame:
                                align .5, .0
                                xysize 180, 30
                                background Frame(Transform("content/gfx/frame/ink_box.png", alpha=.5), 5, 5)
                                text area.name color gold style "interactions_text" size 18 outlines [(1, "#3a3a3a", 0, 0)] align .5, .5

                    # Paging for Main Area:
                    hbox:
                        xalign .5
                        textbutton "<==":
                            action SetScreenVariable("focused_area_index", (focused_area_index - 1) % len(temp))
                        textbutton "==>":
                            action SetScreenVariable("focused_area_index", (focused_area_index + 1) % len(temp))

                    # Sub Areas:
                    null height 5
                    $ areas = sorted([a for a in fg_areas.values() if a.area == area.name], key=attrgetter("stage"))
                    fixed:
                        xalign .5
                        xysize 310, 190
                        vbox:
                            xalign .5
                            style_prefix "dropdown_gm2"
                            for area in areas:
                                button:
                                    xysize (180, 18)
                                    action SetVariable("selected_log_area", area), Show("fg_log", None, area, tt), SelectedIf(selected_log_area == area)
                                    text str(area.stage) size 12 xalign .02
                                    label (u"{color=#66CD00}Meow!") text_size 12 align (1.0, .5)

                    # Total Main Area Stats (Data Does Not Exist Yet):
                    frame:
                        style_group "content"
                        xalign .5
                        xysize (200, 50)
                        background Frame("content/gfx/frame/namebox5.png", 10, 10)
                        label (u"Total") text_size 23 text_color ivory align (.5, .8)

                    text "No Data Yet!" xalign .5

            if bm_exploration_view_mode == "team":
                # Filters:
                frame:
                    background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                    style_group "proper_stats"
                    xsize 300
                    xalign .5
                    padding 12, 12
                    margin 0, 0
                    has vbox spacing 1
                    label "Filters:" xalign .5

                    vbox:
                        style_prefix "basic"
                        xalign .5
                        textbutton "Reset":
                            action Function(fg_filters.clear)
                        textbutton "Warriors":
                            action ModFilterSet(fg_filters, "class_filters", "Warrior")
                        textbutton "Free":
                            action ModFilterSet(fg_filters, "status_filters", "free")
                        textbutton "Slaves":
                            action ModFilterSet(fg_filters, "status_filters", "slave")

                # Sorting:
                frame:
                    background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                    style_group "proper_stats"
                    xsize 300
                    xalign .5
                    padding 12, 12
                    margin 0, 0
                    has vbox spacing 1
                    label "Sort:" xalign .5

                    vbox:
                        style_prefix "basic"
                        xalign .5
                        textbutton "Name":
                            action SetFilter(fg_filters, "alphabetical")
                        textbutton "Level":
                            action SetFilter(fg_filters, "level")

            if bm_exploration_view_mode == "explore":
                fixed: # making sure we can align stuff...
                    xysize(320, 665)
                    frame:
                        style_group "content"
                        xalign .5 ypos 5
                        xysize (200, 50)
                        background Frame("content/gfx/frame/namebox5.png", 10, 10)
                        label (u"Maps") text_size 23 text_color ivory align (.5, .8)

                    viewport:
                        xysize 220, 500
                        xalign .5 ypos 60
                        has vbox spacing 4
                        $ temp = sorted([a for a in fg_areas.values() if a.main and a.unlocked])
                        if temp and not bm_mid_frame_focus:
                            $ mid_frame_focus = temp[0]

                        for area in temp:
                            $ img = im.Scale(area.img, 220, 130)
                            frame:
                                background Frame(Transform("content/gfx/frame/MC_bg3.png", alpha=.9), 10, 10)
                                padding 6, 7
                                margin 0, 0
                                xysize 220, 130
                                button:
                                    align .5, .5
                                    xysize 220, 130
                                    background Frame(img)
                                    hover_background Frame(im.MatrixColor(img, im.matrix.brightness(.10)))
                                    action SetVariable("bm_mid_frame_focus", area)
                                    frame:
                                        align .5, .0
                                        xysize 180, 30
                                        background Frame(Transform("content/gfx/frame/ink_box.png", alpha=.5), 5, 5)
                                        text area.name color gold style "interactions_text" size 18 outlines [(1, "#3a3a3a", 0, 0)] align .5, .5

                    # hbox:
                        # xalign .5
                        # spacing 20
                        # add ProportionalScale("content/gfx/interface/buttons/arrow_button_metal_gold_up.png", 50, 50)
                        # add ProportionalScale("content/gfx/interface/buttons/arrow_button_metal_gold_down.png", 50, 50)

    screen building_management_midframe_building_mode:
        frame:
            background Frame("content/gfx/frame/p_frame6.png", 10, 10)
            style_prefix "content"
            xysize (630, 685)
            xalign .5
            ypos 40
            vbox:
                xsize 630
                null height 5
                frame:
                    xalign .5
                    xysize (380, 50)
                    background Frame("content/gfx/frame/namebox5.png", 10, 10)
                    label (u"__ [building.name] __") text_size 23 text_color ivory align (.5, .6)
                null height 5
                frame:
                    xalign .5
                    background Frame(Transform("content/gfx/frame/MC_bg3.png", alpha=.95), 10, 10)
                    add ProportionalScale(building.img, 600, 444) align (.5, .5)

            # Left/Right Controls + Expand button:
            vbox:
                align .5, 1.0
                frame:
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.9), 10, 10)
                    has hbox xysize (600, 74)
                    button:
                        align .1, .5
                        xysize (140, 40)
                        style "left_wood_button"
                        action Return(['control', 'left'])
                        hovered tt.action("<== Previous")
                        text "Previous" style "wood_text" xalign .69
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                        xysize (200, 50)
                        align (.5, .5)
                    button:
                        align .9, .5
                        xysize (140, 40)
                        style "right_wood_button"
                        action Return(['control', 'right'])
                        hovered tt.action("Next ==>")
                        text "Next" style "wood_text" xalign .39

                if isinstance(building, UpgradableBuilding):
                    frame:
                        align .5, .95
                        style_group "wood"
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.9), 5, 5)
                        xpadding 20
                        ypadding 10
                        button:
                            align .5, .5
                            xysize (135, 40)
                            action SetVariable("bm_mid_frame_mode", building)
                            hovered tt.action('Open a new business or upgrade this building!')
                            text "Expand"

                ## Security Bar:
                if hasattr(building, "gui_security_bar") and building.gui_security_bar()[0]:
                    frame:
                        xalign .490
                        ypos 561
                        background Frame(Transform("content/gfx/frame/rank_frame.png", alpha=.4), 5, 5)
                        xysize (240, 55)
                        xpadding 10
                        ypadding 10
                        hbox:
                            pos (34, 1)
                            vbox:
                                xsize 135
                                text "Security Presence:" size 12
                            vbox:
                                text (u"%d/%d"%(building.security_presence, building.gui_security_bar()[1])) size 12
                        null height 3
                        bar:
                            align (.45, .8)
                            value FieldValue(building, 'security_presence', building.gui_security_bar()[1], max_is_zero=False, style='scrollbar', offset=0, step=1)
                            xsize 170
                            thumb 'content/gfx/interface/icons/move15.png'

    screen building_management_midframe_businesses_mode:
        frame:
            background Frame("content/gfx/frame/p_frame6.png", 10, 10)
            style_prefix "content"
            xysize (630, 685)
            xpadding 0
            xalign .5
            ypos 40

            # Fighter Guild, team launch and area info:
            if isinstance(bm_mid_frame_mode, ExplorationGuild):
                if bm_exploration_view_mode == "log":
                    vbox:
                        xsize 630
                        frame: # Image
                            xalign .5
                            padding 5, 5
                            background Frame("content/gfx/frame/MC_bg3.png", 10 ,10)
                            add im.Scale("content/gfx/bg/buildings/log.webp", 600, 390)

                if bm_exploration_view_mode == "explore":
                    vbox:
                        xsize 630
                        frame: # Image
                            xalign .5
                            padding 5, 5
                            background Frame("content/gfx/frame/MC_bg3.png", 10 ,10)
                            add im.Scale("content/gfx/bg/buildings/Exploration.webp", 600, 390)

                        hbox:
                            box_wrap 1
                            spacing 2
                            xalign .5
                            if isinstance(bm_mid_frame_focus, FG_Area):
                                $ temp = sorted([a for a in fg_areas.values() if a.area == bm_mid_frame_focus.name], key=attrgetter("stage"))
                                for area in temp:
                                    $ fbg = "content/gfx/frame/mes12.jpg"
                                    $ hfbg = im.MatrixColor("content/gfx/frame/mes11.webp", im.matrix.brightness(.10))
                                    button:
                                        background Transform(Frame(fbg, 10, 10), alpha=.9)
                                        hover_background Transform(Frame(hfbg, 10, 10), alpha=.9)
                                        xysize (150, 90)
                                        ymargin 1
                                        ypadding 1
                                        if area.unlocked:
                                            $ temp = area.name
                                            action Show("fg_area", dissolve, area)
                                        else:
                                            $ temp = "?????????"
                                            action NullAction()
                                        text temp color gold style "interactions_text" size 14 outlines [(1, "#3a3a3a", 0, 0)] align (.5, .01)
                                        hbox:
                                            align (.5, .9)
                                            # Get the correct stars:
                                            # python:
                                                # temp = []
                                                # for i in range(area.explored//20):
                                                    # temp.append(ProportionalScale("content/gfx/bg/example/star2.png", 18, 18))
                                                # if len(temp) != 5:
                                                    # if area.explored%20 >= 10:
                                                        # temp.append(ProportionalScale("content/gfx/bg/example/star3.png", 18, 18))
                                                # while len(temp) != 5:
                                                    # temp.append(ProportionalScale("content/gfx/bg/example/star1.png", 18, 18))
                                            # for i in temp:
                                                # add i

                if bm_exploration_view_mode == "team":
                    # Backgrounds:
                    frame:
                        background Frame(gfxframes + "p_frame52.png", 10, 10)
                        xysize 622, 330
                        yoffset -1
                        xalign .5
                        hbox:
                            xalign .5
                            box_wrap 1
                            for i in xrange(18):
                                frame:
                                    xysize 90, 90
                                    xmargin 2
                                    ymargin 2
                                    background Frame(gfxframes + "p_frame53.png", 5, 5)
                        # Page control buttons:
                        hbox:
                            style_prefix "paging_green"
                            align .5, .99
                            hbox:
                                spacing 1
                                button:
                                    style_suffix "button_left2x"
                                    hovered tt.action("<== First Page")
                                    action Function(workers.first_page), SensitiveIf(workers.page != 0)
                                button:
                                    style_suffix "button_left"
                                    hovered tt.action("<== Previous Page")
                                    action Function(workers.prev_page), SensitiveIf(workers.page - 1 >= 0)
                            null width 60
                            hbox:
                                spacing 1
                                button:
                                    style_suffix "button_right"
                                    hovered tt.action("Next Page ==>")
                                    action Function(workers.next_page), SensitiveIf(workers.page + 1 <= workers.max_page)
                                button:
                                    style_suffix "button_right2x"
                                    hovered tt.action("Last Page ==>")
                                    action Function(workers.last_page), SensitiveIf(workers.page != workers.max_page)

                    # Paging guild teams!
                    hbox:
                        style_prefix "paging_green"
                        align .5, .55
                        hbox:
                            spacing 1
                            button:
                                style_suffix "button_left2x"
                                hovered tt.action("<== First Page")
                                action guild_teams.first_page, SensitiveIf(guild_teams.page != 0)
                            button:
                                style_suffix "button_left"
                                hovered tt.action("<== Previous Page")
                                action guild_teams.prev_page, SensitiveIf(guild_teams.page - 1 >= 0)
                        null width 40
                        hbox:
                            spacing 1
                            button:
                                style_suffix "button_right"
                                hovered tt.action("Next Page ==>")
                                action guild_teams.next_page, SensitiveIf(guild_teams.page + 1 < guild_teams.max_page)
                            button:
                                style_suffix "button_right2x"
                                hovered tt.action("Last Page ==>")
                                action guild_teams.last_page, SensitiveIf(guild_teams.page != guild_teams.max_page)


                    # We'll prolly have to do two layers, one for backgrounds and other for drags...
                    draggroup:
                        id "team_builder"
                        for t, pos in guild_teams:
                            drag:
                                drag_name t
                                xysize (310, 83)
                                draggable 0
                                droppable 1
                                pos pos
                                add gfxframes + "team_frame_1.png"
                                hbox:
                                    yalign .5
                                    xpos 117
                                    spacing 15
                                    for i in t:
                                        $ img = i.show("portrait", resize=(46, 46), cache=1)
                                        button:
                                            xysize (46, 46)
                                            background img
                                            hover_background im.MatrixColor(img, im.matrix.brightness(.10))
                                            action Show("fg_char_dropdown", dissolve, i, team=t, remove=True)
                                            hovered tt.action(i.fullname)
                                frame:
                                    xysize (310, 83)
                                    background gfxframes + "team_frame_2.png"
                                    button:
                                        background Null()
                                        padding 0, 0
                                        margin 0, 0
                                        xpos 49 xanchor .5 yalign .5
                                        xysize 78, 61
                                        action Return(["fg_team", "rename", t])
                                        hovered tt.action("Rename %s Team!"%t.name)
                                        text t.name align .5, .5 hover_color red text_align .5
                                    # Remove all teammembers:
                                    $ img = im.Scale("content/gfx/interface/buttons/shape69.png", 20, 20)
                                    button:
                                        background img
                                        hover_background im.MatrixColor(img, im.matrix.brightness(.15))
                                        insensitive_background  im.Sepia(img)
                                        padding 0, 0
                                        margin 0, 0
                                        align 1.0, 1.0
                                        xysize 20, 20
                                        sensitive t
                                        action Return(["fg_team", "clear", t])
                                        hovered tt.action("Rename all explorers from Team %s!"%t.name)

                        for w, pos in workers:
                            drag:
                                dragged dragged
                                droppable 0
                                hovered tt.action(w.fullname)
                                drag_name w
                                pos pos
                                clicked Show("fg_char_dropdown", dissolve, w, team=None, remove=False)
                                add w.show("portrait", resize=(70, 70), cache=1)

                                # fixed:
                                    # xysize (172, 65)
                                    # hbox:
                                        # yalign .3
                                        # xpos 10
                                        # spacing 20
                                        # for i in hero.team:
                                            # add i.show("portrait", resize=(38, 38), cache=1)
                                    # add gfxframes + "small_port_empty.png"
            else:
                viewport:
                    xysize 620, 668
                    mousewheel True
                    xalign .5
                    has vbox xsize 618
                    if hasattr(bm_mid_frame_mode, "all_possible_extensions"):
                        for u in bm_mid_frame_mode.all_possible_extensions():
                            if not bm_mid_frame_mode.has_extension(u):
                                frame:
                                    xalign .5
                                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                                    has fixed xysize 500, 150

                                    $ cost, materials, in_slots, ex_slots = building.get_extension_cost(u)

                                    frame:
                                        align .3, 0
                                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                                        xpadding 10
                                        text "Resources Needed:" align .5, .5 style "stats_text" size 15

                                    # Materials and GOLD
                                    vbox:
                                        pos 5, 30
                                        box_wrap True
                                        xysize 340, 100
                                        spacing 2
                                        frame:
                                            background Frame("content/gfx/frame/p_frame5.png", 5, 5)
                                            xsize 100
                                            has hbox xsize 90
                                            button:
                                                background Frame("content/gfx/animations/coin_top 0.13 1/1.webp")
                                                xysize 25, 25
                                                align 0, .5
                                                action NullAction()
                                                tooltip "{} Gold required!".format(cost)
                                            text "[cost]" align .95, .5 style "proper_stats_text"

                                        # We presently allow for 3 resources each upgrade. If more, this needs to be a conditioned viewport:
                                        for r, amount in materials.items():
                                            $ r = items[r]
                                            # $ amount = u.MATERIALS[r.id]
                                            frame:
                                                background Frame("content/gfx/frame/p_frame5.png", 5, 5)
                                                xsize 100
                                                has hbox xsize 90
                                                button:
                                                    xysize 25, 25
                                                    background Frame(r.icon)
                                                    align 0, .5
                                                    action NullAction()
                                                    tooltip "{} of {} required!".format(amount, r.id)
                                                text "[amount]" align .95, .5 style "proper_stats_text"

                                    hbox:
                                        align .01, .98
                                        spacing 2
                                        style_prefix "proper_stats"
                                        if in_slots:
                                            text "Indoor Slots: {}".format(in_slots)
                                        if ex_slots:
                                            text "Exterior Slots: {}".format(ex_slots)

                                    vbox:
                                        align 1.0, .5
                                        xsize 150
                                        button:
                                            xalign .5
                                            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 3, 3)
                                            xpadding 10
                                            python:
                                                if len(u.NAME) >= 15:
                                                    t_size = 14
                                                else:
                                                    t_size = 15
                                            textbutton "[u.NAME]":
                                                align .5, .5
                                                style "stats_text"
                                                ypadding 3
                                                text_size t_size
                                                action NullAction()
                                                tooltip u.DESC
                                        button:
                                            xalign .5
                                            xysize 133, 83
                                            background Frame("content/gfx/frame/MC_bg3.png", 3, 3)
                                            foreground Transform(u.IMG, size=(120, 75), align=(.5, .5))
                                            action NullAction()
                                            tooltip u.DESC
                                        textbutton "Build":
                                            xalign .5
                                            style "pb_button"
                                            text_size 15
                                            action [Return(["upgrade", "build", u, bm_mid_frame_mode]),
                                                    SensitiveIf(building.eval_extension_build(u,
                                                                price=(cost, materials, in_slots, ex_slots)))]

                # textbutton "{size=20}{font=fonts/TisaOTM.otf}{color=[goldenrod]}Back":
                #     background Transform(Frame("content/gfx/interface/images/story12.png"), alpha=.8)
                #     hover_background Transform(Frame(im.MatrixColor("content/gfx/interface/images/story12.png", im.matrix.brightness(.15))), alpha=1)
                #     align .5, .95
                #     action SetVariable("bm_mid_frame_mode", "building")


    screen building_maintenance():
        modal True
        zorder 1

        frame:
            style_group "content"
            background Frame("content/gfx/frame/p_frame52.png", 10, 10)
            at slide(so1=(600, 0), t1=.7, eo2=(1300, 0), t2=.7)
            xpos 936
            yalign .95
            xysize(343, 675)

            label (u"{size=20}{color=[ivory]}{b}Maintenance!") align(.5, .19) text_outlines [(2, "#424242", 0, 0)]

            # Tooltip related ---------------------------------->
            default tt = Tooltip("Maintenance screen!")
            frame:
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                align(.5, .88)
                xysize (320, 120)
                xpadding 13
                ypadding 15
                has vbox
                text (u"{color=[goldenrod]}%s" % tt.value) outlines [(1, "#424242", 0, 0)]

            # Controls themselves ---------------------------------->
            vbox:
                style_group "basic"
                align(.55, .5)
                if isinstance(building, BuildingStats):
                    button:
                        xysize(200, 32)
                        action Return(['maintenance', "clean"])
                        hovered tt.action("Hire cleaners to completely clean this building for %d Gold."%building.get_cleaning_price())
                        text "Clean: Building"

                    python:
                        price = 0
                        for i in hero.buildings:
                            if isinstance(i, BuildingStats):
                                price = price + i.get_cleaning_price()

                    button:
                        xysize(200, 32)
                        action Return(['maintenance', "clean_all", price])
                        hovered tt.action("Hire cleaners to completely clean all buildings for [price] Gold.")
                        text "Clean: All Buildings"

                    button:
                        xysize (200, 32)
                        yalign .5
                        action ToggleField(building, "auto_clean")
                        hovered tt.action("Enable automatic hiring of cleaners if the building gets too dirty!")
                        text "Auto-Cleaning:" align (.0, .5)
                        if not building.auto_clean:
                            add (im.Scale('content/gfx/interface/icons/checkbox_unchecked.png', 25, 25)) align (1.0, .5)
                        else:
                            add(im.Scale('content/gfx/interface/icons/checkbox_checked.png', 25, 25)) align (1.0, .5)

                null height 30
                button:
                    xysize (200, 32)
                    xalign .5
                    action Return(['maintenance', "rename_building"])
                    hovered tt.Action("Give new name to your Building!")
                    text "Rename Building"

            if False: #isinstance(building, TrainingDungeon):
                button:
                    style_group "basic"
                    xysize (200, 32)
                    align (.5, .5)
                    action Return(["maintenance", "retrieve_jail"])
                    hovered tt.action("Allow your guards to bail your escaped girls out of jail?")
                    text "Auto-bail" align (.0, .5)
                    if not pytfall.ra.retrieve_jail:
                        add im.Scale("content/gfx/interface/icons/checkbox_unchecked.png", 25, 25) align (1.0, .5)
                    else:
                        add im.Scale("content/gfx/interface/icons/checkbox_checked.png", 25, 25) align (1.0, .5)

            button:
                style_group "dropdown_gm"
                action Hide("building_maintenance")
                minimum(50, 30)
                align (.5, .97)
                text  "OK"
            key "mousedown_3" action Hide("building_maintenance")

    screen building_adverts():
        modal True
        zorder 1

        frame:
            style_group "content"
            at slide(so1=(600, 0), t1=.7, eo2=(1300, 0), t2=.7)
            background Frame("content/gfx/frame/p_frame52.png", 10, 10)
            xpos 936
            yalign .95
            xysize(343, 675)

            label (u"{size=20}{color=[ivory]}{b}Advertise!") text_outlines [(2, "#424242", 0, 0)] align (.5, .16)

            # Tooltip related ---------------------------------->
            default tt = Tooltip("Attract the attention of even more and possibly higher class clients. Choose your advertisement budget carefully so the girls can keep up with quality and quantity of your customers!")
            frame:
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                align(.5, .88)
                xysize (320, 140)
                xpadding 13
                ypadding 15
                has vbox
                text (u"{color=[goldenrod]}%s" % tt.value) outlines [(1, "#424242", 0, 0)]

            # Buttons themselves ---------------------------------->
            hbox:
                align(.5, .4)
                box_wrap True
                spacing 20
                for advert in building.adverts:
                    vbox:
                        style_group "basic"
                        align (.5, .5)
                        # if advert['active']:
                        #     button:
                        #         xysize(280, 32)
                        #         hovered tt.action(advert['desc'])
                        #         action ToggleDict(advert, "active")
                        #         text ("Stop %s!" % advert['name']) color black align (.5, .5)
                        # else:
                        if advert['name'] == "Sign" and not advert['active']:
                            button:
                                xysize(280, 32)
                                hovered tt.action(advert['desc'])
                                action Return(["building", 'sign', advert])
                                text "Put Up Sign!" color black align (.5, .5) size 15
                        elif advert['name'] == "Celebrity":
                            button:
                                xysize(280, 32)
                                hovered tt.action(advert['desc'])
                                action Return(["building", 'celeb', advert])
                                sensitive not advert['active']
                                if not not advert['active']:
                                    text "Hire a Celeb!" color black align (.5, .5) size 15
                                else:
                                    text "Celebrity hired!" color black align (.5, .5) size 15
                        else:
                            button:
                                xysize(280, 32)
                                hovered tt.action(advert['desc'])
                                action ToggleDict(advert, "active")
                                if advert['active']:
                                    text ("Stop %s!" % advert['name']) color black align (.5, .5)
                                elif advert['price'] == 0:
                                    text ("Use %s for %s Gold a day!" % (advert['name'], advert['upkeep'])) color black align (.5, .5) size 15
                                elif advert['upkeep'] == 0:
                                    text ("Use %s for %s Gold!" % (advert['name'], advert['price'])) color black align (.5, .5) size 15
                                else:
                                    text ("Use %s for %s Gold and %s a day!" % (advert['name'], advert['price'], advert['upkeep'])) color black align (.5, .5) size 15

            button:
                style_group "dropdown_gm"
                action Hide("building_adverts")
                minimum(50, 30)
                align (.5, .97)
                text  "OK"
        key "mousedown_3" action Hide("building_adverts")

    screen building_finances():
        modal True
        zorder 1

        default show_fin = "day"

        frame at slide(so1=(0, 700), t1=.7, so2=(0, 0), t2=.3, eo2=(0, -config.screen_height)):
            background Frame("content/gfx/frame/arena_d.png", 5, 5)
            align (.5, .5)

            # side "c r":
            viewport id "message_vp":
                style_group "content"
                xysize (1100, 600)
                draggable False
                mousewheel True

                if day > 1 and str(day-1) in building.fin.game_fin_log:
                    $ fin_inc = building.fin.game_fin_log[str(day-1)][0]
                    $ fin_exp = building.fin.game_fin_log[str(day-1)][1]

                    if show_fin == 'day':
                        label (u"Fin Report (Yesterday)") xalign .4 ypos 30 text_size 30
                        # Income:
                        vbox:
                            pos (50, 100)
                            label "Income:" text_size 20
                            null height 10
                            hbox:
                                vbox:
                                    xmaximum 170
                                    xfill True

                                    for key in fin_inc["work"]:
                                        text ("[key]")

                                    for key in fin_inc["private"]:
                                        if key != "work":
                                            text("[key]")

                                vbox:
                                    for key in fin_inc["work"]:
                                        $ val = fin_inc["work"][key]
                                        text("[val]")

                                    for key in fin_inc["private"]:
                                        $ val = fin_inc["private"][key]
                                        text("[val]")

                        # Expense:
                        vbox:
                            pos (450, 100)
                            label "Expense:" text_size 20
                            null height 10
                            hbox:
                                vbox:
                                    xmaximum 170
                                    xfill True

                                    for key in fin_exp["work"]:
                                        text("[key]")

                                    for key in fin_exp["private"]:
                                        text("[key]")

                                vbox:
                                    for key in fin_exp["work"]:
                                        $ val = fin_exp["work"][key]
                                        text("[val]")

                                    for key in fin_exp["private"]:
                                        $ val = fin_exp["private"][key]
                                        text("[val]")

                        python:
                            total_income = sum(fin_inc["work"].values())
                            total_expenses = sum(fin_exp["work"].values())
                            for key in fin_inc["private"]: total_income += fin_inc["private"][key]
                            for key in fin_exp["private"]: total_expenses += fin_exp["private"][key]
                            total = total_income - total_expenses
                        vbox:
                            align (.80, .60)
                            text "----------------------------------------"
                            text ("Revenue: [total]"):
                                size 25
                                xpos 15
                                if total > 0:
                                    color lawngreen
                                else:
                                    color red

                        hbox:
                            style_group "basic"
                            align (.5, .9)
                            textbutton "{size=-3}Show Total" action SetScreenVariable("show_fin", "total") minimum(200, 30)

                    elif show_fin == 'total':
                        label (u"Fin Report (Game)") xalign .4 ypos 30 text_size 30
                        python:
                            income = dict()
                            for _day in building.fin.game_fin_log:
                                for key in building.fin.game_fin_log[_day][0]["private"]:
                                    income[key] = income.get(key, 0) + building.fin.game_fin_log[_day][0]["private"][key]

                                for key in building.fin.game_fin_log[_day][0]["work"]:
                                    income[key] = income.get(key, 0) + building.fin.game_fin_log[_day][0]["work"][key]

                        # Income:
                        vbox:
                            pos (50, 100)
                            label "Income:" text_size 20
                            null height 10
                            hbox:
                                vbox:
                                    xmaximum 170
                                    xfill True
                                    for key in income:
                                        text("[key]")
                                vbox:
                                    for key in income:
                                        $ val = income[key]
                                        text("[val]")

                        python:
                            expenses = dict()
                            for _day in building.fin.game_fin_log:
                                for key in building.fin.game_fin_log[_day][1]["private"]:
                                    expenses[key] = expenses.get(key, 0) + building.fin.game_fin_log[_day][1]["private"][key]

                                for key in building.fin.game_fin_log[_day][1]["work"]:
                                    expenses[key] = expenses.get(key, 0) + building.fin.game_fin_log[_day][1]["work"][key]
                        vbox:
                            pos (450, 100)
                            label "Expense:" text_size 20
                            null height 10
                            hbox:
                                vbox:
                                    xmaximum 170
                                    xfill True
                                    for key in expenses:
                                        text("[key]")
                                vbox:
                                    for key in expenses:
                                        $ val = expenses[key]
                                        text("[val]")

                        python:
                            game_total = 0
                            total_income = sum(income.values())
                            total_expenses = sum(expenses.values())
                            game_total = total_income - total_expenses
                        vbox:
                            align (.80, .60)
                            text "----------------------------------------"
                            text ("Revenue: [game_total]"):
                                size 25
                                xpos 15
                                if game_total > 0:
                                    color lawngreen
                                else:
                                    color red

                        hbox:
                            style_group "basic"
                            align (.5, .9)
                            textbutton "{size=-3}Show Daily" action SetScreenVariable("show_fin", "day") minimum(200, 30)

                else:
                    text (u"No financial records available!") align(.5, .5)

                button:
                    style_group "basic"
                    action Hide('building_finances')
                    minimum (250, 30)
                    align (.5, .96)
                    text "OK"

    # Customized screens for specific businesses:
    screen fg_log(area, tt):
        on "hide":
            action SetVariable("selected_log_area", None)

        modal True
        zorder 1

        key "mousedown_3" action Hide("fg_log")

        default focused_log = None

        frame:
            ypos 40
            xalign .5
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
            style_prefix "content"
            xysize (630, 680)

            $ fbg = "content/gfx/frame/mes11.webp"
            frame:
                background Transform(Frame(fbg, 10, 10), alpha=.9)
                xysize (620, 90)
                ymargin 1
                ypadding 1
                $ temp = area.name
                text temp color gold style "interactions_text" size 35 outlines [(1, "#3a3a3a", 0, 0)] align (.5, .3)
                hbox:
                    align (.5, .9)
                    # Get the correct stars:
                    python:
                        temp = []
                        for i in range(area.explored//20):
                            temp.append(ProportionalScale("content/gfx/interface/icons/stars/star2.png", 18, 18))
                        if len(temp) != 5:
                            if area.explored%20 >= 10:
                                temp.append(ProportionalScale("content/gfx/interface/icons/stars/star3.png", 18, 18))
                        while len(temp) != 5:
                            temp.append(ProportionalScale("content/gfx/interface/icons/stars/star1.png", 18, 18))
                    for i in temp:
                        add i

            # Buttons with logs (Events):
            frame:
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                style_prefix "dropdown_gm2"
                ypos 100
                ysize 240
                xalign .0
                padding 10, 10
                has vbox xsize 220

                frame:
                    style_group "content"
                    align (.5, .015)
                    padding 15, 5
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                    label "Events" text_size 20 text_color ivory align .5, .5

                null height 2

                for l in area.logs:
                    button:
                        xalign .5
                        ysize 18
                        action SetScreenVariable("focused_log", l)
                        text str(l.name) size 12 xalign .02 yoffset 1
                        # Resolve the suffix:
                        if l.item:
                            text "[l.item.type]" size 12 align (1.0, .5)
                        else: # Suffix:
                            text str(l.suffix) size 12 align (1.0, .5)

            # Information (Story)
            frame:
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                ysize 297
                padding 10, 10
                ypos 100 xalign 1.0
                has vbox xsize 350

                frame:
                    style_group "content"
                    align (.5, .015)
                    padding 15, 5
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                    label "Story" text_size 20 text_color ivory align .5, .5

                null height 2

                frame:
                    background Frame("content/gfx/frame/ink_box.png", 10, 10)
                    has viewport draggable 1 mousewheel 1

                    if focused_log:
                        if focused_log.battle_log:
                            text "\n".join(focused_log.battle_log) color white
                        elif focused_log.item:
                            $ item = focused_log.item
                            vbox:
                                spacing 10 xfill 1
                                add ProportionalScale(item.icon, 100, 100) xalign .5
                                text item.desc xalign .5 color white

    screen fg_area(area):
        modal True
        zorder 1

        key "mousedown_3" action Hide("fg_area")

        # Left frame with Area controls
        frame:
            background Frame("content/gfx/frame/p_frame6.png", 10, 10)
            style_prefix "basic"
            xysize (325, 674)
            xalign .0 ypos 41
            has vbox spacing 4

            # The idea is to add special icons for as many features as possible in the future to make Areas cool:
            # Simple buttons are temp for dev versions/beta.
            button:
                xalign .5
                xysize 300, 25
                if not area.camp:
                    action ToggleField(area, "building_camp")
                else:
                    action NullAction()
                python:
                    if area.camp:
                        status = "Complete"
                    elif area.building_camp:
                        status = area.camp_build_status + " Complete"
                    else:
                        status = "Unknown"
                text "Camp status: [status]" align .01, .5

            button:
                xalign .5
                xysize 300, 25
                action ToggleField(area, "capture_chars")
                text "Capture Chars: [area.capture_chars]" align .01, .5


        # Mid-Frame:
        frame:
            ypos 40
            xalign .5
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
            style_prefix "content"
            xysize (630, 680)

            $ fbg = "content/gfx/frame/mes11.webp"
            frame:
                background Transform(Frame(fbg, 10, 10), alpha=.9)
                xysize (620, 90)
                ymargin 1
                ypadding 1
                $ temp = area.name
                text temp color gold style "interactions_text" size 35 outlines [(1, "#3a3a3a", 0, 0)] align (.5, .3)
                hbox:
                    align (.5, .9)
                    # Get the correct stars:
                    # python:
                        # temp = []
                        # for i in range(area.explored//20):
                            # temp.append(ProportionalScale("content/gfx/bg/example/star2.png", 18, 18))
                        # if len(temp) != 5:
                            # if area.explored%20 >= 10:
                                # temp.append(ProportionalScale("content/gfx/bg/example/star3.png", 18, 18))
                        # while len(temp) != 5:
                            # temp.append(ProportionalScale("content/gfx/bg/example/star1.png", 18, 18))
                    # for i in temp:
                        # add i
                    # button:
                        # align (.5, .95)
                        # action NullAction()
                        # text "Stage 1" size 14
                # vbox:
                    # xfill True
                    # spacing 7
                    # frame:
                        # style_group "content"
                        # align (.5, .015)
                        # xysize (210, 30)
                        # background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                        # label (u"Team name") text_size 20 text_color ivory align(.5, .5)
                    # hbox:
                        # xfill True
                        # spacing 2
                        # add "content/gfx/bg/example/1.png" align (.5, .5)
                        # add "content/gfx/bg/example/2.png" align (.5, .5)
                        # add "content/gfx/bg/example/3.png" align (.5, .5)

            hbox:
                align .5, .5
                frame:
                    background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                    xysize (310, 410)
                    xpadding 5
                    frame:
                        style_group "content"
                        align (.5, .015)
                        xysize (210, 40)
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                        label (u"Enemies") text_size 23 text_color ivory align .5, .5
                    viewport:
                        style_prefix "proper_stats"
                        xysize (300, 340)
                        ypos 50
                        xalign .5
                        has vbox spacing 3
                        for m in area.mobs:
                            $ m = mobs[m]
                            fixed:
                                xysize 300, 65
                                frame:
                                    xpos 6
                                    left_padding 2
                                    align .01, .5
                                    xsize 197
                                    text m["name"]
                                frame:
                                    yalign .5
                                    xanchor 1.0
                                    ysize 44
                                    xpadding 4
                                    xminimum 28
                                    xpos 233
                                    $ temp = m["min_lvl"]
                                    text ("Lvl\n[temp]+") style "TisaOTM" size 17 text_align .5 line_spacing -6
                                frame:
                                    background Frame(Transform("content/gfx/interface/buttons/choice_buttons2.png", alpha=.75), 10, 10)
                                    padding 3, 3
                                    margin 0, 0
                                    xysize 60, 60
                                    align .99, .5
                                    add ProportionalScale(m["portrait"], 57, 57) align .5, .5

                frame:
                    background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                    xysize (310, 410)
                    xpadding 5
                    frame:
                        style_group "content"
                        align (.5, .015)
                        xysize (210, 40)
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                        label (u"Items") text_size 23 text_color ivory align .5, .5
                    viewport:
                        style_prefix "proper_stats"
                        mousewheel 1
                        xysize (300, 340)
                        ypos 50
                        xalign .5
                        has vbox spacing 3
                        for i in area.items:
                            $ i = items[i]
                            fixed:
                                xysize 300, 65
                                frame:
                                    xpos 6
                                    left_padding 2
                                    align .01, .5
                                    xsize 197
                                    text i.id
                                frame:
                                    yalign .5
                                    xanchor 1.0
                                    ysize 40
                                    xsize 35
                                    xpadding 4
                                    xpos 233
                                    #$ temp = m["min_lvl"]
                                    #text ("Lvl\n[temp]+") align (.5, .5) style "TisaOTM" size 18
                                frame:
                                    background Frame(Transform("content/gfx/interface/buttons/choice_buttons2.png", alpha=.75), 10, 10)
                                    padding 3, 3
                                    xysize 60, 60
                                    align .99, .5
                                    add ProportionalScale(i.icon, 57, 57) align .5, .5
                    # frame:
                        # background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                        # xysize (390, 380)
                        # yalign 1.0
                        # frame:
                            # style_group "content"
                            # align (.5, .015)
                            # xysize (200, 40)
                            # background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                            # label (u"Loot") text_size 23 text_color ivory align(.5, .5)
                        # vbox:    ### Need Side-scrolling ###
                            # style_group "stats"
                            # vbox:
                                # xalign .5
                                # ypos 53
                                # vbox:
                                    # spacing 2
                                    # xanchor 0
                                    # xmaximum 210
                                    # xfill True
                                    # hbox:
                                        # xfill True
                                        # spacing -3
                                        # frame:
                                            # yalign .5
                                            # xsize 210
                                            # text("\"Lorekeeper\" Staff")
                                        # frame:
                                            # yalign .5
                                            # xsize 140
                                            # text("Weapon") xalign .5
                                        # frame:
                                            # yalign .5
                                            # xsize 20
                                            # add ProportionalScale("content/gfx/bg/example/legendary.png", 25, 25)
                                # vbox:
                                    # spacing 2
                                    # xanchor 0
                                    # xmaximum 210
                                    # xfill True
                                    # hbox:
                                        # xfill True
                                        # spacing -3
                                        # frame:
                                            # yalign .5
                                            # xsize 210
                                            # text("Ashwood Flatbow")
                                        # frame:
                                            # yalign .5
                                            # xsize 140
                                            # text("Weapon") xalign .5
                                        # frame:
                                            # yalign .5
                                            # xsize 20
                                            # add ProportionalScale("content/gfx/bg/example/uncommon.png", 25, 25)
                                # vbox:
                                    # spacing 2
                                    # xanchor 0
                                    # xmaximum 220
                                    # xfill True
                                    # hbox:
                                        # xfill True
                                        # spacing -3
                                        # frame:
                                            # yalign .5
                                            # xsize 210
                                            # text("???????")
                                        # frame:
                                            # yalign .5
                                            # xsize 140
                                            # text("???????") xalign .5
                                        # frame:
                                            # yalign .5
                                            # xsize 20
                                            # add ProportionalScale("content/gfx/bg/example/unknown2.png", 25, 25)
                                # vbox:
                                    # spacing 2
                                    # xanchor 0
                                    # xmaximum 220
                                    # xfill True
                                    # hbox:
                                        # xfill True
                                        # spacing -3
                                        # frame:
                                            # yalign .5
                                            # xsize 210
                                            # text("Honey")
                                        # frame:
                                            # yalign .5
                                            # xsize 140
                                            # text("Consumable") xalign .5
                                        # frame:
                                            # yalign .5
                                            # xsize 20
                                            # add ProportionalScale("content/gfx/bg/example/common.png", 25, 25)
                                # vbox:
                                    # spacing 2
                                    # xanchor 0
                                    # xmaximum 220
                                    # xfill True
                                    # hbox:
                                        # xfill True
                                        # spacing -3
                                        # frame:
                                            # yalign .5
                                            # xsize 210
                                            # text("???????")
                                        # frame:
                                            # yalign .5
                                            # xsize 140
                                            # text("???????") xalign .5
                                        # frame:
                                            # yalign .5
                                            # xsize 20
                                            # add ProportionalScale("content/gfx/bg/example/unknown2.png", 25, 25)
                                # vbox:
                                    # spacing 2
                                    # xanchor 0
                                    # xmaximum 220
                                    # xfill True
                                    # hbox:
                                        # xfill True
                                        # spacing -3
                                        # frame:
                                            # yalign .5
                                            # xsize 210
                                            # text("???????")
                                        # frame:
                                            # yalign .5
                                            # xsize 140
                                            # text("???????") xalign .5
                                        # frame:
                                            # yalign .5
                                            # xsize 20
                                            # add ProportionalScale("content/gfx/bg/example/unknown2.png", 25, 25)
                                # vbox:
                                    # spacing 2
                                    # xanchor 0
                                    # xmaximum 220
                                    # xfill True
                                    # hbox:
                                        # xfill True
                                        # spacing -3
                                        # frame:
                                            # yalign .5
                                            # xsize 210
                                            # text("???????")
                                        # frame:
                                            # yalign .5
                                            # xsize 140
                                            # text("???????") xalign .5
                                        # frame:
                                            # yalign .5
                                            # xsize 20
                                            # add ProportionalScale("content/gfx/bg/example/unknown2.png", 25, 25)

            hbox:
                align .5, .9

                python:
                    temp = building.get_business("fg")
                    teams = temp.teams_to_launch() if temp else []
                    if teams:
                        if not temp.focus_team:
                            try:
                                temp.focus_team = teams[temp.team_to_launch_index]
                            except:
                                temp.focus_team = teams[0]
                    # if teams:
                        # if temp.focus_team in teams:
                            # temp.team_to_launch_index = teams.index(temp.focus_team)
                        # else:
                            # temp.team_to_launch_index = 0
                            # temp.focus_team = teams[index]


                # Implement team paging...
                # Failed to make this work in a screen, will have to move this paging to the class where there is more control... something is off with scopes I think.
                if teams:
                    textbutton "<==":
                        yalign .5
                        action temp.prev_team_to_launch, renpy.restart_interaction
                    textbutton "Launch \n[temp.focus_team.name]":
                        xsize 300
                        action Function(temp.launch_team, area), Jump("building_management")
                    textbutton "==>":
                        yalign .5
                        action temp.next_team_to_launch, renpy.restart_interaction
                else:
                    text "No teams avalible!"

            hbox:
                align (.5, .98)
                button:
                    style_group "basic"
                    action Hide("fg_area")
                    minimum (50, 30)
                    text  "Back"
                # button:
                        # style_group "basic"
                        # action NullAction()
                        # minimum(50, 30)
                        # align (.5, .98)
                        # text  "Launch!!! Days 1" # Gismo: AutoCalculate. 1 day per stage (1-5), 2 days per stage (6-10).

    screen fg_char_dropdown(char, team=None, remove=False):
        # Trying to create a drop down screen with choices of actions:
        zorder 3
        modal True

        default pos = renpy.get_mouse_pos()

        key "mousedown_4" action NullAction()
        key "mousedown_5" action NullAction()

        # Get mouse coords:
        python:
            x, y = pos
            xval = 1.0 if x > config.screen_width/2 else .0
            yval = 1.0 if y > config.screen_height/2 else .0

        frame:
            style_prefix "dropdown_gm"
            pos (x, y)
            anchor (xval, yval)
            has vbox

            textbutton "Profile":
                action [SetVariable("char_profile", last_label), SetVariable("char", char), SetVariable("girls", [char]), Hide("fg_char_dropdown"), Hide("pyt_fg_management"), Jump("char_profile")]
            textbutton "Equipment":
                action [SetVariable("came_to_equip_from", "building_management"), SetVariable("eqtarget", char), SetVariable("char", char), Hide("fg_char_dropdown"), Hide("pyt_fg_management"), Jump("char_equip")]
            if remove: # and team[0] != girl:
                textbutton "Remove from the Team":
                    action [Function(team.remove, char), Function(workers.add, char), Hide("fg_char_dropdown")]

            null height 10

            textbutton "Close":
                action Hide("fg_char_dropdown")
