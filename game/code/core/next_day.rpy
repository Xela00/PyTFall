init python:
    def sort_for_nd_summary():
        # By Actions, Flags and Buildings...
        events = dict()
        rest = dict()
        actions = dict()

        base = {"IDLE": 0, "Service": 0, "Warriors": 0, "Managers": 0}

        for setup in ["ALL"] + [b for b in hero.buildings if isinstance(b, UpgradableBuilding)]:
            actions[setup] = base.copy()
            rest[setup] = base.copy()
            events[setup] = base.copy()
            for i in events[setup]:
                events[setup][i] = {"count": 0, "red_flag": 0, "green_flag": 0}

            # Actions/Rest first:
            a = actions[setup]
            r = rest[setup]
            e = events[setup]

            if setup == "ALL":
                container = hero.chars
            else:
                container = [c for c in hero.chars if setup in (c.workplace, )]

            for char in container:
                cat = 0
                if char.action is None:
                    cat = "IDLE"
                    a["IDLE"] += 1
                elif hasattr(char.action, "type"):
                    if char.action.type == "Combat":
                        cat = "Warriors"
                        a["Warriors"] += 1
                    elif char.action.type in ["Service", "SIW"]:
                        cat = "Service"
                        a["Service"] += 1
                    elif char.action.type == "Management":
                        cat = "Managers"
                        a["Managers"] += 1
                    elif char.action.type == "Resting":
                        # This needs to be handled separately:
                        if char.action.__class__ == Rest:
                            cat = "IDLE"
                            r["IDLE"] += 1
                        elif char.action.__class__ == AutoRest:
                            # We need to loop over it separately, based on previous occupation:
                            if hasattr(char.previousaction, "type"):
                                if char.previousaction.type == "Combat":
                                    cat = "Warriors"
                                    r["Warriors"] += 1
                                elif char.previousaction.type in ["Service", "SIW"]:
                                    cat = "Service"
                                    r["Service"] += 1
                                elif char.previousaction.type == "Management":
                                    cat = "Managers"
                                    r["Managers"] += 1

                # Events:
                if cat:
                    for event in NextDayEvents:
                        if isinstance(setup, UpgradableBuilding):
                            if event.loc != setup:
                                continue
                        if event.char == char:
                            e[cat]["count"] += 1
                            if event.red_flag:
                                e[cat]["red_flag"] += 1
                            if event.green_flag:
                                e[cat]["green_flag"] += 1

        return actions, rest, events

    def auto_rest_conditions(char):
        # returns True if a char can go AutoResting, False if not.
        c0 = char.is_available
        c1 = isinstance(char.action, Rest)
        c2 = char.AP > 0
        return all([c0, c1, c2])


label next_day:
    scene

    $ next_day_local = None

    if just_view_next_day: # Review old reports:
        $ just_view_next_day = False
    else: # Do the calculations:
        show screen next_day_calculations
        $ nd_turns = getattr(store, "nd_turns", 1)
        while nd_turns:
            call next_day_calculations from _call_next_day_calculations
            call next_day_effects_check from _call_next_day_effects_check
            $ nd_turns -= 1

    $ nd_turns = 1

    # Preparing to display ND.
    ####### - - - - - #######
    # Sort data for summary reports:
    $ ndactive, ndresting, ndevents = sort_for_nd_summary()
    # Setting index and picture
    $ FilteredList = NextDayEvents * 1
    if FilteredList:
        $ event = FilteredList[0]
        $ gimg = event.load_image()

    hide screen next_day_calculations

    call next_day_controls from _call_next_day_controls

    # Lets free some memory...
    if not day%50:
        $ renpy.free_memory()
    if next_day_local:
        jump next_day

    $ girls = None
    hide screen next_day

    if persistent.auto_saves:
        call special_auto_save from _call_special_auto_save

    jump mainscreen

label next_day_calculations:
    if global_flags.flag("nd_music_play"):
        $ global_flags.del_flag("nd_music_play")
        if not "pytfall" in ilists.world_music:
            $ ilists.world_music["pytfall"] = [track for track in os.listdir(content_path("sfx/music/world")) if track.startswith("pytfall")]
        play world choice(ilists.world_music["pytfall"])

    $ global_flags.set_flag("keep_playing_music")

    $ tl.start("Next Day")
    python:
        nd_debug("Day: %s, Girls (Player): %s, Girls (Game): %s" % (day, len(hero.chars), len(chars)))
        FilteredList = list()
        NextDayEvents = list()

    # Restore (AutoEquip for HP/Vit/MP) before the jobs:
    python hide:
        tl.start("AutoEquip Consumables for Workers")
        list(c.restore() for c in list(c for c in hero.chars if c.is_available))
        tl.end("AutoEquip Consumables for Workers")

    # Building events Start:
    $ tl.start("ND-Buildings")

    # Generate buildings list and update manager effectiveness:
    $ nd_buildings = list(b for b in hero.buildings if isinstance(b, UpgradableBuilding))
    python hide: # Figure out what managers can do for us.
        for b in nd_buildings:
            # We can calculate manager effectiveness once, so we don't have to do
            # expensive calculations 10 000 000 times:
            if b.manager:
                job = simple_jobs["Manager"]
                difficulty = b.tier
                b.manager_effectiveness = job.effectiveness(b.manager,
                                                    difficulty, None, False)

    $ tl.start("ND-Rest (First pass)")
    # Sets to AutoRest amongst other things:
    python hide:
        for c in hero.chars:
            if not isinstance(c.action, (Rest, SchoolCourse)):
                can_do_work(c, check_ap=True, log=None)

    # Next Day Resting Chars
    $ ndr_chars = list(c for c in hero.chars if auto_rest_conditions(c))
    while ndr_chars:
        $ resting_char = ndr_chars.pop()
        $ resting_char.action(resting_char) # <--- Looks odd and off?
    $ tl.end("ND-Rest (First pass)")

    while nd_buildings:
        $ building = nd_buildings.pop()
        $ building.run_nd()
        $ building.next_day()

    $ tl.end("ND-Buildings")
    # Building events END.

    # Training events Start:
    python:
        tl.start("Schools ND")
        for school in schools.values():
            school.next_day()
        tl.end("Schools ND")
    # Training events End.

    # Searching events Start:
    # tl.start("Searching") # TODO (lt) Find out if we still want escaping chars?
    # for building in hero.buildings:
    #     girls = building.get_girls("Search")
    #     while girls:
    #         EscapeeSearchJob(choice(girls), building, girls)
    # tl.end("Searching")
    # Searching events End.

    # Second iteration of Rest:
    $ tl.start("ND-Rest (Second pass)")
    $ ndr_chars = list(c for c in hero.chars if auto_rest_conditions(c)) # Next Day Resting Chars
    while ndr_chars:
        $ resting_char = ndr_chars.pop()
        $ resting_char.action(resting_char) # <--- Looks odd and off?
    $ tl.end("ND-Rest (Second pass)")

    python hide:
        # Done after buildings resets in next day because we may allow
        # inter-building actions later.
        for b in nd_buildings:
            building.manager_effectiveness = 0

    python:
        ################## Logic ##################
        tl.start("pytfall/calender .next_day")
        pytfall.next_day()
        calendar.next() # day + 1 is here.
        gm.gm_points = 0
        tl.end("pytfall/calender .next_day")

    $ tl.end("Next Day")

    # Reset Flags:
    python hide:
        for char in chars.values():
            for flag in char.flags.keys():
                if flag.startswith("ndd"):
                    char.del_flag(flag)

    return

label next_day_controls:
    scene bg profile_2
    show screen next_day
    with dissolve
    while 1:
        python:
            result = ui.interact()

            if result[0] == 'filter':
                if result[1] == 'all':
                    FilteredList = NextDayEvents * 1
                elif result[1] == 'red_flags':
                    FilteredList = [e for e in NextDayEvents if e.red_flag]
                elif result[1] == 'mc':
                    FilteredList = [e for e in NextDayEvents if e.type == 'mcndreport']
                elif result[1] == 'school':
                    order = {"school_nd_report": 1, "course_nd_report": 2}
                    temp = [e for e in NextDayEvents if e.type in order]
                    # temp.sort(key=itemgetter(1))
                    # FilteredList = temp
                    temp.sort(key=lambda e: order[e.type])
                    FilteredList = temp
                elif result[1] == 'gndreports': # Girl Next Day Reports
                    FilteredList = [e for e in NextDayEvents if e.type == 'girlndreport']
                elif result[1] == 'building':
                    building = result[2]
                    order = {"buildingreport": 1, "manager_report": 2, "jobreport": 3}
                    FilteredList = sorted([e for e in NextDayEvents if e.loc == building and e.type in order], key=lambda e: order[e.type])
                elif result[1] == "fighters_guild":
                    order = {"fg_report": 1, "exploration_report": 2, "fg_job": 3}
                    FilteredList = sorted([e for e in NextDayEvents if e.type in order], key=lambda e: order[e.type])
                else:
                    nd_debug("unhandled event:"+result[1], "warn")

                if FilteredList:
                    event = FilteredList[0]
                    gimg = event.load_image()
                    index = 0
                else:
                    nd_debug("all NextDayEvents were filtered for: "+result[0]+", "+result[1], "warn")
                    # if result[1] == 'gndreports':
                    # Preventing Index Exception on empty filter
                    FilteredList = NextDayEvents

        if result[0] == 'control':
            if result[1] == 'left':
                python:
                    index = FilteredList.index(event)
                    if index > 0:
                        event = FilteredList[index-1]
                        gimg = event.load_image()
            elif result[1] == 'right':
                python:
                    index = FilteredList.index(event)
                    if index < len(FilteredList)-1:
                        event = FilteredList[index+1]
                        gimg = event.load_image()
            elif result[1] == "next_day_local":
                # Special Logic required:
                hide screen next_day
                $ next_day_local = True
                return
            elif result[1] == 'return':
                return

label next_day_effects_check:  # all traits and effects which require some unusual checks every turn do it here
    python hide:
        if "Life Beacon" in hero.traits:
            mod_by_max(hero, "health", .1)

        for i in hero.chars: # chars with low or high joy get joy-related effects every day

            if 'Depression' in i.effects:
                i.AP -= 1
            elif not "Pessimist" in i.traits and i.joy <= randint(15, 20):
                i.up_counter("depression_counter", 1)
            elif i.joy > 25:
                i.del_flag("depression_counter")

            if i.get_flag("depression_counter", 0) >= 3 and not 'Depression' in i.effects:
                i.enable_effect('Depression')

            if 'Elation' in i.effects:
                if dice(10):
                    i.AP += 1
            elif i.joy >= 95:
                i.up_counter("elation_counter", 1)
            else:
                i.del_flag("elation_counter")
            if i.get_flag("elation_counter", 0) >= 3 and not 'Elation' in i.effects:
                i.enable_effect('Elation')

            if i.vitality < i.get_max("vitality")*.3 and not 'Exhausted' in i.effects: # 5+ days with vitality < .3 max lead to Exhausted effect, can be removed by one day of rest or some items
                i.up_counter("exhausted_counter", 1)
            if i.get_flag("exhausted_counter", 0) >= 5 and not 'Exhausted' in i.effects:
                i.enable_effect('Exhausted')

            if "Life Beacon" in hero.traits: # hero-only trait which heals everybody
                mod_by_max(i, "health", .1)
                i.joy += 1

            if 'Horny' in i.effects: # horny effect which affects various sex-related things and scenes
                i.disable_effect("Horny")
            else:
                if interactions_silent_check_for_bad_stuff(i):
                    if "Nymphomaniac" in i.traits and locked_dice(60):
                        i.enable_effect("Horny")
                    elif not ("Frigid" in i.traits) and locked_dice(30) and i.joy > 50:
                        i.enable_effect("Horny")
    return

label special_auto_save: # since built-in autosave works like shit, I use normal saves to save in auto slots
    $ renpy.notify("Autosaving... You can disable it in game settings")
    if special_save_number > 6:
        $ special_save_number = 1
    python hide:
        temp = "auto-" + str(special_save_number)
        renpy.save(temp)
    $ special_save_number += 1
    if special_save_number > 6:
        $ special_save_number = 1
    return


screen next_day():
    default show_summary = True
    default summary_filter = "buildings" # Not applicable atm
    default report_stats = False


    if show_summary:
        # Right frame (Building/Businesses reports):
        frame:
            background Frame(Transform("content/gfx/frame/p_frame6.png", alpha=.98), 10, 10)
            xysize (581, 683)
            ypos 37
            xalign 1.0
            # ALL Buildings/Workers SUMMARY:
            vbox:
                xalign .38

                frame:
                    style_group "content"
                    xalign .5
                    ypos 5
                    xysize (330, 50)
                    background Frame("content/gfx/frame/namebox5.png", 10, 10)
                    label (u"Buildings") text_size 23 text_color ivory align .5, .6
                    add ProportionalScale("content/gfx/images/birds1.webp", 548, 115) pos (-100, 5)

                null height 80
                # ALL Buildings/Workers SUMMARY:
                frame:
                    align .5, .5
                    top_padding 6
                    xysize 515, 136
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                    hbox:
                        xalign .5

                        null width 5

                        # DATA:
                        frame:
                            align .5, .5
                            xysize 300, 122
                            background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 5, 5)
                            style_group "proper_stats"
                            padding 8, 10
                            has vbox spacing 1

                            # Active (Numeric Info):
                            frame:
                                xysize (285, 25)
                                text "Active" yalign .5 xpos 3
                                text str(ndactive["ALL"]["Service"]) style_suffix "value_text" xpos 135
                                text str(ndactive["ALL"]["Warriors"]) style_suffix "value_text" xpos 175
                                text str(ndactive["ALL"]["Managers"]) style_suffix "value_text" xpos 215
                                text str(ndactive["ALL"]["IDLE"]) style_suffix "value_text" xpos 255

                            # Resting:
                            frame:
                                xysize (285, 25)
                                text "Resting" yalign .5 xpos 3
                                text str(ndresting["ALL"]["Service"]) style_suffix "value_text" xpos 135
                                text str(ndresting["ALL"]["Warriors"]) style_suffix "value_text" xpos 175
                                text str(ndresting["ALL"]["Managers"]) style_suffix "value_text" xpos 215
                                text str(ndresting["ALL"]["IDLE"]) style_suffix "value_text" xpos 255

                            # Events:
                            frame:
                                xpos 2
                                xysize (285, 25)
                                text "Events" yalign .5 xpos 3

                                hbox:
                                    xpos 120
                                    xmaximum 40
                                    text str(ndevents["ALL"]["Service"]["count"]) style_suffix "value_text"

                                    if ndevents["ALL"]["Service"]["red_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color red
                                            action NullAction()

                                    if ndevents["ALL"]["Service"]["green_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color green
                                            action NullAction()

                                hbox:
                                    xpos 164
                                    xmaximum 40
                                    text str(ndevents["ALL"]["Warriors"]["count"]) style_suffix "value_text"

                                    if ndevents["ALL"]["Warriors"]["red_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color red
                                            action NullAction()

                                    if ndevents["ALL"]["Warriors"]["green_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color green
                                            action NullAction()

                                hbox:
                                    xpos 205
                                    xmaximum 40
                                    text str(ndevents["ALL"]["Managers"]["count"]) style_suffix "value_text"

                                    if ndevents["ALL"]["Managers"]["red_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color red
                                            action NullAction()

                                    if ndevents["ALL"]["Managers"]["green_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color green
                                            action NullAction()

                                hbox:
                                    xpos 245
                                    xmaximum 40
                                    text str(ndevents["ALL"]["IDLE"]["count"]) style_suffix "value_text"

                                    if ndevents["ALL"]["IDLE"]["red_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color red
                                            action NullAction()

                                    if ndevents["ALL"]["IDLE"]["green_flag"]:
                                        button:
                                            yoffset 4
                                            padding 1, 1
                                            background Null()
                                            text "!" style "next_day_summary_text" color green
                                            action NullAction()

                            frame:
                                xpos 2
                                xysize (285, 25)
                                text "Customers:" xpos 3
                                python:
                                    clients = 0
                                    for b in [b for b in hero.buildings if isinstance(b, UpgradableBuilding)]:
                                        clients = clients + b.total_clients
                                text "[clients]" style_suffix "value_text"  xpos 135

                        null width 4

            # Separate Buildings data ------------------------------------------------->>>
            side "c l":
                style_prefix "proper_stats"
                xalign .5
                ypos 285
                viewport id "Reports":
                    xysize (580, 365)
                    child_size (600, 10000)
                    draggable True
                    mousewheel True
                    has vbox

                    # Buildings:
                    for building in [b for b in hero.buildings if isinstance(b, UpgradableBuilding)]:
                        # Image/Name:
                        null height 4
                        label "[building.name]" xpos 10
                        null height 1
                        frame:
                            xoffset 9
                            xysize 550, 136
                            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                            hbox:
                                yalign .5
                                null width 10
                                frame:
                                    yalign .5
                                    xysize 95, 95
                                    background Frame("content/gfx/frame/MC_bg3.png", 5, 5)
                                    $ img = im.Scale(building.img, 89, 89)
                                    imagebutton:
                                        align .5, .5
                                        idle img
                                        hover im.MatrixColor(img ,im.matrix.brightness(.15))
                                        action [Return(['filter', 'building', building]), SetScreenVariable("show_summary", None)]
                                        tooltip "View Events in %s building." % building.name

                                    if building.flag_red:
                                        button:
                                            align .95, .95
                                            background Null()
                                            text "!" color red size 40 italic True
                                            action NullAction()
                                            tooltip "There are building related events flagged Red!"

                                null width 6

                                # DATA:
                                frame:
                                    align .5, .5
                                    xysize 426, 122
                                    background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 5, 5)
                                    style_prefix "proper_stats"
                                    padding 8, 10
                                    has vbox spacing 1

                                    # Active:
                                    frame:
                                        xysize 410, 25
                                        text "Active" yalign .5 xpos 3
                                        text str(ndactive[building]["Service"]) style_suffix "value_text" xpos 135
                                        text str(ndactive[building]["Warriors"]) style_suffix "value_text" xpos 175
                                        text str(ndactive[building]["Managers"]) style_suffix "value_text" xpos 215
                                        text str(ndactive[building]["IDLE"]) style_suffix "value_text" xpos 255
                                        text "Dirt" yalign .5 xpos 285
                                        text ("%d%%" % building.get_dirt_percentage()[0]) style_suffix "value_text" xalign .99

                                    # Resting:
                                    frame:
                                        xysize (410, 25)
                                        text "Resting" yalign .5 xpos 3
                                        text str(ndresting[building]["Service"]) style_suffix "value_text" xpos 135
                                        text str(ndresting[building]["Warriors"]) style_suffix "value_text" xpos 175
                                        text str(ndresting[building]["Managers"]) style_suffix "value_text" xpos 215
                                        text str(ndresting[building]["IDLE"]) style_suffix "value_text" xpos 255
                                        text "Fame" yalign .5 xpos 285
                                        text ("%d/%d" % (building.fame, building.maxfame)) style_suffix "value_text" xalign .99

                                    # Events:
                                    frame:
                                        xpos 2
                                        xysize (410, 25)
                                        text "Events" yalign .5 xpos 3

                                        hbox:
                                            xpos 120
                                            xmaximum 40
                                            text str(ndevents[building]["Service"]["count"]) style_suffix "value_text"

                                            if ndevents[building]["Service"]["red_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "!" style "next_day_summary_text" color red
                                                    action NullAction()

                                            if ndevents[building]["Service"]["green_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "!" style "next_day_summary_text" color green
                                                    action NullAction()

                                        hbox:
                                            xpos 164
                                            xmaximum 40
                                            text str(ndevents[building]["Warriors"]["count"]) style_suffix "value_text"

                                            if ndevents[building]["Warriors"]["red_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "{color=[red]}!" style "next_day_summary_text"
                                                    action NullAction()

                                            if ndevents[building]["Warriors"]["green_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "{color=[green]}!" style "next_day_summary_text"
                                                    action NullAction()

                                        hbox:
                                            xpos 205
                                            xmaximum 40
                                            text str(ndevents[building]["Managers"]["count"]) style_suffix "value_text"

                                            if ndevents[building]["Managers"]["red_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "{color=[red]}!" style "next_day_summary_text"
                                                    action NullAction()

                                            if ndevents[building]["Managers"]["green_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "{color=[green]}!" style "next_day_summary_text"
                                                    action NullAction()

                                        hbox:
                                            xpos 245
                                            xmaximum 40
                                            text str(ndevents[building]["IDLE"]["count"]) style_suffix "value_text"

                                            if ndevents[building]["IDLE"]["red_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "{color=[red]}!" style "next_day_summary_text"
                                                    action NullAction()

                                            if ndevents[building]["IDLE"]["green_flag"]:
                                                button:
                                                    yoffset 4
                                                    padding 1, 1
                                                    background Null()
                                                    text "{color=[green]}!" style "next_day_summary_text"
                                                    action NullAction()

                                        hbox:
                                            xpos 284
                                            xmaximum 48
                                            text "Rep."
                                        hbox:
                                            xalign .99
                                            xmaximum 100
                                            text ("%d/%d" % (building.rep, building.maxrep)) style_suffix "value_text"

                                    hbox:
                                        frame:
                                            xpos 2
                                            xysize (410, 25)
                                            if hasattr(building, "total_clients"):
                                                text "Customers:" xpos 3
                                                text "[building.total_clients]" style_suffix "value_text" xpos 135

                vbar value YScrollValue("Reports")

        # Buttons will be drawn over the frame ================================================>>>>
        if summary_filter == "buildings":
            $ start_pos = 844
            for i in ("Servers", "Combatant", "Managers", "IDLE"):
                $ start_pos = start_pos + 42
                frame:
                    at rotate_by(45)
                    pos (start_pos, 95)
                    xysize (90, 30)
                    background Frame("content/gfx/interface/buttons/button_wood_right_hover.png", 3, 3)
                    text "[i]" size 12 bold True xalign .4

        # Left Frame ==========================================================================>>>>
        # Finances:
        frame:
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
            xysize 277, 683 xoffset 3
            ypos 37

            # Day Total ===========================================>>>
            $ fin_inc = hero.fin.game_main_income_log.get(day-1, {})
            $ fin_exp = hero.fin.game_main_expense_log.get(day-1,{})

            frame:
                style_prefix "proper_stats"
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                xysize 270, 670
                xoffset -4

                null height 10

                frame:
                    style "content_frame"
                    xalign .6 ypos 15
                    xysize 210, 40
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                    label (u"Daily Balance") text_size 23 text_color ivory xalign .5 yoffset -4

                vbox:
                    ypos 60
                    $ counter = 0
                    $ max_fields = 21
                    for k, v in fin_inc.iteritems():
                        if v:
                            $ counter += 1
                            frame:
                                xysize 250, 25
                                xoffset 10
                                text "[k]" color green xoffset 3
                                text "[v]" color green style_suffix "value_text" xoffset -3

                    for k, v in fin_exp.iteritems():
                        if v:
                            $ counter += 1
                            frame:
                                xysize 250, 25
                                xoffset 10
                                text "[k]" color red xoffset 3
                                text "[v]" color red style_suffix "value_text" xoffset -3

                    # Empty field fillers:
                    for i in xrange(max(0, max_fields-counter)):
                        frame:
                            xysize 250, 25
                            xoffset 10

                python:
                    total_income = 0
                    total_expenses = 0
                    for key in fin_inc:
                        total_income += fin_inc[key]
                    for key in fin_exp:
                        total_expenses += fin_exp[key]
                    total = total_income - total_expenses
                    if total < 0:
                        color = red
                    else:
                        color = green

                frame:
                    xysize 250, 25
                    yalign .98 xoffset 10
                    text "Total" xoffset 3 color color
                    text "[total]" style_suffix "value_text" xoffset -3 color color

                add ProportionalScale("content/gfx/images/magic2.png", 120, 120) offset 140, -140

        # Middle Frames =======================================================================>>>>
        # Middle Top: Game Total
        frame:
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
            xysize (430, 220)
            pos (275, 37)
            style_group "content"

            frame:
                ypos 6
                xalign .5
                xysize (380, 50)
                background Frame("content/gfx/frame/namebox5.png", 10, 10)
                label (u"Game Total") text_size 23 text_color ivory align .5, .6

            $ income, expense, total = hero.fin.get_game_total()
            null height 1
            frame:
                align .5, .95
                xysize (414, 150)
                style_prefix "proper_stats"
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 5, 5)
                add ProportionalScale("content/gfx/images/jp1.png", 68, 101) pos (330, 20)
                add ProportionalScale("content/gfx/images/jp2.png", 73, 103) pos (12, 20)

                vbox:
                    align .5, .3
                    frame:
                        xysize 240, 30
                        xalign .5
                        text ("Earnings") color green xoffset 2
                        text ("[income]") color green style_suffix "value_text" xoffset -2
                    frame:
                        xysize 240, 30
                        xalign .5
                        text ("Expenses") color red xoffset 2
                        text ("[expense]") color red style_suffix "value_text" xoffset -2

                null height 2
                $ cl = green if total > 0 else red
                frame:
                    align .5, .90
                    xysize 250, 30
                    frame:
                        text "Total" color cl size 24 xpos 2
                        text "[total]" color cl style_suffix "value_text" xoffset -3 size 19

        # Middle Bottom Frame =================================================================>>>>
        frame:
            pos (275, 252)
            xysize (430, 468)
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)

            # Hero Filter/Portrait:
            frame:
                xalign .5
                xysize 414, 120
                background Frame("content/gfx/frame/ink_box.png", 10 ,10)
                $ img = hero.show("portrait", resize=(95, 95), cache=True)
                frame:
                    background Frame("content/gfx/frame/MC_bg3.png", 10 ,10)
                    align .23, .8
                    imagebutton:
                        idle img
                        hover im.MatrixColor(img, im.matrix.brightness(.15))
                        action [Return(['filter', 'mc']), SetScreenVariable("show_summary", None)]
                        tooltip "Show personal MC report!"
                frame:
                    style_group "proper_stats"
                    yalign .5
                    xpos 178
                    xysize 155, 110
                    background Frame(Transform("content/gfx/frame/P_frame2.png", alpha=.6), 10, 10)
                    vbox:
                        label "[hero.name]":
                            text_size 16
                            text_bold True
                            xpos 38
                            yalign .03
                            text_color ivory
                        fixed: # HP
                            xysize (150, 25)
                            xanchor -8
                            bar:
                                yalign .5
                                left_bar ProportionalScale("content/gfx/interface/bars/hp1.png", 150, 20)
                                right_bar ProportionalScale("content/gfx/interface/bars/empty_bar1.png", 150, 20)
                                value hero.health
                                range hero.get_max("health")
                                thumb None
                                xysize (150, 20)
                            text "HP" size 14 color ivory bold True yalign .1 xpos 8
                            if hero.health <= hero.get_max("health")*.2:
                                text "[hero.health]" size 14 color red bold True style_suffix "value_text" yoffset -3 xpos 102
                            else:
                                text "[hero.health]" size 14 color ivory bold True style_suffix "value_text" yoffset -3 xpos 102

                        fixed: # MP
                            xysize (150, 25)
                            xanchor -5
                            bar:
                                yalign .2
                                left_bar ProportionalScale("content/gfx/interface/bars/mp1.png", 150, 20)
                                right_bar ProportionalScale("content/gfx/interface/bars/empty_bar1.png", 150, 20)
                                value hero.mp
                                range hero.get_max("mp")
                                thumb None
                                xysize (150, 20)
                            text "MP" size 14 color ivory bold True yalign .8 xpos 7
                            if hero.mp <= hero.get_max("mp")*.2:
                                text "[hero.mp]" size 14 color red bold True style_suffix "value_text" yoffset 2 xpos 99
                            else:
                                text "[hero.mp]" size 14 color ivory bold True style_suffix "value_text" yoffset 2 xpos 99

                        fixed: # VIT
                            xysize (150, 25)
                            xanchor -2
                            bar:
                                yalign .5
                                left_bar ProportionalScale("content/gfx/interface/bars/vitality1.png", 150, 20)
                                right_bar ProportionalScale("content/gfx/interface/bars/empty_bar1.png", 150, 20)
                                value hero.vitality
                                range hero.get_max("vitality")
                                thumb None
                                xysize (150, 20)
                            text "VP" size 14 color ivory bold True yalign .8 xpos 7
                            if hero.vitality <= hero.get_max("vitality")*.2:
                                text "[hero.vitality]" size 14 color red bold True style_suffix "value_text" yoffset 2 xpos 99
                            else:
                                text "[hero.vitality]" size 14 color ivory bold True style_suffix "value_text" yoffset 2 xpos 99
                            add ProportionalScale("content/gfx/images/c1.png", 123, 111) pos (-42, 55)

                # MC (extra info) -------------------------------------------->>>
                # Preparing info:
                python:
                    for i in NextDayEvents:
                        if i.type == "mcndreport":
                            report = i

                if i.red_flag:
                    button:
                        align .99, .99
                        background Frame("content/gfx/frame/p_frame5.png", 5, 5)
                        text "!" color red size 35 hover_size 40 style "proper_stats_text"
                        action NullAction()
                        tooltip "Red flag in MC's Report!"

            # Group report buttons (School, All, Flagged Red)
            hbox:
                xalign .5 ypos 150
                spacing 20
                # ALL Reports button:
                $ img = "content/gfx/frame/MC_bg3.png"
                button:
                    xysize 95, 95
                    yalign .5
                    idle_background Frame(img, 5 , 5)
                    hover_background Frame(im.MatrixColor(img ,im.matrix.brightness(.2)), 5, 5)
                    text "All" align .5, .5 style "proper_stats_label_text" size 32
                    action [Return(['filter', 'all']), SetScreenVariable("show_summary", None)]
                    tooltip "Show full report tree!"

                # RED FLAG Button:
                # View all red flagged events:
                python:
                    red_flags = False
                    for i in NextDayEvents:
                        if i.red_flag:
                            red_flags = True
                            break
                $ img = "content/gfx/frame/p_frame5.png"
                button:
                    yalign .5
                    xysize (90, 90)
                    idle_background Frame(img, 5, 5)
                    if red_flags:
                        hover_background Frame(im.MatrixColor(img, im.matrix.brightness(.10)), 5, 5)
                        tooltip "View all Events flagged Red!"
                        action [Return(['filter', 'red_flags']), SetScreenVariable("show_summary", None)]
                    else:
                        hover_background Frame(img, 5, 5)
                        action NullAction()
                        tooltip "There are no events flagged Red!"
                    text "!" align (.5, .5) color (red if red_flags else grey) size 60 style "proper_stats_text"

                # School:
                # Preparing info:
                python:
                    for school_report in NextDayEvents:
                        if school_report.type == "school_nd_report":
                            break

                frame:
                    align .02, .98
                    xysize 95, 95
                    padding 2, 2
                    background Frame("content/gfx/frame/MC_bg3.png", 5, 5)
                    $ img = schools["-PyTFall Educators-"].img
                    button:
                        xysize 90, 90
                        align .5, .5
                        background Frame(img, 10, 10)
                        hover_background Frame(im.MatrixColor(img ,im.matrix.brightness(.15)), 10, 10)
                        action [Return(['filter', 'school']), SetScreenVariable("show_summary", None)]
                        tooltip "View School and School Events!"

                    hbox:
                        align 1.0, 1.0
                        if "New Courses" in school_report.txt:
                            button:
                                xysize 30, 30
                                yalign .5
                                padding 0, 0
                                margin 0, 0
                                background Null()
                                action NullAction()
                                tooltip "New Courses available!"
                                text "+" color yellow size 40 style "proper_stats_text" align .5, .5
                        if "Student(s) completed" in school_report.txt:
                            button:
                                xysize 10, 36
                                yalign .5
                                background Null()
                                action NullAction()
                                tooltip "One of your girls has successfully completed her course (this doesn't mean that a course has ended)!"
                                text "!" color yellow size 40 style "proper_stats_text" align .5, .5
                        if "Student(s) were sent" in school_report.txt:
                            button:
                                xysize 10, 36
                                yalign .5
                                background Null()
                                action NullAction()
                                tooltip "A course one of your girls attended has ended!"
                                text "!" color yellow size 40 style "proper_stats_text" align .5, .5

            # # Girls and Other Related data:
            hbox:
                xalign .5 ypos 300
                spacing 80
                # Getting .status field data:
                python:
                    free = 0
                    slaves = 0
                    for girl in hero.chars:
                        if girl.status == "slave":
                            slaves = slaves + 1
                        else:
                            free = free + 1
                python:
                    red_flags = False
                    for i in NextDayEvents:
                        if i.type == "girlndreport" and i.red_flag:
                            red_flags = True

                hbox:
                    spacing 5
                    yalign .5
                    add ProportionalScale("content/gfx/interface/icons/slave.png", 50, 50)
                    text "[slaves]" style "agrevue"

                frame:
                    xysize 95, 95
                    padding 2, 2
                    background Frame("content/gfx/frame/MC_bg3.png", 5, 5)
                    $ img = "content/gfx/interface/buttons/girls_reports.png"
                    button:
                        align .5, .5
                        xysize 90, 90
                        background Frame(img, 10, 10)
                        hover_background Frame(im.MatrixColor(img ,im.matrix.brightness(.15)), 10, 10)
                        action [Return(['filter', 'gndreports']), SetScreenVariable("show_summary", None)]
                        tooltip "Show personal girl reports!"
                    if red_flags:
                        button:
                            xysize 10, 36
                            align 1.0, 1.0
                            background Null()
                            action NullAction()
                            tooltip "Red flag in Girls personal Reports!"
                            text "!":
                                style "proper_stats_text"
                                color red
                                size 40
                                align .5, .5

                hbox:
                    spacing 5
                    yalign .5
                    text "[free]" style "agrevue"
                    add ProportionalScale("content/gfx/interface/icons/free.png", 50, 50)

            # Data:
            python:
                unas = list()
                for girl in hero.chars:
                    if not girl.action:
                        unas.append(girl)
                unas = len(unas)
            text "Unassigned: [unas]":
                yalign .5 ypos 420
                style "agrevue"
                if unas:
                    color red
                else:
                    color green

        use top_stripe(True)

    #  Reports  =============================================================================>>>>
    else:
        key "mousedown_4" action Return(['control', 'right'])
        key "mousedown_5" action Return(['control', 'left'])

        # Image frame:
        frame:
            pos 0, 0
            xysize 839, 720
            background Frame("content/gfx/frame/p_frame7.webp", 10, 10)
            padding 0, 0
            margin 0, 0
            frame:
                align .5, .5
                padding 5, 5
                margin 0, 0
                background Frame("content/gfx/frame/MC_bg3.png", 10 , 10)
                add gimg align .5, .5

        # Stat Frames:
        $ show_stat_frame = event.charmod or event.team_charmod or event.locmod
        showif show_stat_frame and report_stats:
            # Chars/Teams Stats Frame:
            frame:
                at slide(so1=(136, 0), eo1=(0, 0), t1=.4,
                         so2=(0, 0), eo2=(136, 0), t2=.3)
                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                pos (690, -2)
                has fixed xysize 136, 400
                if event.charmod or event.team_charmod:
                    frame:
                        style_group "content"
                        xalign .5
                        ypos 5
                        xysize (136, 40)
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.7), 10, 10)
                        label (u"Stat Changes:") text_size 18 text_color ivory align (.5, .5)

                    if event.team:
                        pass # Preventing crash before system is adjusted to team jobs again.
                    elif event.team_charmod:
                        viewport:
                            xalign .5
                            ypos 45
                            xysize (136, 355)
                            child_size 5000, 355
                            # We'll use a single vbox for stats in case of one char and the usual slideshow thing for teams:
                            $ xsize = len(event.team_charmod)*136
                            for i in range(2):
                                fixed:
                                    xysize xsize, 355
                                    if not i:
                                        at mm_clouds(xsize, 0, 25)
                                    else:
                                        at mm_clouds(0, -xsize, 25)
                                    $ xpos = 0
                                    for w, stats in event.team_charmod.iteritems():
                                        vbox:
                                            style_group "proper_stats"
                                            xsize 136
                                            xpos xpos
                                            spacing 1
                                            frame:
                                                xysize 132, 25
                                                xalign .5
                                                if len(w.nickname) > 20:
                                                    $ size = 16
                                                else:
                                                    $ size = 20
                                                text w.nickname align .5, .5 style "TisaOTM" size size
                                            null height 4
                                            for key in sorted(stats.keys()):
                                                $ value = stats[key]
                                                if value:
                                                    frame:
                                                        xalign .5
                                                        xysize 130, 25
                                                        text (u"%s:"%str(key).capitalize()) align .02, .5
                                                        if value > 0:
                                                            label (u"{color=[lawngreen]}%d"%value) align .98, .5
                                                        else:
                                                            label (u"{color=[red]}%d"%value) align .98, .5
                                        $ xpos += 136
                    # Normal, one worker report case:
                    else:
                        vbox:
                            style_group "proper_stats"
                            xsize 136
                            xalign .5 ypos 45
                            spacing 1
                            for key, value in event.charmod.items():
                                if value:
                                    frame:
                                        xalign .5
                                        xysize 130, 25
                                        text (u"%s:" % str(key).capitalize()) align .02, .5
                                        python: # Special considerations:
                                            if key in ["dirt", "threat"]:
                                                neg_color = lawngreen
                                                pos_color = red
                                            else:
                                                neg_color = red
                                                pos_color = lawngreen
                                        if value > 0:
                                            label (u"[value]") text_color pos_color align .98, .5
                                        elif value < 0:
                                            label (u"[value]") text_color neg_color align .98, .5

            # Buildings Stats Frame:
            frame background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10):
                at slide(so1=(136, 0), eo1=(0, 0), t1=.4,
                             so2=(0, 0), eo2=(136, 0), t2=.3)
                pos (690, 406)
                viewport id "nextdaybsf_vp":
                    xysize (136, 305)
                    if event.type=="jobreport":
                        vbox:
                            null height 5
                            frame:
                                style_group "content"
                                xalign .5
                                xysize (136, 40)
                                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.7), 10, 10)
                                label (u"Building Stats:") text_size 18 text_color ivory align .5, .5
                            null height 10
                            vbox:
                                style_group "proper_stats"
                                xsize 136
                                spacing 1
                                for key in event.locmod:
                                    if event.locmod[key] != 0:
                                        frame:
                                            xalign .5
                                            xysize 130, 25
                                            if key == "reputation":
                                                $ hkey = "Rep"
                                            else:
                                                $ hkey = key
                                            text (u"{size=-1} %s:"%hkey.capitalize()) align .02, .5
                                            label (u"{size=-5}%d"%event.locmod[key]) align .98, .5

        # Text Frame + Stats Reports Mousearea:
        # frame:
        #     background Frame("content/gfx/frame/p_frame5.png", 10, 10)
        #     xysize (449, 609)
        #     pos (834, -2)
        #     vbox:
                # frame:
                #     background Frame("content/gfx/frame/namebox5.png", 10, 10)
                #     xalign .5
                #     style_prefix "content"
                #     xysize (200, 40)
                #     label (u"Description:") text_size 18 text_color ivory align(.5, .6)
        frame:
            background Frame("content/gfx/frame/mes12.jpg")
            xysize 442, 606
            xalign 1.0
            side "c l":
                ypos 5
                xalign .5
                viewport id "nextdaytxt_vp":
                    xysize 420, 580
                    draggable True mousewheel True
                    child_size 400, 10000
                    has vbox xsize 420 xfill True
                    null height 5
                    if isinstance(event.txt, basestring):
                        text u"{}".format(event.txt) style "TisaOTMolxm" size 18
                    else:
                        for i in event.txt:
                            text str(i) style "TisaOTMolxm" xalign .0 size 12
                vbar value YScrollValue("nextdaytxt_vp")

        mousearea:
            area (834, -2, 449, 609)
            hovered SetScreenVariable("report_stats", True)
            unhovered SetScreenVariable("report_stats", False)
        # Bottom Buttons:
        frame:
            background Frame("content/gfx/frame/mes12.jpg")
            align 1.0, 1.0
            xysize 442, 115
            vbox:
                align .5, .5
                spacing 8
                hbox:
                    align (.5, .5)
                    spacing 20
                    button:
                        xysize (120, 40)
                        style "left_wood_button"
                        action Return(['control', 'left'])
                        tooltip "<== View Previous Event"
                        text "Previous Event" style "wood_text" xalign(.6) size 10
                    frame:
                        align (.5, .5)
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.9), 5, 5)
                        xysize (90, 40)
                        text(u'Act: %d/%d'%(FilteredList.index(event)+1, len(FilteredList))) align (.5, .5) size 16 style "proper_stats_text" text_align .5
                    button:
                        xysize (120, 40)
                        style "right_wood_button"
                        action Return(['control', 'right'])
                        tooltip "View Next Event ==>"
                        text "Next Event" style "wood_text" xalign .4 size 10
                hbox:
                    align .5, .5
                    spacing 20
                    textbutton "-Next Day-":
                        style "main_screen_4_button"
                        tooltip "Begin New day and watch the results."
                        action [Hide("mainscreen"), Return(['control', "next_day_local"])]
                        text_size 16
                        ypadding 5
                        xysize (150, 40)

                    $ img = im.Scale("content/gfx/interface/buttons/close.png", 40, 40)
                    imagebutton:
                        align (.5, .5)
                        idle img
                        hover im.MatrixColor(img, im.matrix.brightness(.25))
                        action Return(['control', 'return'])
                        tooltip "Return to previous screen!"

                    textbutton "-Summary-":
                        style "main_screen_4_button"
                        tooltip "Back to ND Summary!"
                        action SetScreenVariable("show_summary", True)
                        text_size 16
                        ypadding 5
                        xysize 150, 40
                        keysym "mousedown_3"

screen next_day_calculations():
    zorder 20
    text "Processing next day calculations..." font "fonts/badaboom.ttf" color "#daa520" size 35 align(.5, .5) outlines [(2, "#000000", 0, 0)]
