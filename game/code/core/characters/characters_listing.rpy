init:
    default chars_list_state = None
    python:
        def sorting_for_chars_list():
            return [c for c in hero.chars if c.is_available]

        class CharsListState(_object):
            def __init__(self):
                self.source = CharsSortingForGui(sorting_for_chars_list)
                self.source.sorting_order = "level"

                self.status_filters = None
                #self.location_filters = None
                self.action_filters = None
                self.class_filters = None
                self.home_filters = None
                self.work_filters = None

                self.selected_filters = set()
                self.the_chosen = set()

            def update_filter_sets(self):
                self.status_filters = set()
                #self.location_filters = set()
                self.action_filters = set()
                self.class_filters = set()
                self.home_filters = set()
                self.work_filters = set()
                for c in hero.chars:
                    self.status_filters.add(c.status)
                    #self.locations_filters.add(c.location)
                    self.action_filters.add(c.action)
                    self.home_filters.add(c.home)
                    self.work_filters.add(c.workplace)
                    for bt in c.traits.basetraits:
                        self.class_filters.add(bt)

            def reset_filters(self):
               self.selected_filters = set()

               self.source.clear()
               self.source.filter()

               renpy.restart_interaction()

            def toggleChosenMembership(self, chars):
                if self.the_chosen.issuperset(chars):
                    self.the_chosen.difference_update(chars)
                else:
                    self.the_chosen.update(chars)

label chars_list:
    scene bg gallery
    python:
        # lazy init the page state
        if chars_list_state is None:
            chars_list_state = CharsListState()
        # always update/run the filters, because some girls might have become unavailable
        chars_list_state.update_filter_sets()
        chars_list_state.source.filter()

    show screen chars_list()
    with dissolve

    python:
        while 1:

            result = ui.interact()

            if result[0] == 'control':
                if result[1] == 'return':
                    break
            elif result[0] == "dropdown":
                if result[1] == "workplace":
                    renpy.show_screen("set_workplace_dropdown", result[2], pos=renpy.get_mouse_pos())
                elif result[1] == "home":
                    renpy.show_screen("set_home_dropdown", result[2], pos=renpy.get_mouse_pos())
                elif result[1] == "action":
                    renpy.show_screen("set_action_dropdown", result[2], pos=renpy.get_mouse_pos())
            elif result[0] == 'choice':
                renpy.hide_screen("chars_list")
                char = result[1]
                jump('char_profile')

    hide screen chars_list
    jump mainscreen

screen chars_list():
    key "mousedown_3" action Return(['control', 'return']) # keep in sync with button - alternate

    $ CLS = chars_list_state
    $ num_chars = len(CLS.source.sorted)

    # Normalize pages.
    default page_size = 10
    default page = chars_list_last_page_viewed

    $ max_page = 0 if num_chars == 0 else ((num_chars-1)/page_size)
    if page > max_page:
        $ page = max_page
        $ chars_list_last_page_viewed = max_page

    # Chars:
    if num_chars == 0:
        text "You don't have any workers.":
            size 40
            color ivory
            align .5, .2
            style "TisaOTM"
    else:
        python:
            #listed_chars = []
            #for start in xrange(0, num_chars, page_size):
            #    listed_chars.append(CLS.source.sorted[start:start+page_size])
            #charz_list = listed_chars[page]
            charz_list = CLS.source.sorted[page*page_size:page*page_size+page_size]
        hbox:
            style_group "content"
            spacing 14
            pos 27, 94
            xsize 970
            box_wrap True
            for c in charz_list:
                $ char_profile_img = c.show('portrait', resize=(98, 98), cache=True)
                $ img = "content/gfx/frame/ink_box.png"
                button:
                    ymargin 0
                    idle_background Frame(Transform(img, alpha=.4), 10 ,10)
                    hover_background Frame(Transform(img, alpha=.9), 10 ,10)
                    xysize (470, 115)
                    action Return(['choice', c])
                    alternate Return(['control', 'return']) # keep in sync with mousedown_3
                    tooltip "Show {}'s Profile!".format(c.name)

                    # Image:
                    frame:
                        background Frame("content/gfx/frame/MC_bg3.png", 10, 10)
                        padding 0, 0
                        align 0, .5
                        xysize 100, 100
                        add char_profile_img align .5, .5 alpha .96

                    # Texts/Status:
                    frame:
                        xpos 120
                        xysize (335, 110)
                        background Frame(Transform("content/gfx/frame/P_frame2.png", alpha=.6), 10, 10)
                        label "[c.name]":
                            text_size 18
                            xpos 10
                            yalign .06
                            if c.__class__ == Char:
                                text_color pink
                            else:
                                text_color ivory

                        vbox:
                            align (.96, .035)
                            spacing 5
                            if c.status == "slave":
                                add ProportionalScale("content/gfx/interface/icons/slave.png", 40, 40)
                            else:
                                add ProportionalScale("content/gfx/interface/icons/free.png", 40, 40)

                        vbox:
                            align 1.0, .6 xoffset 5
                            hbox:
                                xsize 60
                                text "AP:" xalign .0 color ivory
                                text "[c.AP]" xalign .1 color ivory
                            hbox:
                                xsize 60
                                text "Tier:" xalign .0 color ivory
                                text "[c.tier]" xalign .1 color ivory
                            # text "AP: [c.AP]" size 17 color ivory
                            # text "Tier: [c.tier]" size 17 color ivory

                        vbox:
                            yalign .98
                            xpos 10
                            # Prof-Classes
                            python:
                                if len(c.traits.basetraits) == 1:
                                    classes = list(c.traits.basetraits)[0].id
                                elif len(c.traits.basetraits) == 2:
                                    classes = list(c.traits.basetraits)
                                    classes.sort()
                                    classes = ", ".join([str(t) for t in classes])
                                else:
                                    raise Exception("Character without prof basetraits detected! line: 211, chars_lists screen")
                            text "Classes: [classes]" color ivory size 18

                            null height 2
                            if c not in pytfall.ra:
                                if not c.flag("last_chars_list_geet_icon"):
                                    $ c.set_flag("last_chars_list_geet_icon", "work")
                                if c.status == "free" and c.flag("last_chars_list_geet_icon") != "work":
                                    $ c.set_flag("last_chars_list_geet_icon", "work")

                                if c.flag("last_chars_list_geet_icon") == "home":
                                    button:
                                        style_group "ddlist"
                                        if c.status == "slave":
                                            action Return(["dropdown", "home", c])
                                            tooltip "Choose a place for %s to live at (RMB to set Work)!" % c.nickname
                                        else: # Can't set home for free cs, they decide it on their own.
                                            action NullAction()
                                            tooltip "%s is free and decides on where to live at!" % c.nickname
                                        alternate [Function(c.set_flag, "last_chars_list_geet_icon", "work"),
                                                   Return(["dropdown", "workplace", c])]
                                        text "{image=button_circle_green}Home: [c.home]":
                                            if len(str(c.home)) > 18:
                                                size 15
                                            else:
                                                size 18
                                elif c.flag("last_chars_list_geet_icon") == "work":
                                    $ tt_hint = "Choose a place for %s to work at" % c.nickname
                                    if c.status == "slave":
                                        $ tt_hint += " (RMB to set Home)!"
                                    else:
                                        $ tt_hint += "!"
                                    button:
                                        style_group "ddlist"
                                        action Return(["dropdown", "workplace", c])
                                        if c.status == "slave":
                                            alternate [Function(c.set_flag, "last_chars_list_geet_icon", "home"),
                                                       Return(["dropdown", "home", c])]
                                        tooltip tt_hint
                                        text "{image=button_circle_green}Work: [c.workplace]":
                                            if len(str(c.workplace)) > 18:
                                                size 15
                                            else:
                                                size 18
                                button:
                                    style_group "ddlist"
                                    action Return(["dropdown", "action", c])
                                    tooltip "Choose a task for %s to do!" % c.nickname
                                    text "{image=button_circle_green}Action: [c.action]":
                                        if c.action is not None and len(str(c.action)) > 18:
                                            size 15
                                        else:
                                            size 18
                            else:
                                text "{size=15}Location: Unknown"
                                text "{size=15}Action: Hiding"

                    # Add to Group Button:
                    button:
                        style_group "basic"
                        xysize (25, 25)
                        align 1.0, 1.0 offset 9, -2
                        action ToggleSetMembership(CLS.the_chosen, c)
                        if c in CLS.the_chosen:
                            add(im.Scale('content/gfx/interface/icons/checkbox_checked.png', 25, 25)) align .5, .5
                        else:
                            add(im.Scale('content/gfx/interface/icons/checkbox_unchecked.png', 25, 25)) align .5, .5
                        tooltip 'Select the character'

    # Filters:
    frame:
        background Frame(Transform("content/gfx/frame/p_frame2.png", alpha=.55), 10 ,10)
        style_prefix "content"
        xmargin 0
        padding 5, 5
        pos (1005, 47)
        xysize (270, 468)
        vbox:
            xalign .5
            spacing 3
            label "Filters:":
                xalign .5
                text_size 35
                text_color goldenrod
                text_outlines [(1, "#000000", 0, 0)]

            hbox:
                xalign .5
                box_wrap True
                for f, c, t in [('Home', saddlebrown, 'Toggle home filters'),
                                ('Work', brown, 'Toggle workplace filters'),
                                ("Status", green, 'Toggle status filters'),
                                ("Action", darkblue, 'Toggle action filters'),
                                ('Class', purple, 'Toggle class filters')]:
                    button:
                        style_prefix "basic"
                        xpadding 6
                        xsize 100
                        action ToggleSetMembership(CLS.selected_filters, f)
                        tooltip t
                        text f color c size 18 outlines [(1, "#3a3a3a", 0, 0)]

                button:
                    style_group "basic"
                    xsize 100
                    action CLS.reset_filters
                    tooltip 'Reset all filters'
                    text "Reset"

            null height 3

            vpgrid:
                style_prefix "basic"
                xysize 256, 289
                xalign .5
                cols 2
                draggable True edgescroll (30, 100)
                if "Status" in CLS.selected_filters:
                    for f in CLS.status_filters:
                        button:
                            xysize 125, 32
                            action ModFilterSet(CLS.source, "status_filters", f)
                            text f.capitalize() color green
                            tooltip 'Toggle the filter'
                if "Home" in CLS.selected_filters:
                    for f in CLS.home_filters:
                        button:
                            xysize 125, 32
                            action ModFilterSet(CLS.source, "home_filters", f)
                            text "[f]" color saddlebrown:
                                if len(str(f)) > 12:
                                    size 10
                            tooltip 'Toggle the filter'
                if "Work" in CLS.selected_filters:
                    for f in CLS.work_filters:
                        button:
                            xysize 125, 32
                            action ModFilterSet(CLS.source, "work_filters", f)
                            text "[f]" color brown:
                                if len(str(f)) > 12:
                                    size 10
                                    line_spacing -6
                            tooltip 'Toggle the filter'
                if "Action" in CLS.selected_filters:
                    for f in CLS.action_filters:
                        button:
                            xysize 125, 32
                            action ModFilterSet(CLS.source, "action_filters", f)
                            $ t = str(f)
                            if t.lower().endswith(" job"):
                                $ t = t[:-4]
                            text "[t]" color darkblue:
                                if len(str(t)) > 12:
                                    size 10
                                    line_spacing -6
                            tooltip 'Toggle the filter'
                if "Class" in CLS.selected_filters:
                    for f in CLS.class_filters:
                        button:
                            xysize 125, 32
                            action ModFilterSet(CLS.source, "class_filters", f)
                            text "[f]" color purple
                            tooltip 'Toggle the filter'

    # Mass (de)selection Buttons ====================================>
    vbox:
        pos 1015, 518
        frame:
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.9), 10, 10)
            xysize (250, 50)
            style_prefix "basic"
            has hbox spacing 5 align .5, .5
            button: # select all on current listing, deselects them if all are selected
                xysize (66, 40)
                action Function(CLS.toggleChosenMembership, set(charz_list))
                sensitive num_chars != 0
                text "These"
                tooltip 'Select all currently visible characters'
            button: # every of currently filtered, also in next tabs
                xysize (66, 40)
                action Function(CLS.toggleChosenMembership, set(CLS.source.sorted))
                sensitive num_chars != 0
                text "All"
                tooltip 'Select all characters'
            button: # deselect all
                xysize (66, 40)
                action Function(CLS.the_chosen.clear)
                sensitive CLS.the_chosen
                text "None"
                tooltip "Clear Selection"

        # Mass action Buttons ====================================>
        frame:
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=.9), 10, 10)
            align .5, .5
            style_prefix "basic"
            xysize (250, 145)
            has vbox align .5, .5 spacing 3
            button:
                xysize (150, 40)
                action [SetVariable("char", PytGroup(CLS.the_chosen)), Show("char_control")]
                sensitive CLS.the_chosen
                text "Controls"
                selected False
                tooltip 'Set desired behavior for group'
            button:
                xysize (150, 40)
                action [Hide("chars_list"), With(dissolve), SetVariable("eqtarget", None), Jump('char_equip')]
                sensitive CLS.the_chosen
                text "Equipment"
                selected False
                tooltip "Manage Group's Equipment"
            button:
                xysize (150, 40)
                action [Hide("chars_list"), With(dissolve),
                          Jump('school_training')]
                sensitive CLS.the_chosen
                text "Training"
                selected False
                tooltip "Send the entire group to School!"

    use top_stripe(True)

    # Two buttons that used to be in top-stripe:
    hbox:
        style_group "basic"
        pos 300, 5
        spacing 3
        textbutton "<--":
            sensitive page > 0
            action SetScreenVariable("page", page-1)
            tooltip 'Previous page'
            keysym "mousedown_4"

        $ temp = page + 1
        textbutton "[temp]":
            xsize 40
            action NullAction()
        textbutton "-->":
            sensitive page < max_page
            action SetScreenVariable("page", page+1)
            tooltip 'Next page'
            keysym "mousedown_5"

    $ store.chars_list_last_page_viewed = page # At Darks Request!
