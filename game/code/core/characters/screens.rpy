screen new_style_tooltip():
    layer "tooltips"
    $ tooltip = GetTooltip()

    style_prefix "new_style_tooltip"

    # Get mouse coords:
    python:
        x, y = renpy.get_mouse_pos()
        xval = 1.0 if x > config.screen_width/2 else .0
        yval = 1.0 if y > config.screen_height/2 else .0

    if persistent.tooltips and tooltip:
        frame:
            pos (x, y)
            anchor (xval, yval)
            text "[tooltip]"

screen set_action_dropdown(char, pos=()):
    # Trying to create a drop down screen with choices of actions:
    zorder 3
    modal True

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

        if getattr(char.workplace, "is_school", False): #char.workplace should have the building ref, to be consistent with elif below
            textbutton "Change Course": #this should unenroll the student in current class
                action [Hide("set_action_dropdown"),
                        Hide("charslist"),
                        Hide("char_profile"),
                        SetField(store, "char", char, True),
                        Function(char.workplace.remove_student, char),
                        Jump("school_training")]
                tooltip "Change training course to a different one."
            textbutton "Stop Course": #this should also unenroll the student 
                action [SetField(char, "location", None),
                        SetField(char, "workplace", None),
                        SetField(char, "action", None),
                        Function(char.workplace.remove_student, char),
                        Hide("set_action_dropdown")]
                tooltip "Call your girl back from the Academy to do something useful in one of your businesses."
        elif isinstance(char.workplace, UpgradableBuilding):
            $ jobs = char.workplace.get_valid_jobs(char)
            if char != hero: # Rest is not really useful for MC, which player controls.
                $ jobs.append(simple_jobs["Rest"])
            for i in jobs:
                textbutton "[i.id]":
                    action [Function(set_char_to_work, char, char.workplace, i),
                            Hide("set_action_dropdown")]
                    tooltip i.desc
            textbutton "None":
                action [SetField(char, "action", None),
                        If(char_is_training(char), true=Function(stop_training, char)),
                        Hide("set_action_dropdown")]
                tooltip "In case you are in a great need of a slacker..."

        textbutton "Close":
            action [Hide("set_action_dropdown")]

    # use new_style_tooltip()

    key "K_ESCAPE" action [Hide("set_action_dropdown")]

screen set_workplace_dropdown(char, pos=()):
    # Trying to create a drop down screen with choices of actions:
    zorder 3
    modal True

    key "mousedown_4" action NullAction()
    key "mousedown_5" action NullAction()

    # Get mouse coords:
    python:
        x, y = pos
        xval = 1.0 if x > config.screen_width/2 else .0
        yval = 1.0 if y > config.screen_height/2 else .0

    python:
        workable_buildings = []
        for b in hero.buildings:
            if isinstance(b, UpgradableBuilding) and b.workable:
                workable_buildings.append(b)

    frame:
        style_prefix "dropdown_gm"
        pos (x, y)
        anchor (xval, yval)
        has vbox
        for building in workable_buildings:
            if char.action in building.jobs:
                $ can_keep_action = True
            else:
                $ can_keep_action = False
            textbutton "[building.name]":
                selected char.workplace == building
                action [If(char_is_training(char), true=Function(stop_training, char)),
                        If(not can_keep_action, true=SetField(char, "action", None)),
                        SetField(char, "workplace", building),
                        Hide("set_workplace_dropdown")]
        textbutton "None":
            selected char.workplace is None
            action [If(char_is_training(char), true=Function(stop_training, char)),
                    If(char.workplace.is_student(char), true=Function(char.workplace.remove_student, char)), #setting workplace to None should unenroll student
                    SetField(char, "workplace", None),
                    SetField(char, "action", None),
                    Hide("set_workplace_dropdown")]
        textbutton "Close":
            action Hide("set_workplace_dropdown")

    key "K_ESCAPE" action Hide("set_workplace_dropdown")

screen set_home_dropdown(char, pos=()):
    # Trying to create a drop down screen with choices of actions:
    zorder 3
    modal True

    key "mousedown_4" action NullAction()
    key "mousedown_5" action NullAction()

    # Get mouse coords:
    python:
        x, y = pos
        xval = 1.0 if x > config.screen_width/2 else .0
        yval = 1.0 if y > config.screen_height/2 else .0

    default habitable_locations = [b for b in hero.buildings if (b.habitable and b.vacancies)] + [locations["Streets"]]

    frame:
        style_prefix "dropdown_gm"
        pos (x, y)
        anchor (xval, yval)
        has vbox

        for loc in habitable_locations:
            textbutton "[loc]":
                selected char.home == loc
                action SetField(char, "home", loc), Hide("set_home_dropdown")
        textbutton "Close":
            action Hide("set_home_dropdown")

    key "K_ESCAPE" action Hide("set_home_dropdown")

screen char_rename(char=None):
    modal True
    zorder 1
    frame:
        if isinstance(char, Player):
            background Frame("content/gfx/frame/post_battle.png", 500, 400)
            xysize(500, 400)
        elif char.status != "slave":
            background Frame("content/gfx/frame/post_battle.png", 500, 300)
            xysize(500, 300)
        else:
            background Frame("content/gfx/frame/post_battle.png", 500, 500)
            xysize(500, 500)
        align (.5, .5)
        vbox:
            style_prefix "wood"
            at fade_in_out()
            align (.5, .5)
            spacing 10
            if isinstance(char, Player) or char.status == "slave":
                text "Name:" size 21 color goldenrod outlines [(2, "#3a3a3a", 0, 0)]
                button:
                    xysize (340, 60)
                    xalign 1.0
                    yalign .5
                    text "[char.name]" size 16 color goldenrod
                    action Return(["rename", "name"])
                    padding (10, 10)
            if not(isinstance(char, Player)): # it's weird to give a nickname to yourself. should be handled by ingame events
                text "Nickname:" size 21 color goldenrod outlines [(2, "#3a3a3a", 0, 0)]
                button:
                    xysize (340, 60)
                    xalign 1.0
                    yalign .5
                    if char.nickname != char.name:
                        text "[char.nickname]" size 16 color goldenrod
                    else:
                        text "None" size 16 color goldenrod
                    action Return(["rename", "nick"])
                    padding (10, 10)
            if isinstance(char, Player) or char.status == "slave":
                text "Full Name:" size 21 color goldenrod outlines [(2, "#3a3a3a", 0, 0)]
                button:
                    xysize (340, 60)
                    xalign 1.0
                    yalign .5
                    text "[char.fullname]" size 16 color goldenrod
                    action Return(["rename", "full"])
                    padding (10, 10)

            null height 20
            button:
                xysize (100, 50)
                xalign .5
                yalign .5
                text "Back" size 16 color goldenrod
                action Hide("char_rename")
                padding (10, 10)

    key "K_ESCAPE" action Hide("char_rename")

screen character_pick_screen(): # screen to select someone from the MC team
    key "mousedown_3" action Return(False)
    frame:
        align (.5, .5)
        xsize 450
        ysize 310
        padding(2, 2)
        background Frame("content/gfx/frame/frame_dec_1.png")
        label "Select a character" align (.5, .08) text_color "#DAA520" text_size 18
        hbox:
            spacing 45
            align (.5, .4)
            for l in hero.team:
                $ char_profile_img = l.show('portrait', resize=(101, 101), cache=True)
                $ img = "content/gfx/frame/ink_box.png"
                vbox:
                    spacing 1
                    xsize 102
                    imagebutton:
                        xalign .5
                        background Frame("content/gfx/frame/MC_bg3.png", 10, 10)
                        idle (char_profile_img)
                        hover (im.MatrixColor(char_profile_img, im.matrix.brightness(.15)))
                        action Return(l)
                        xysize (102, 102)
                    bar:
                        xalign .5
                        right_bar im.Scale("content/gfx/interface/bars/empty_bar2.png", 102, 14)
                        left_bar im.Scale("content/gfx/interface/bars/hp2.png", 102, 14)
                        value l.health
                        range l.get_max("health")
                        thumb None
                        left_gutter 0
                        right_gutter 0
                        xysize (102, 14)
                    bar:
                        xalign .5
                        right_bar im.Scale("content/gfx/interface/bars/empty_bar2.png", 102, 14)
                        left_bar im.Scale("content/gfx/interface/bars/mp2.png", 102, 14)
                        value l.mp
                        range l.get_max("mp")
                        thumb None
                        left_gutter 0
                        right_gutter 0
                        xysize (102, 14)
                    bar:
                        xalign .5
                        right_bar im.Scale("content/gfx/interface/bars/empty_bar2.png", 102, 14)
                        left_bar im.Scale("content/gfx/interface/bars/vitality2.png", 102, 14)
                        value l.vitality
                        range l.get_max("vitality")
                        thumb None
                        left_gutter 0
                        right_gutter 0
                        xysize (102, 14)
                    frame:
                        xalign .5
                        xsize 102
                        ysize 30
                        padding(2, 2)
                        background Frame("content/gfx/frame/gm_frame.png")
                        $ name = l.name[:8]
                        label "[name]" align (.5, .5) text_color "#DAA520" text_size 16

        vbox:
            style_group "wood"
            align (.5, .9)
            button:
                xysize (102, 40)
                yalign .5
                action Return(False)
                text "Cancel" size 15 color goldenrod
