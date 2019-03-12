screen building_management_leftframe_exploration_guild_mode:
    if bm_exploration_view_mode == "explore":

        default focused_area_index = 0

        $ temp = sorted([a for a in fg_areas.values() if a.main and a.unlocked], key=attrgetter("stage"))
        vbox:
            xsize 320 spacing 1
            # Maps sign:
            frame:
                style_group "content"
                xalign .5 ypos 3
                xysize 200, 50
                background Frame("content/gfx/frame/namebox5.png", 10, 10)
                label (u"Maps") text_size 23 text_color ivory align .5, .8

            null height 5

            # Main Area with paging:
            # We assume that there is always at least one area!
            $ main_area = temp[focused_area_index]
            $ img = main_area.img
            hbox:
                xalign .5
                button:
                    style "paging_green_button_left"
                    yalign .5
                    tooltip "Previous Page"
                    action SetScreenVariable("focused_area_index", (focused_area_index - 1) % len(temp)), SetScreenVariable("focused_log", None)
                null width 5
                frame:
                    background Frame(Transform("content/gfx/frame/MC_bg3.png", alpha=.9), 10, 10)
                    padding 2, 2
                    margin 0, 0
                    xalign .5
                    button:
                        align .5, .5
                        xysize 220, 130
                        background Frame(img)
                        action NullAction()
                        frame:
                            align .5, .0
                            padding 20, 2
                            background Frame(Transform("content/gfx/frame/frame_bg.png", alpha=.5), 5, 5)
                            text main_area.name:
                                color gold
                                style "interactions_text"
                                size 18 outlines [(1, "#3a3a3a", 0, 0)]
                                align .5, .5
                null width 5
                button:
                    style "paging_green_button_right"
                    yalign .5
                    tooltip "Next Page"
                    action SetScreenVariable("focused_area_index", (focused_area_index + 1) % len(temp)), SetScreenVariable("focused_log", None)

            # Sub Areas:
            null height 5
            $ areas = sorted([a for a in fg_areas.values() if a.area == main_area.id], key=attrgetter("stage"))
            fixed:
                xalign .5
                xysize 310, 190
                vbox:
                    xalign .5
                    style_prefix "dropdown_gm2"
                    for area in areas:
                        button:
                            xysize 220, 18
                            if area.unlocked:
                                if selected_log_area == area:
                                    action SetScreenVariable("focused_log", None), SetVariable("selected_log_area", None)
                                    selected True
                                else:
                                    action SetScreenVariable("focused_log", None), SetVariable("selected_log_area", area)
                                $ tmp = area.name
                                tooltip area.desc
                            else:
                                if the_eye_upgrade_active:
                                    $ tmp = get_obfuscated_str(area.name)
                                else:
                                    $ tmp = "????????????"
                                action NullAction()
                            selected selected_log_area == area
                            text str(area.stage):
                                size 12
                                xalign .02
                                yoffset 1
                            label "[tmp]":
                                text_color limegreen
                                text_selected_color gold
                                text_size 12
                                align 1.0, .5

            # Total Main Area Stats (Data Does Not Exist Yet):
            frame:
                style_group "content"
                xalign .5
                xysize 200, 50
                background Frame("content/gfx/frame/namebox5.png", 10, 10)
                label (u"Total") text_size 23 text_color ivory align .5, .8

            vbox:
                xalign .5
                style_prefix "proper_stats"
                $ total = sum(main_area.found_items.values())
                frame:
                    xoffset 4
                    xysize 270, 27
                    xpadding 7
                    text "Items Found:":
                        color ivory
                    text "[total]":
                        style_suffix "value_text"
                        color ivory
                frame:
                    xoffset 4
                    xysize 270, 27
                    xpadding 7
                    text "Gold Found:":
                        color ivory
                    text "[main_area.cash_earned]":
                        style_suffix "value_text"
                        color ivory
                $ total = sum(main_area.mobs_defeated.values())
                frame:
                    xoffset 4
                    xysize 270, 27
                    xpadding 7
                    text "Mobs Crushed:":
                        color ivory
                    text "[total]":
                        style_suffix "value_text"
                        color ivory
                frame:
                    xoffset 4
                    xysize 270, 27
                    xpadding 7
                    hbox:
                        if the_eye_upgrade_active and (area.chars or area.rchars):
                            button:
                                background Frame("content/buildings/upgrades/the_eye.webp")
                                xysize 28, 28
                                yalign .5
                                action NullAction()
                                tooltip "The Eye detects wanderers at this location!"
                        text "Chars Captured:":
                            color ivory
                    text "[main_area.chars_captured]":
                        style_suffix "value_text"
                        color ivory

        if selected_log_area:
            $ area = selected_log_area
            vbox:
                xalign .5 yoffset 10
                if the_eye_upgrade_active and (area.chars or area.special_chars or area.special_items):
                    button:
                        background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                        padding 5, 5
                        xalign .5
                        action SetVariable("bm_exploration_view_mode", "team")
                        tooltip "The Eye detects something interesting at this location!"
                        add pscale("content/buildings/upgrades/the_eye.webp", 50, 50)
                else:
                    null height 50
                frame:
                    background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
                    xalign .5
                    style_prefix "wood"
                    button:
                        xysize 150, 40
                        action SetVariable("bm_exploration_view_mode", "team"), SetScreenVariable("focused_log", None)
                        tooltip "You can customize your team here or hire Guild members."
                        text "<== Teams" size 15
    elif bm_exploration_view_mode == "team":
        # Filters:
        frame:
            background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
            style_group "proper_stats"
            xsize 314
            xalign .5
            padding 10, 10
            margin 0, 0
            has vbox spacing 1
            label "Filters:" xalign .5
            vbox:
                style_prefix "basic"
                xalign .5
                textbutton "Reset":
                    xsize 292
                    action Function(fg_filters.clear)
                textbutton "Warriors":
                    xsize 292
                    action ModFilterSet(fg_filters, "occ_filters", "Combatant")
                textbutton "Idle":
                    xsize 292
                    action ModFilterSet(fg_filters, "action_filters", None)

        # Sorting:
        frame:
            background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
            style_group "proper_stats"
            xsize 314
            xalign .5
            padding 10, 10
            margin 0, 0
            has vbox spacing 1
            label "Sort:" xalign .5
            vbox:
                style_prefix "basic"
                xalign .5
                textbutton "Name":
                    xsize 292
                    action SetFilter(fg_filters, "alphabetical")
                textbutton "Level":
                    xsize 292
                    action SetFilter(fg_filters, "level")

        # Exploration teams status:
        frame:
            background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
            style_group "proper_stats"
            xsize 314
            xalign .5
            padding 10, 10
            margin 0, 0
            has vbox
            label "Teams Exploring:" xalign .5
            viewport:
                xysize 310, 350
                scrollbars "vertical"
                mousewheel True
                vbox:
                    spacing 5
                    for aname, area in fg_areas.items():
                        if area.trackers:
                            frame:
                                background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                                xsize 280
                                padding 3, 2
                                margin 0, 0
                                has vbox
                                text "[aname]:"
                                for tracker in area.trackers:
                                    hbox:
                                        xsize 274
                                        text "[tracker.team.name]"
                                        text "[tracker.days_explored]/[tracker.days]" xalign 1.0
    elif bm_exploration_view_mode == "upgrade":
        use building_management_leftframe_businesses_mode_upgrades

screen building_management_midframe_exploration_guild_mode:
    if bm_exploration_view_mode == "explore":
        if isinstance(selected_log_area, FG_Area):
            default focused_log = None
            default fg_mid_log_mode = "log"
            $ area = selected_log_area

            frame:
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
                        use stars(area.explored, 100)

            if fg_mid_log_mode == "log":
                # Buttons with logs (Events):
                hbox:
                    ypos 100 xalign .5
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                        style_prefix "dropdown_gm2"
                        ysize 410
                        padding 10, 10
                        has vbox xsize 220 # spacing 1
                        frame:
                            style_group "content"
                            xalign .5
                            padding 15, 5
                            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                            label "Events" text_size 20 text_color ivory align .5, .5

                        null height 4

                        for l in area.logs:
                            button:
                                xalign .5
                                ysize 18
                                action SetScreenVariable("focused_log", l)
                                text str(l.name) size 12 xalign .02 yoffset 1
                                # Resolve the suffix:
                                if l.item:
                                    text "[l.item.type]" size 12 align 1.0, .5
                                else: # Suffix:
                                    text str(l.suffix) size 12 align 1.0, .5

                    # Information (Story)
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6, yzoom=-1), 10, 10)
                        ysize 410
                        padding 10, 10
                        has vbox xsize 350 spacing 1
                        frame:
                            style_group "content"
                            xalign .5
                            padding 15, 5
                            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.6), 10, 10)
                            label "Story" text_size 20 text_color ivory align .5, .5

                        frame:
                            background Frame("content/gfx/frame/ink_box.png", 10, 10)
                            has viewport draggable 1 mousewheel 1
                            if focused_log:
                                if focused_log.battle_log:
                                    text "\n".join(focused_log.battle_log) style "stats_value_text" size 14 color ivory
                                elif focused_log.item:
                                    $ item = focused_log.item
                                    vbox:
                                        spacing 10 xfill True
                                        add ProportionalScale(item.icon, 100, 100) xalign .5
                                        text item.desc xalign .5 style "stats_value_text" size 14 color ivory
            elif fg_mid_log_mode == "info":
                hbox:
                    ypos 100 xalign .5
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
                        xysize 310, 410
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
                                if m in area.mobs_defeated or the_eye_upgrade_active:
                                    $ mob = mobs[m]
                                    fixed:
                                        xysize 300, 65
                                        frame:
                                            xpos 6
                                            left_padding 2
                                            align .01, .5
                                            xsize 197
                                            if m in area.mobs_defeated:
                                                text mob["name"]
                                            else:
                                                text get_obfuscated_str(mob["name"], mod=.8)
                                        frame:
                                            yalign .5
                                            xanchor 1.0
                                            ysize 44
                                            xpadding 4
                                            xminimum 28
                                            xpos 233
                                            if m in area.mobs_defeated:
                                                $ temp = mob["min_lvl"]
                                            else:
                                                $ temp = "??"
                                            text ("Lvl\n[temp]+") style "TisaOTM" size 17 text_align .5 line_spacing -6
                                        frame:
                                            background Frame(Transform("content/gfx/interface/buttons/choice_buttons2.png", alpha=.75), 10, 10)
                                            padding 3, 3
                                            margin 0, 0
                                            xysize 60, 60
                                            align .99, .5
                                            if m in area.mobs_defeated:
                                                add ProportionalScale(mob["portrait"], 57, 57) align .5, .5
                                            else:
                                                add ProportionalScale("content/buildings/upgrades/the_eye.webp", 57, 57) align .5, .5

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
                            $ source = area.found_items.keys() if not the_eye_upgrade_active else area.found_items.keys() + area.items.keys()
                            for i in source:
                                $ item = items[i]
                                fixed:
                                    xysize 300, 65
                                    frame:
                                        xpos 6
                                        left_padding 2
                                        align .01, .5
                                        xsize 197
                                        if i in area.found_items:
                                            text item.id
                                        else:
                                            text get_obfuscated_str(item.id, .8)
                                    frame:
                                        yalign .5
                                        xanchor 1.0
                                        ysize 40
                                        xsize 35
                                        xpadding 4
                                        xpos 233
                                        if i in area.found_items:
                                            $ n = area.found_items[i]
                                            if n >= 100:
                                                $ n = "99+"
                                        else:
                                            $ n = "--"
                                        text "[n]" align (.5, .5) style "TisaOTM" size 18
                                    frame:
                                        background Frame(Transform("content/gfx/interface/buttons/choice_buttons2.png", alpha=.75), 10, 10)
                                        padding 3, 3
                                        xysize 60, 60
                                        align .99, .5
                                        if i in area.found_items:
                                            add ProportionalScale(item.icon, 57, 57) align .5, .5
                                        else:
                                            add ProportionalScale("content/buildings/upgrades/the_eye.webp", 57, 57) align .5, .5

            # Toggle mode:
            # Launch teams:
            vbox:
                align .5, .95 spacing 10
                button:
                    xalign .5
                    style_prefix "basic"
                    if fg_mid_log_mode == "log":
                        action SetScreenVariable("fg_mid_log_mode", "info")
                    else:
                        action SetScreenVariable("fg_mid_log_mode", "log")
                    minimum 100, 30
                    text "<= Toggle View =>"
                hbox:
                    spacing 20
                    python:
                        temp = bm_mid_frame_mode
                        teams = temp.teams_to_launch() if temp else []
                        if teams:
                            if not temp.focus_team:
                                try:
                                    temp.focus_team = teams[temp.team_to_launch_index]
                                except:
                                    temp.focus_team = teams[0]

                    button:
                        style "paging_green_button_left2x"
                        yalign .5
                        action temp.prev_team_to_launch, renpy.restart_interaction
                        tooltip "Previous Team"
                        sensitive len(teams) > 1
                    button:
                        style "marble_button"
                        padding 10, 10
                        if teams:
                            action Function(temp.launch_team, area), Jump("building_management")
                            tooltip "Send {} on {} days long exploration run!".format(temp.focus_team.name, area.days)
                            vbox:
                                xminimum 150
                                spacing -30
                                text "Launch" style "basic_button_text" xalign .5
                                text "\n[temp.focus_team.name]" style "basic_button_text" xalign .5
                        else:
                            action NullAction()
                            text "No Teams Available!" style "basic_button_text" align .5, .5
                    button:
                        style "paging_green_button_right2x"
                        yalign .5
                        action temp.next_team_to_launch, renpy.restart_interaction
                        tooltip "Next Team"
                        sensitive len(teams) > 1
        else:
            vbox:
                xsize 630
                frame: # Image
                    xalign .5
                    padding 5, 5
                    background Frame("content/gfx/frame/MC_bg3.png", 10 ,10)
                    add im.Scale("content/gfx/bg/buildings/log.webp", 600, 390)
    elif bm_exploration_view_mode == "team":
        # Backgrounds:
        frame:
            background Frame(gfxframes + "p_frame52.webp", 10, 10)
            xysize 622, 344
            yoffset -5
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
                align .5, .97
                hbox:
                    spacing 5
                    $ temp = workers.page - 1 >= 0
                    button:
                        style_suffix "button_left2x"
                        tooltip "<== First Page"
                        action Function(workers.first_page)
                        sensitive temp
                    button:
                        style_suffix "button_left"
                        tooltip "<== Previous Page"
                        action Function(workers.prev_page)
                        sensitive temp
                null width 100
                hbox:
                    spacing 5
                    $ temp = workers.page + 1 < workers.max_page
                    button:
                        style_suffix "button_right"
                        tooltip "Next Page ==>"
                        action Function(workers.next_page)
                        sensitive temp
                    button:
                        style_suffix "button_right2x"
                        tooltip "Last Page ==>"
                        action Function(workers.last_page)
                        sensitive temp

        # Downframe (for the teams and team paging)
        frame:
            background Frame(gfxframes + "p_frame52.webp", 10, 10)
            xysize 700, 349
            ypos 331 xalign .5

        # Paging guild teams!
        hbox:
            style_prefix "paging_green"
            xalign .5 ypos 611
            hbox:
                spacing 5
                $ temp = guild_teams.page - 1 >= 0
                button:
                    style_suffix "button_left2x"
                    tooltip "<== First Page"
                    action Function(guild_teams.first_page)
                    sensitive temp
                button:
                    style_suffix "button_left"
                    tooltip "<== Previous Page"
                    action Function(guild_teams.prev_page)
                    sensitive temp
            null width 20
            button:
                style_group "pb"
                align (.5, .5)
                xsize 60
                action Return(["fg_team", "create"])
                sensitive bm_mid_frame_mode.can_extend_capacity()
                text "..." style "pb_button_text"
                tooltip "Create new team"
            null width 20
            hbox:
                spacing 5
                $ temp = guild_teams.page + 1 < guild_teams.max_page
                button:
                    style_suffix "button_right"
                    tooltip "Next Page ==>"
                    action Function(guild_teams.next_page)
                    sensitive temp
                button:
                    style_suffix "button_right2x"
                    tooltip "Last Page ==>"
                    action Function(guild_teams.last_page)
                    sensitive temp

        # We'll prolly have to do two layers, one for backgrounds and other for drags...
        draggroup:
            id "team_builder"
            drag:
                drag_name workers
                xysize 600, 310
                draggable 0
                droppable True
                pos 0, 0

            for t, pos in guild_teams:
                $ idle_t = t not in bm_mid_frame_mode.exploring_teams()
                for idx, w in enumerate(t):
                    $ w_pos = (pos[0]+17+idx*63, pos[1]+12)
                    $ w.set_flag("_drag_container", t)
                    drag:
                        dragged dragged
                        droppable 0
                        draggable idle_t
                        tooltip w.fullname
                        drag_name w
                        pos w_pos
                        if idle_t:
                            clicked Show("fg_char_dropdown", dissolve, w, team=t, remove=True)
                            hovered Function(setattr, config, "mouse", mouse_drag)
                            unhovered Function(setattr, config, "mouse", mouse_cursor)

                        add w.show("portrait", resize=(46, 46), cache=1)

                drag:
                    drag_name t
                    xysize 208, 83
                    draggable 0
                    droppable idle_t
                    pos pos
                    frame:
                        xysize 208, 83
                        background gfxframes + "team_frame_4.png"
                        button:
                            background Frame("content/gfx/frame/namebox4.png")
                            padding 12, 4
                            margin 0, 0
                            align .5, 1.2
                            action Return(["fg_team", "rename", t])
                            tooltip "Rename the team"
                            text t.name align .5, .5 color orange hover_color red text_align .5
                        # Dissolve the team:
                        $ img = im.Scale("content/gfx/interface/buttons/close4.png", 20, 20)
                        button:
                            background img
                            hover_background im.MatrixColor(img, im.matrix.brightness(.15))
                            insensitive_background  im.Sepia(img)
                            padding 0, 0
                            margin 0, 0
                            align 1.0, 0.0 offset 3, -8
                            xysize 20, 20
                            sensitive idle_t and bm_mid_frame_mode.can_reduce_capacity()
                            action Return(["fg_team", "dissolve", t])
                            tooltip "Dissolve"
                        # Remove all teammembers:
                        $ img = im.Scale("content/gfx/interface/buttons/shape69.png", 20, 20)
                        button:
                            background img
                            hover_background im.MatrixColor(img, im.matrix.brightness(.15))
                            insensitive_background  im.Sepia(img)
                            padding 0, 0
                            margin 0, 0
                            align 1.0, 1.0 offset 3, -10
                            xysize 20, 20
                            sensitive t and idle_t
                            action Return(["fg_team", "clear", t])
                            tooltip "Remove all members!"

            for w, pos in workers:
                $ w.set_flag("_drag_container", workers)
                drag:
                    dragged dragged
                    droppable 0
                    tooltip w.fullname
                    drag_name w
                    pos pos
                    clicked Show("fg_char_dropdown", dissolve, w, team=None, remove=False)
                    add w.show("portrait", resize=(70, 70), cache=1)
                    hovered SetField(config, "mouse", mouse_drag)
                    unhovered SetField(config, "mouse", mouse_cursor)
    elif bm_exploration_view_mode == "upgrade":
        use building_management_midframe_businesses_mode_upgrades

screen building_management_rightframe_exploration_guild_mode:
    if bm_exploration_view_mode == "explore" and selected_log_area:
        $ area = selected_log_area

        style_prefix "basic"

        # Left frame with Area controls
        vbox:
            xsize 330
            spacing 2
            ypos 60 xalign .5
            # The idea is to add special icons for as many features as possible in the future to make Areas cool:
            # Simple buttons are temp for dev versions/beta.
            button:
                xalign .5
                xysize 300, 30
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
                text "Camp status:" xalign .0
                text "[status]" xalign 1.0
            button:
                xalign .5
                xysize 300, 30
                action ToggleField(area, "capture_chars")
                text "Capture Chars:" xalign .0
                text "[area.capture_chars]" xalign 1.0

            null height 5
            button:
                xalign .5
                xysize 300, 30
                text "Days Exploring:" xalign .0
                text "[area.days]" xalign 1.0
                action NullAction()
            hbox:
                xalign .5
                imagebutton:
                    yalign .5
                    idle 'content/gfx/interface/buttons/prev.png'
                    hover im.MatrixColor('content/gfx/interface/buttons/prev.png', im.matrix.brightness(.15))
                    action SetField(area, "days", max(3, area.days-1))
                null width 5
                bar:
                    align .5, 1.0
                    value FieldValue(area, 'days', area.max_days-3, max_is_zero=False, style='scrollbar', offset=3, step=1)
                    xmaximum 150
                    thumb 'content/gfx/interface/icons/move15.png'
                    tooltip "How many days do you wish for the team to spend questing?"
                null width 5
                imagebutton:
                    yalign .5
                    idle 'content/gfx/interface/buttons/next.png'
                    hover im.MatrixColor('content/gfx/interface/buttons/next.png', im.matrix.brightness(.15))
                    action SetField(area, "days", min(15, area.days+1))

            null height 5
            button:
                xalign .5
                xysize 300, 30
                text "Risk:" xalign .0
                text "[area.risk]" xalign 1.0
                action NullAction()
            hbox:
                xalign .5
                imagebutton:
                    yalign .5
                    idle 'content/gfx/interface/buttons/prev.png'
                    hover im.MatrixColor('content/gfx/interface/buttons/prev.png', im.matrix.brightness(.15))
                    action SetField(area, "risk", max(0, area.risk-1))
                null width 5
                bar:
                    align .5, 1.0
                    value FieldValue(area, 'risk', 100, max_is_zero=False, style='scrollbar', offset=0, step=1)
                    xmaximum 150
                    thumb 'content/gfx/interface/icons/move15.png'
                    tooltip ("How much risk does the team take when exploring? The more significant the risk,"+
                             "the higher the reward but your team may not even return of you push this too far!")
                null width 5
                imagebutton:
                    yalign .5
                    idle 'content/gfx/interface/buttons/next.png'
                    hover (im.MatrixColor('content/gfx/interface/buttons/next.png', im.matrix.brightness(.15)))
                    action SetField(area, "risk", min(100, area.risk+1))

        # Exploration teams status:
        frame:
            background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=.6), 10, 10)
            style_group "proper_stats"
            xsize 314
            align .5, .98
            padding 10, 10
            margin 0, 0
            has vbox xsize 294
            frame:
                background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                xalign .5
                xsize 280
                padding 3, 2
                margin 0, 0
                hbox:
                    xsize 274
                    text "Explored:"
                    text "{}%".format(round_int(area.explored)) xalign 1.0
            frame:
                background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                xalign .5
                xsize 280
                padding 3, 2
                margin 0, 0
                hbox:
                    xsize 274
                    text "Distance from city:"
                    text "[area.distance_from_city] km" xalign 1.0
            frame:
                background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                xalign .5
                xsize 280
                padding 3, 2
                margin 0, 0
                hbox:
                    xsize 274
                    text "Difficulty:"
                    text "[area.tier]/10" xalign 1.0
            frame:
                background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                xalign .5
                xsize 280
                padding 3, 2
                margin 0, 0
                hbox:
                    xsize 274
                    text "Hazards:"
                    if not area.explored:
                        text "Unknown" xalign 1.0
                    else:
                        if area.hazard:
                            text "Yes" xalign 1.0
                        else:
                            text "No" xalign 1.0
            null height 10
            label "Teams Exploring:" xalign .5
            viewport:
                xysize 314, 200
                scrollbars "vertical"
                mousewheel True
                if area.trackers:
                    frame:
                        background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                        xsize 280
                        padding 3, 2
                        margin 0, 0
                        has vbox
                        for tracker in area.trackers:
                            hbox:
                                xsize 274
                                text "[tracker.team.name]"
                                text "[tracker.days_explored]/[tracker.days]" xalign 1.0
                else:
                    frame:
                        background Frame(Transform("content/gfx/frame/Namebox.png", alpha=.9), 10, 10)
                        xsize 280
                        padding 3, 2
                        margin 0, 0
                        text "No teams on exploration runs."
    else:
        frame:
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.98), 10, 10)
            align .5, .5
            padding 10, 10
            vbox:
                style_prefix "wood"
                align .5, .5
                spacing 10
                button:
                    xysize 150, 40
                    yalign .5
                    action Return(["bm_mid_frame_mode", "building"])
                    tooltip ("Here you can invest your gold and resources for various improvements.\n"+
                             "And see the different information (reputation, rank, fame, etc.)")
                    text "Building" size 15

                if False:
                    button:
                        xysize 150, 40
                        yalign .5
                        action NullAction()
                        tooltip ("All the meetings and conversations are held in this Hall."+
                                 "On the noticeboard, you can take job that available for your rank."+
                                 " Sometimes guild members or the master himself and his Council, can offer you a rare job.")
                        text "Main Hall" size 15
                button:
                    xysize 150, 40
                    yalign .5
                    action SetVariable("bm_exploration_view_mode", "team")
                    tooltip "You can customize your team here or hire Guild members."
                    text "Teams" size 15
                button:
                    xysize 150, 40
                    yalign .5
                    action SetVariable("bm_exploration_view_mode", "explore")
                    tooltip ("On this screen you can organize the expedition. Also, there is a "+
                             "possibility to see all available information on the various places, enemies and items drop.")
                    text "Exploration" size 15
                button:
                    xysize 150, 40
                    yalign .5
                    action SetVariable("bm_exploration_view_mode", "upgrade")
                    tooltip "Extend your guild with the best upgrades availible!"
                    text "Upgrades" size 15

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
            action [SetVariable("char_profile_entry", "building_management"),
                    SetVariable("char", char),
                    SetVariable("girls", [char]),
                    Hide("fg_char_dropdown"),
                    Hide("pyt_fg_management"),
                    Jump("char_profile")]
        textbutton "Equipment":
            action [SetVariable("came_to_equip_from", "building_management"),
                    SetVariable("eqtarget", char),
                    SetVariable("char", char),
                    Hide("fg_char_dropdown"),
                    Hide("pyt_fg_management"),
                    Jump("char_equip")]
        if remove: # and team[0] != girl:
            textbutton "Remove from the Team":
                action [Function(team.remove, char), Function(workers.add, char), Hide("fg_char_dropdown"), With(dissolve)]

        null height 10

        textbutton "Close":
            action Hide("fg_char_dropdown"), With(dissolve)
            keysym "mouseup_3"

screen se_debugger():
    zorder 200
    # Useful SE info cause we're not getting anywhere otherwise :(
    viewport:
        xysize (1280, 720)
        scrollbars "vertical"
        mousewheel True
        has vbox

        for area in fg_areas.values():
            if area.trackers:
                text area.name
                for t in area.trackers:
                    hbox:
                        xsize 500
                        spacing 5
                        text t.team.name xalign .0
                        text "[t.state]" xalign 1.0
                    hbox:
                        xsize 500
                        spacing 5
                        text "Days:" xalign .0
                        text "[t.day]/[t.days]" xalign 1.0
                    null height 3
                add Solid("F00", xysize=(1280, 5))

    textbutton "Exit":
        align 1.0, 1.0
        action Hide("se_debugger")
