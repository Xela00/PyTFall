label mc_setup:
    $ persistent.intro = True
    $ male_fighters, female_fighters = load_special_arena_fighters()

    # call build_mc_stories from _call_build_mc_stories

    scene bg mc_setup
    show screen mc_setup
    with dissolve
    play music "content/sfx/music/world/foregone.ogg" fadein 1.0 fadeout 1.0

    $ global_flags.set_flag("game_start")

    while 1:
        $ result = ui.interact()
        if isinstance(result, basestring):
            $ renpy.notify(traits[result].desc)

        elif result[0] == "control":
            if result[1] == "build_mc":
                python:
                    af = result[2]
                    del male_fighters[af.id]

                    hero._path_to_imgfolder = af._path_to_imgfolder
                    hero.id = af.id

                jump mc_setup_end

        elif result[0] == "rename":
            if result[1] == "name":
                $ n = renpy.call_screen("pyt_input", hero.name, "Enter Name", 20)
                if len(n):
                    $ hero.name = n
                    $ hero.nickname = hero.name
                    $ hero.fullname = hero.name
            if result[1] == "nick":
                $ n = renpy.call_screen("pyt_input", hero.name, "Enter Name", 20)
                if len(n):
                    $ hero.nickname = renpy.call_screen("pyt_input", hero.name, "Enter Nick Name", 20)
            if result[1] == "full":
                $ n = renpy.call_screen("pyt_input", hero.name, "Enter Full Name", 20)
                if len(n):
                    $ hero.fullname = n

label mc_setup_end:
    $ renpy.scene(layer='screens')
    scene black

    call set_mc_basetraits from _call_set_mc_basetraits

    # Call all the labels:
    python:
        """
        main_story: Merchant
        substory: Caravan
        mc_story: Defender
        mc_substory: Sword
        """
    $ hero.add_money(randint(2250, 2300), "Inheritance") # Barely enough to buy a slave and few items.

    $ temp = mc_stories[main_story].get('label', '')
    if "label" in temp and renpy.has_label(temp["label"]):
        call expression temp["label"] from _call_expression_2

    $ temp = mc_stories[main_story][sub_story].get('label', '')
    if renpy.has_label(temp):
        call expression temp from _call_expression_3

    $ temp = mc_stories[main_story]["MC"][sub_story][mc_story].get('label', '')
    if renpy.has_label(temp):
        call expression temp from _call_expression_4

    $ temp = mc_stories[main_story]["MC"][sub_story][mc_story][mc_substory].get('label', '')
    if renpy.has_label(temp):
        call expression temp from _call_expression_5

    $ restore_battle_stats(hero) # We never really want to start with weakened MC?

    python hide:
        high_factor = partial(uniform, .5, .6)
        normal_factor = partial(uniform, .35, .45)

        base_stats = hero.stats.get_base_stats()
        for s in ['constitution', 'intelligence', 'charisma', 'attack', 'magic', 'defence', 'agility']:
            if s in base_stats:
                value = high_factor()
                mod_by_max(hero, s, value)
            else:
                value = normal_factor()
                set_stat_to_percentage(hero, s, value)

        base_skills = hero.stats.get_base_skills()
        for s in base_skills:
            value = high_factor()+.2
            set_stat_to_percentage(hero, s, value)

    # Add default workable building to MC, but only if we didn't add one in special labels.
    if not [b for b in hero.upgradable_buildings if b.workable]:
        python hide:
            # Find the cheapest business
            scary = None 
            for b in businesses.values():
                if ((not scary) or scary.price > b.price):
                    scary = b
            if scary:
                scary.normalize_jobs()
                hero.add_building(scary)

    # Add Home apartment (Slums) to MC, unless we have set him up with a home in special labels.
    python hide:
        if not hero.home:
            # Find the cheapest building
            for b in buildings.values():
                if ((not hero.home) or hero.home.price > b.price):
                    hero.home = b
            if hero.home:
                hero.add_building(hero.home)

    # Set the default battle skill:
    if not hero.attack_skills:
        $ hero.attack_skills.append(hero.default_attack_skill)

    $ hero.init()
    $ hero.log_stats()

    python:
        del temp
        del mc_stories
        del main_story
        del sub_story
        del mc_story
        del mc_substory

    return

label set_mc_basetraits:
    # We build the MC here. First we get the classes player picked in the choices screen and add those to MC:
    python:
        temp = set()
        bt1 = mc_stories[main_story][sub_story].get("class", None) or mc_stories[main_story].get("class", None)
        bt2 = mc_stories[main_story]["MC"][sub_story][mc_story][mc_substory].get("class", None) or mc_stories[main_story]["MC"][sub_story][mc_story].get("class", None)
        temp = [t for t in (bt1, bt2) if t is not None]

    python:
        for t in temp:
            hero.traits.basetraits.add(traits[t])
            hero.apply_trait(traits[t])
    return

init: # MC Setup Screens:
    screen mc_setup():

        default sprites = male_fighters.values()
        default index = 0
        default left_index = -1
        default right_index = 1

        # Rename and Start buttons + Classes are now here as well!!!:
        if all([(hasattr(store, "mc_substory") and store.mc_substory)]):
            textbutton "{size=40}{color=[white]}{font=fonts/TisaOTB.otf}Start Game" at fade_in_out():
                background Transform(Frame("content/gfx/interface/images/story12.png", 5, 5), alpha=1)
                hover_background Transform(Frame(im.MatrixColor("content/gfx/interface/images/story12.png", im.matrix.brightness(.15)), 5, 5), alpha=1)
                align (.46, .93)
                action [Stop("music"), Return(["control", "build_mc", sprites[index]])]
        vbox:
            # align (.37, .10)
            pos (365, 68)
            hbox:
                textbutton "{size=20}{font=fonts/TisaOTM.otf}{color=[goldenrod]}Name:":
                    background Transform(Frame("content/gfx/interface/images/story12.png", 5, 5), alpha=.8)
                    hover_background Transform(Frame(im.MatrixColor("content/gfx/interface/images/story12.png", im.matrix.brightness(.15)), 5, 5), alpha=1)
                    xpadding 12
                    ypadding 8
                textbutton "{size=20}{font=fonts/TisaOTM.otf}{color=[white]}[hero.name]":
                    background Transform(Frame("content/gfx/interface/images/story12.png", 5, 5), alpha=.8)
                    hover_background Transform(Frame(im.MatrixColor("content/gfx/interface/images/story12.png", im.matrix.brightness(.15)), 5, 5), alpha=1)
                    xpadding 12
                    ypadding 8

            textbutton "{size=20}{font=fonts/TisaOTM.otf}{color=[red]}Click to change name":
                background Transform(Frame("content/gfx/interface/images/story12.png", 5, 5), alpha=.8)
                hover_background Transform(Frame(im.MatrixColor("content/gfx/interface/images/story12.png", im.matrix.brightness(.15)), 5, 5), alpha=1)
                xpadding 12
                ypadding 8
                align (.0, .10)
                action Show("char_rename", char=hero)

        # MC Sprites:
        hbox:
            spacing 4
            align (.463, .75)
            $ img = ProportionalScale("content/gfx/interface/buttons/blue_arrow_left.png", 40, 40)
            imagebutton:
                idle img
                hover im.MatrixColor(img, im.matrix.brightness(.20))
                activate_sound "content/sfx/sound/sys/hover_2.wav"
                action [SetScreenVariable("index", (index - 1) % len(sprites)),
                        SetScreenVariable("left_index", (left_index - 1) % len(sprites)),
                        SetScreenVariable("right_index", (right_index - 1) % len(sprites))]
            $ img = ProportionalScale("content/gfx/interface/buttons/blue_arrow_right.png", 40, 40)
            textbutton "{size=20}{font=fonts/TisaOTM.otf}{color=[white]}Select your appearance":
                background Transform(Frame("content/gfx/interface/images/story12.png", 5, 5), alpha=.8)
                hover_background Transform(Frame(im.MatrixColor("content/gfx/interface/images/story12.png", im.matrix.brightness(.15)), 5, 5), alpha=1)
                xpadding 12
                ypadding 8
            imagebutton:
                idle img
                hover im.MatrixColor(img, im.matrix.brightness(.20))
                activate_sound "content/sfx/sound/sys/hover_2.wav"
                action [SetScreenVariable("index", (index + 1) % len(sprites)),
                        SetScreenVariable("left_index", (left_index + 1) % len(sprites)),
                        SetScreenVariable("right_index", (right_index + 1) % len(sprites))]
        frame:
            align .328, .53
            xysize (160, 220)
            background Frame("content/gfx/frame/MC_bg3.png", 40, 40)
            add im.Sepia(sprites[left_index].show("battle_sprite", resize=(140, 190))) align .5, .4
        frame:
            align .586, .53
            xysize (160, 220)
            background Frame("content/gfx/frame/MC_bg3.png", 40, 40)
            add im.Sepia(sprites[right_index].show("battle_sprite", resize=(140, 190))) align .5, .4
        frame:
            align .457, .36
            xysize (160, 220)
            background Frame("content/gfx/frame/MC_bg3.png", 40, 40)
            add sprites[index].show("battle_sprite", resize=(150, 200)) align .5, .4
        frame:
            pos 713, 37
            background Frame("content/gfx/frame/MC_bg.png", 10, 10)
            add sprites[index].show("portrait", resize=(100, 100))

        ### Background Story ###
        add "content/gfx/interface/images/story1.png" align (.002, .09)

        frame: # Text frame for Main Story (Merchant, Warrior, Scholar and Noble)
            background Frame(Transform("content/gfx/interface/images/story12.png", alpha=.8), 10, 10)
            pos 173, 16 anchor .5, .0
            padding 15, 10
            # xysize (150, 40)
            text ("{size=20}{font=fonts/TisaOTm.otf}Select your origin") # align (.53, .4)

        hbox: # Fathers Main occupation:
            style_group "sqstory"
            pos (30, 65)
            spacing 17
            $ ac_list = [Hide("mc_stories"), Hide("mc_sub_stories"), Hide("mc_sub_texts"),
                         SetVariable("sub_story", None), SetVariable("mc_story", None),
                         SetVariable("mc_substory", None)]
            for branch in mc_stories:
                $ img = im.Scale(mc_stories[branch]["img"], 50, 50, align=(.5, .5))
                button: ## Merchant ##
                    foreground im.Sepia(img, align=(.5, .5))
                    selected_foreground img
                    idle_foreground im.Sepia(img, align=(.5, .5))
                    hover_foreground im.MatrixColor(img, im.matrix.brightness(.15), align=(.5, .5))
                    if mc_stories[branch].get("header", ""):
                        action SelectedIf(main_story == branch), If(store.main_story == branch,
                                  false=ac_list + [SetVariable("main_story", branch),
                                   Show("mc_stories", transition=dissolve, choices=mc_stories[branch])])

    screen mc_texts():
        tag mc_texts
        frame:
            pos (0, 350)
            ysize 370
            background Frame(Transform("content/gfx/frame/MC_bg.png", alpha=1), 30, 30)
            has vbox xsize 350
            if main_story in mc_stories:
                $ temp = mc_stories[main_story].get('header', "Add 'header' to {} story!".format(main_story))
                text "[temp]" xalign .5 font "fonts/DeadSecretary.ttf" size 22
                $ temp = mc_stories[main_story].get("text", False)
                if temp:
                    text "[temp]" style "garamond" size 18
                null height 15
                vbox:
                    if sub_story in mc_stories[main_story]:
                        text ("%s" % mc_stories[main_story][sub_story]["text"]) style "garamond" size 18
            else:
                text "No [main_story] story found!!!" align (.5, .5)

    screen mc_stories(choices=OrderedDict()): # This is the fathers SUB occupation choice.
        tag mc_sub
        hbox:
            pos(0, 145)
            style_group "mcsetup"
            box_wrap True
            xsize 360
            $ img_choices = choices["choices"]
            for key in img_choices:
                python:
                    if choices["MC"][key].get("choices", ""):
                        # greycolor = False
                        sepia = False
                    else:
                        # greycolor = True
                        sepia = True
                    img = im.Scale(im.Sepia(img_choices[key]) if sepia else img_choices[key], 39, 39)
                button:
                    if img_choices.keys().index(key) % 2:
                        text key align (1.0, .52)
                            # if greycolor:
                                # color grey
                        add img align (.0, .5)
                    else:
                        text key align (.0, .52)
                        add img align (1.0, .5)
                    action SensitiveIf(not sepia), SelectedIf(store.sub_story==key), If(store.sub_story==key, false=[Hide("mc_sub_texts"), Hide("mc_texts"),
                                  SetVariable("mc_story", None), SetVariable("mc_substory", None), SetVariable("sub_story", key),
                                  Show("mc_texts", transition=dissolve),
                                  Show("mc_sub_stories", transition=dissolve, choices=mc_stories[main_story]["MC"][key]["choices"])])

    screen mc_sub_stories(choices=OrderedDict()): # This is the MC occupation choice.
        if choices:
            hbox:
                pos 870, 50
                spacing 10
                for i in ["l", "r"]:
                    if choices.get(i, ""):
                        vbox:
                            spacing 2
                            $ img = ProportionalScale(choices["".join([i, "_img"])], 150, 150, align=(.5, .5))
                            if not choices[i] == mc_story:
                                $ img = im.Sepia(img, align=(.5, .5))
                            button:
                                xalign .5
                                xysize (165, 165)
                                background Frame("content/gfx/frame/MC_bg.png", 10, 10)
                                idle_foreground img
                                hover_foreground im.MatrixColor(img, im.matrix.brightness(.10), align=(.5, .5))
                                action Hide("mc_sub_texts"), SetVariable("mc_story", choices[i]), SetVariable("mc_substory", None), Show("mc_sub_texts", transition=dissolve)
                            hbox:
                                xalign .5
                                spacing 1
                                style_group "sqstory"
                                for sub in xrange(3):
                                    $ sub = str(sub)
                                    if choices.get(i + sub, ""):
                                        $ img = ProportionalScale(choices["".join([i, sub, "_img"])], 46, 46, align=(.5, .5))
                                        if not mc_substory == choices[i + sub]:
                                            $ img = im.Sepia(img, align=(.5, .5))
                                        button:
                                            # foreground img
                                            # idle_foreground im.Sepia(img, align=(.5, .5))
                                            # hover_foreground im.MatrixColor(img, im.matrix.brightness(.15), align=(.5, .5))
                                            background Frame("content/gfx/frame/MC_bg.png", 10, 10)
                                            idle_foreground im.Sepia(img, align=(.5, .5))
                                            hover_foreground im.MatrixColor(img, im.matrix.brightness(.15), align=(.5, .5))
                                            selected_foreground img
                                            action SetVariable("mc_substory", choices[i + sub]), SensitiveIf(choices[i] == mc_story), SelectedIf(mc_substory == choices[i + sub]), Show("mc_sub_texts", transition=dissolve)

    screen mc_sub_texts():
        tag mc_subtexts
        frame:
            background Frame(Transform("content/gfx/frame/MC_bg.png", alpha=1), 30, 30)
            anchor (1.0, 1.0)
            pos (1280, 721)
            xysize (450, 440)
            # xmargin 20
            has vbox xmaximum 430 xfill True xalign .5
            $ texts = mc_stories[main_story]["MC"][sub_story][mc_story]
            if "header" in texts:
                text ("{font=fonts/DeadSecretary.ttf}{size=28}%s" % texts["header"]) xalign .5
            else:
                text "Add Header text!"
            null height 10
            if "text" in texts:
                text ("%s" % texts["text"]) style "garamond" size 18
            else:
                text "Add Main Text!"
            null height 20
            if mc_substory in texts:
                text ("{font=fonts/DeadSecretary.ttf}{size=23}%s" % mc_substory) xalign .5
                null height 5
                text ("%s" % texts[mc_substory]["text"]) style "garamond" size 18
