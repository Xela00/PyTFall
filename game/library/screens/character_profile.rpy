label char_profile:
    
    if not hasattr(store, "girls") or girls is None or char not in girls:
        $ girls = list(girl for girl in hero.chars if girl.action != "Exploring")
    
    scene bg scroll
    $ renpy.retain_after_load()
    show screen char_profile
    with dissolve
    
    while 1:
        $ result = ui.interact()
        
        if isinstance(result, (list, tuple)):
            # If the girl has runaway
            if char in pytfall.ra:
                if result[0] == "girl":
                    if result[1] == "gallery":
                        $ gallery = PytGallery(char)
                        jump gallery
                    
                    elif result[1] == "get_rid":
                        if renpy.call_screen("yesno_prompt", message="Are you sure you wish to stop looking for %s?"%char.name, yes_action=Return(True), no_action=Return(False)):
                            python:
                                hero.remove_char(char)
                                girls.remove(char)
                                char.dispoition -= 300
                                if char in hero.team: hero.team.remove(char)
                            if girls:
                                $ index = (index+1) % len(girls)
                                $ char = girls[index]
                            else:
                                jump char_profile_end
                    else:
                        $ renpy.show_screen("message_screen", "This girl has run away!")
                
                elif result[0] != "control":
                    $ renpy.show_screen("message_screen", "This girl has run away!")
            
            # Else if you still have the girl
            else:
                if result[0] == "jump":
                    if result[1] == "item_transfer":
                        hide screen char_profile
                        $ items_transfer([hero, char])
                        show screen char_profile
                
                elif result[0] == "dropdown":
                    python:
                        if result[1] == "loc":
                            renpy.show_screen("set_location_dropdown", result[2], pos=renpy.get_mouse_pos())
                        elif result[1] == "action":
                            renpy.show_screen("set_action_dropdown", result[2], pos=renpy.get_mouse_pos())
                
                elif result[0] == "girl":
                    if result[1] == "gallery":
                        $ gallery = PytGallery(char)
                        jump gallery
                    elif result[1] == "it": # THIS IS WTF???
                        $ raise Exception("MEOW")
                        $ pytfall.it = GuiItemsTransfer("personal_transfer", char=char, last_label=last_label)
                        jump items_transfer
                    elif result[1] == "get_rid":
                        if char.status == "slave":
                            $ message = "Are you sure you wish to sell {} for {}?".format(char.name, int(char.fin.get_price()*0.8))
                        else:
                            $ message = "Are you sure that you wish to fire {}?".format(char.name)
                        if renpy.call_screen("yesno_prompt",
                                                        message=message,
                                                        yes_action=Return(True), no_action=Return(False)):
                            if char.status == 'slave':
                                $ hero.add_money(int(char.fin.get_price()*0.8), reason="SlaveTrade")
                                $ char.location = 'slavemarket'
                            else:
                                $ char.location = 'city'
                            python:    
                                hero.remove_char(char)
                                index = girls.index(char) # Index is not set otherwise???
                                girls.remove(char)
                                char.disposition -= 300
                            if char in hero.team:
                                $ hero.team.remove(char)
                            if girls:
                                $ index = (index + 1) % len(girls)
                                $ char = girls[index]
                            else:
                                jump girls_profile_end
                                
                    # elif result[1] == 'buyrank':
                        # # Should prolly move this to the Girl method at some point:
                        # # TODO: Update to skills (Refinement!)
                        # # No Longer in use!!!
                        # python:
                            # targetrank = char.rank + 1
                            # maxrank = max(b.maxrank for b in hero.brothels)
                            # if targetrank > 3 and char.status == "slave":
                                # renpy.call_screen('message_screen', "Slave Girls cannot be pushed past rank 3!")
                            # elif targetrank > maxrank:
                                # renpy.call_screen('message_screen', "You do not currently own any brothels to justify ranking a prostitute to Rank %d" % targetrank)
                            # else:    
                                # rankinfo = char.wranks['r%d' % targetrank]
                    
                                # if char.exp >= rankinfo['exp']:
                                    # if char.refinement >= rankinfo['ref']:
                                        # if hero.take_money(rankinfo['price'], reason="Prositute Ranks"):
                                            # char.rank += 1
                                            # char.stats.max['refinement'] += 15
                                     
                            # del maxrank
                            # del targetrank
                            
                elif result[0] == "rename":
                    if result[1] == "name":
                        $ char.name = renpy.call_screen("pyt_input", char.name, "Enter Name", 20)
                    if result[1] == "nick":
                        $ char.nickname = renpy.call_screen("pyt_input", char.name, "Enter Nick-Name", 20)
                    if result[1] == "full":
                        $ char.fullname = renpy.call_screen("pyt_input", char.name, "Enter Full-Name", 20)
            
            if result[0] == 'control':
                $ index = girls.index(char)
                if result[1] == 'left':
                   $ index = (index - 1) % len(girls)
                   $ char = girls[index]
                elif result[1] == 'right':
                    $ index = (index + 1) % len(girls)
                    $ char = girls[index]
                    
                elif result[1] == 'return':
                    jump char_profile_end

label char_profile_end:
    hide screen char_profile
    
    $ girls = None
    
    if char_profile:
        $ last_label, char_profile = char_profile, None
        jump expression last_label
    else:
        jump chars_list
                
screen char_profile():

    key "mousedown_4" action Return(["control", "right"])
    key "mousedown_5" action Return(["control", "left"])
    
    if girls:
        # text ("{color=[ivory]}[char.desc]") style "content_text" layout "greedy" justify True minwidth 304 xalign 0.5
        default tt = Tooltip("[char.desc]")
    else:
        default tt = Tooltip("Manage your girls here!!!")
    default stats_display = "main"
    
    $ not_escaped = char not in pytfall.ra
    
    if girls:
        # Picture and left/right buttons ====================================>
        if True:
            add "content/gfx/frame/p_frame6.png" xalign 0.487 yalign 0.185 size (613, 595)
            # Alex: Code by Gismo, messy but gets the job done, I actually have no idea of how to get this done with just one frame and the image...
            # Vbox is just for more convenient positioning.
            vbox:
                align (0.487, 0.184) #0.487, 0.164
                yfill True
                ymaximum 514 #569
                if check_friends(hero, char) or check_lovers(char, hero):
                    python:
                        frame_image = im.Scale("content/gfx/frame/MC_bg3.png", 1, 1)
                        img = char.show('profile', resize=(600, 514), cache=True)
                else:
                    python:
                        frame_image = im.Scale("content/gfx/frame/MC_bg3.png", 1, 1)
                        img = char.show('profile', resize=(600, 514), exclude=["revealing", "lingerie", "swimsuit"], cache=True)
                button:
                    align (0.5, 0.5)
                    idle_background frame_image
                    idle_foreground Transform(img, align=(0.5, 0.5))
                    
                    hover_background im.MatrixColor(frame_image, im.matrix.brightness(0.1))
                    hover_foreground Transform(im.MatrixColor(img, im.matrix.brightness(0.1)), align=(0.5, 0.5))
                    
                    insensitive_background frame_image
                    insensitive_foreground Transform(img, align=(0.5, 0.5))
                    frame:
                        align(0.5, 0.5)
                        background Frame("content/gfx/frame/MC_bg3.png", 10 ,10)
                        add img align(0.5, 0.5)#ProportionalScale(img, 600, 514) align(0.5, 0.5)
                    if check_friends(hero, char) or check_lovers(char, hero):
                        action If(not_escaped, true=[Hide("char_profile"), With(dissolve), Function(gm.start_int, char, img=char.show("girlmeets", resize=gm.img_size))], false=NullAction())
                    else:
                        action If(not_escaped, true=[Hide("char_profile"), With(dissolve), Function(gm.start_int, char, img=char.show("girlmeets", exclude=["revealing", "lingerie", "swimsuit"], resize=gm.img_size))], false=NullAction())
                    
                    hovered tt.action("Interact with [char.nickname]!")
                
            frame:
                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=0.9), 10, 10)
                xalign 0.489
                ypos 560
                xysize (628, 64)
                hbox:
                    xalign 0.46
                    yalign 0.5
                    button:
                        xysize (140, 40)
                        style "left_wood_button"
                        action Return(['control', 'left'])
                        hovered tt.action("<== Previous Girl")
                        text "Previous Girl" style "wood_text" xalign(0.69)
                    
                    null width 280
                    
                    button:
                        xysize (140, 40)
                        style "right_wood_button"
                        action Return(['control', 'right'])
                        hovered tt.action("Next Girl ==>")
                        text "Next Girl" style "wood_text" xalign(0.19)  
        
        # Left Frame with most of the info ====================================>
        frame:
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=0.98), 10, 10)
            xysize (330, 780)
            xanchor 0.01
            ypos 30
            style_group "content"
            has vbox
            null height 7
            # Base frame ====================================> 
            fixed:
                $ trait = char.personality
                $ img = ProportionalScale("".join(["content/gfx/interface/images/personality/", trait.id.lower(), ".png"]), 120, 120)
                imagebutton:
                    at pers_effect()
                    xcenter 60
                    ycenter 65
                    idle img
                    hover img
                    hovered tt.Action("{=library_book_header_main}{color=[blue]}{size=17}%s{/=}{/color}{/size}"%trait.id + "\n" + trait.desc)
                    action NullAction()
                align (.0, .0)
                xysize (330, 126)
                add Transform("content/gfx/frame/base_frame.png", alpha=0.9, size=(330, 126))

                    
                label "[char.name]":
                    text_color gold
                    text_outlines [(2, "#424242", 0, 0)]
                    pos 118, 47
                    anchor 0, 1.0
                    if len(char.name) < 20:
                        text_size 21
                # background Frame (Transform("content/gfx/frame/namebox5.png", alpha=0.95), 250, 50)
                # label "{color=[gold]}[char.name]":
                    # text_color ivory text_outlines [(2, "#424242", 0, 0)]
                    # align (0.5, 0.5)
                    # if len(char.name) < 20:
                        # text_size 21
                
            null height 5
            # Rank up for prostitutes:
            # TODO: Adapt ranks to new skills code!
            # @Review: Will not be used until further notice!
            # if traits['Prostitute'] in char.occupations:
                # frame:
                    # xanchor -0.01
                    # xysize(313, 47)
                    # background Frame("content/gfx/frame/rank_frame.png", 10, 10)
                    # text ('%s:'%char.wranks['r%s'%char.rank]['name'][0]) align(0.1, 0.2) color ivory size 16
                    # text ('%s'%char.wranks['r%s'%char.rank]['name'][1]) align(0.5, 0.96) color ivory size 16
                    # if char.rank < 8:
                        # $ rankinfo = char.wranks['r%d' % (char.rank+1)]                                
                        # imagebutton:
                            # align (0.95, 0.5)
                            # hover "rank_up"
                            # if char.refinement >=rankinfo['ref'] and char.exp >= rankinfo['exp']:
                                # idle "rank_up"
                                # action Return(['girl', 'buyrank'])
                                # hovered tt.Action("Increase this girl's Rank. Rank is one of the most important things for a girl in a brothel to have. \nTo achieve next rank your girl requires: %d of Refinement, %d of Experience and a sum of %d gold."%(rankinfo['ref'], rankinfo['exp'], rankinfo['price']))
                            # else:
                                # idle im.Sepia("content/gfx/animations/rank_up/1.png")
                                # action NullAction()
                                # hovered tt.Action("[char.nickname] does not meet the requirements for a rank up.\nRank is one of the most important things for a girl in a brothel to have. \nTo achieve next rank your girl requires: %d of Refinement, %d of Experience and a sum of %d gold."%(rankinfo['ref'], rankinfo['exp'], rankinfo['price']))

            null height 8

            # Stats/Info ====================================>
            fixed:
                xanchor -0.01
                xysize (300, 60)
                vbox:
                    # Prof-Classes ====================================>
                    python:
                        if len(char.traits.basetraits) == 1:
                            classes = list(char.traits.basetraits)[0].id
                        elif len(char.traits.basetraits) == 2:
                            classes = list(char.traits.basetraits)
                            classes.sort()
                            classes = ", ".join([str(c) for c in classes])
                        else:
                            raise Exception("Character without prof basetraits detected! line: 267, girlsprofile screen")
                    button:
                        xmargin 0
                        xpadding 0
                        ypadding 0
                        action NullAction()
                        background Null()
                        text "Classes: [classes]" color ivory size 18
                        
                    null height 2
                    
                    button:
                        style_group "ddlist"
                        action Return(["dropdown", "loc", char])
                        hovered tt.Action("Choose a location for %s to work at!" % char.nickname)
                        text "{image=content/gfx/interface/icons/move15.png}Location: [char.location]":
                            if len(str(char.location)) > 18:
                                size 15
                            else:
                                size 18
                    button:
                        style_group "ddlist"
                        action Return(["dropdown", "action", char])
                        hovered tt.Action("Choose a task for %s to do!" % char.nickname)
                        text "{image=content/gfx/interface/icons/move15.png}Action: [char.action]":
                            if char.action is not None and len(str(char.action)) > 18:
                                size 15
                            else:
                                size 18
                    
                imagebutton:
                    align(0.99, 0.45)
                    if char.status == "slave":
                        idle ProportionalScale("content/gfx/interface/icons/slave.png", 50, 50)
                        hover (im.MatrixColor(ProportionalScale("content/gfx/interface/icons/slave.png", 50, 50), im.matrix.brightness(0.25)))
                        hovered tt.Action("This girl is a slave!")
                    else:
                        idle ProportionalScale("content/gfx/interface/icons/free.png", 50, 50)
                        hover (im.MatrixColor(ProportionalScale("content/gfx/interface/icons/free.png", 50, 50), im.matrix.brightness(0.25)))
                        hovered tt.Action("This girl is free as a bird :)")
                    action NullAction()
                    
            null height 5
            hbox:
                style_group "basic"
                xalign 0.5
                button:
                    yalign 0.5
                    action SetScreenVariable("stats_display", "main"), With(dissolve)
                    text "Main" size 15
                button:
                    yalign 0.5
                    action SetScreenVariable("stats_display", "stats"), With(dissolve)
                    text "Stats" size 15
                button:
                    yalign 0.5
                    action SetScreenVariable("stats_display", "pro_stats"), With(dissolve)
                    text "Pro Stats" size 15
                if config.developer:
                    button:
                        yalign 0.5
                        action SetScreenVariable("stats_display", "skillstest"), With(dissolve)
                        text "S" size 15
                        
            null height 4
            vbox:
                style_prefix "proper_stats"
                xsize 318
                if stats_display == "main":
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=0.6), 10, 10)
                        xpadding 12
                        ypadding 12
                        xmargin 0
                        ymargin 0
                        has vbox spacing 1
                        frame:
                            xalign 0.0
                            yfill True
                            background Frame (Transform("content/gfx/frame/MC_bg3.png", alpha=0.6), 10, 10)
                            xysize (145, 30)
                            text (u"{color=#CDAD00} Full name") font "fonts/Rubius.ttf" size 20 outlines [(1, "#3a3a3a", 0, 0)] align (0.5, 0.7)
                        frame:
                            xpadding 10
                            has vbox box_wrap True xmaximum 250
                            xalign .0
                            ysize 25
                            text "[char.fullname]" xalign .0 yalign 0.5 style "TisaOTM" color "#79CDCD" size 15
                        null height 5
                        frame:
                            xalign 0.0
                            yfill True
                            background Frame (Transform("content/gfx/frame/MC_bg3.png", alpha=0.6), 10, 10)
                            xysize (145, 30)
                            text (u"{color=#CDAD00} Race") font "fonts/Rubius.ttf" size 20 outlines [(1, "#3a3a3a", 0, 0)] align (0.5, 0.7)
                        vbox:
                            frame:
                                xpadding 10
                                has vbox box_wrap True xmaximum 250
                                xalign .0
                                ysize 25
                                text "[char.full_race]" xalign .0 yalign 0.5 style "TisaOTM" color "#79CDCD" size 15
                            null height 1
                            frame:
                                xysize (100, 100)
                                $ trait = char.race
                                $ img = ProportionalScale(trait.icon, 100, 100)
                                add img
                    
                    # Basetraits:
                    vbox:
                        xsize 315
                        xfill True
                        fixed:
                            xysize (300, 70)
                            yfill True
                            for trait in sorted(list(char.traits.basetraits)):
                                $ temp = (0.7, 0.9) if sorted(list(char.traits.basetraits)).index(trait) else (0.3, 0.1)
                                textbutton "[trait]" action NullAction() hovered tt.action(trait.desc) align temp
                                
                    null height 4

                    
                elif stats_display == "stats":
                    frame:
                        style_suffix "main_frame"
                        xsize 318
                        has vbox spacing 1
                        $ stats = ["charisma", "character", "reputation", "constitution", "joy", "intelligence", "disposition"]
                        frame:
                            xoffset 4
                            xysize (290, 27)
                            xpadding 7
                            text "Health:" color "#CD4F39"
                            if char.health <= char.get_max("health")*0.3:
                                text (u"{color=[red]}%s/%s"%(char.health, char.get_max("health"))) xalign 1.0 style_suffix "value_text"
                            else:
                                text (u"%s/%s"%(char.health, char.get_max("health"))) xalign 1.0 style_suffix "value_text"
                        frame:
                            xoffset 4
                            xysize (290, 27)
                            xpadding 7
                            text "Vitality:" color "#43CD80"
                            if char.vitality < char.get_max("vitality")*0.3:
                                text (u"{color=[red]}%s/%s"%(char.vitality, char.get_max("vitality"))) xalign 1.0 style_suffix "value_text"
                            else:
                                text (u"%s/%s"%(char.vitality, char.get_max("vitality"))) xalign 1.0 style_suffix "value_text"
                        for stat in stats:
                            frame:
                                xoffset 4
                                xysize (290, 27)
                                xpadding 7
                                text '{}'.format(stat.capitalize()) color "#79CDCD"
                                text ('%d/%d'%(getattr(char, stat), char.get_max(stat))) xalign 1.0 style_suffix "value_text"
                        frame:
                            xoffset 4
                            xysize (290, 27)
                            xpadding 7
                            text "Gold:" color gold
                            text (u"{color=[gold]}[char.gold]") xalign 1.0 style_suffix "value_text"
                            
                    label (u"{size=20}{color=[ivory]}{b}Info:") xalign .48 text_outlines [(2, "#424242", 0, 0)]
                    frame:
                        background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=0.6), 10, 10)
                        xsize 318
                        padding 12, 12
                        has vbox spacing 1
                        frame:
                            xoffset 4
                            xysize (290, 27)
                            xpadding 7
                            text "{color=#79CDCD}Upkeep:"
                            text u"%s"%(char.fin.get_upkeep()) xalign 1.0 style_suffix "value_text"
                        if char.status == "slave":
                            frame:
                                xoffset 4
                                xysize (290, 27)
                                xpadding 7                          
                                text "{color=#79CDCD}Market Price:"
                                text (u"%s"%(char.fin.get_price())) xalign 1.0 style_suffix "value_text"
                        if traits['Prostitute'] in char.occupations:
                            frame:
                                xoffset 4
                                xysize (290, 27)
                                xpadding 7
                                text "{color=#79CDCD}Work Price:"
                                text (u"%s"%(char.fin.get_whore_price())) xalign 1.0 style_suffix "value_text"
                            
                ##############################################################################
                # Stats 2 (pro)
                elif stats_display == "pro_stats": 
                    label (u"{size=20}{color=[ivory]}{b}Battle Stats:") xalign(0.48) text_outlines [(2, "#424242", 0, 0)]
                    frame:
                        style_suffix "main_frame"
                        xsize 318
                        has vbox spacing 1
                        $ stats = [("Attack", "#CD4F39"), ("Defence", "#dc762c"), ("Magic", "#8470FF"), ("MP", "#009ACD"), ("Agility", "#1E90FF"), ("Luck", "#00FA9A")]
                        for stat, color in stats:
                            frame:
                                xoffset 4
                                xysize (290, 27)
                                xpadding 7
                                text "[stat]" color color
                                text "{}/{}".lower().format(getattr(char, stat.lower()), char.get_max(stat.lower())) style_suffix "value_text" color color
                                
                    null height 4
                    
                    # Elements:
                    $ els = [Transform(e.icon, size=(90, 90)) for e in char.elements]
                    frame:
                        style_group "content"
                        background Frame(Transform("content/gfx/frame/ink_box.png", alpha=0.5), 10, 10)
                        xysize (300, 130)
                        ymaximum 120
                        xalign 0.5
                        
                        $ x = 0
                        $ els = [Transform(i, crop=(90/len(els)*els.index(i), 0, 90/len(els), 90), subpixel=True, xpos=(x + 90/len(els)*els.index(i))) for i in els]
                        $ f = Fixed(*els, xysize=(90, 90))
                        add f xcenter 230 ycenter 58
                        
                        viewport:
                            draggable True
                            edgescroll (20, 10)
                            xysize (200, 102)
                            yalign 0.5
                            has vbox spacing -10
                            for e in char.elements:
                                textbutton "{=TisaOTM}[e.id]":
                                    background None
                                    action NullAction()
                                    hovered tt.Action("%s" % e.desc)
                        add ProportionalScale("content/gfx/interface/images/elements/hover.png", 90, 90) pos (185, 12)
                                        
                elif stats_display == "skillstest":
                    frame:
                        style_suffix "main_frame"
                        xsize 318
                        has viewport scrollbars "vertical" xysize(310, 392) mousewheel True child_size (300, 1000)
                        vbox spacing 1:
                            for skill in char.stats.skills:
                                $ skill_val = int(char.get_skill(skill))
                                if config.debug or skill_val > char.level * 10:
                                    frame:
                                        xoffset 4
                                        xysize (270, 27)
                                        xpadding 7    
                                        text "{}:".format(skill.capitalize())
                                        text "{true} <{action}, {training}>".format(true=skill_val, action=int(char.stats.skills[skill][0]), training=int(char.stats.skills[skill][1])) style_suffix "value_text"

        # Level, experience ====================================>
        fixed:
            xalign 0.490
            ypos 570
            xysize (360, 45)
            add(ProportionalScale("content/gfx/frame/level.png", 360, 45)) align(0.5, 0.5)
            text("{font=fonts/Rubius.ttf}{color=[ivory]}{size=16}{b}[char.level]") pos(106, 7)
            text("{font=fonts/Rubius.ttf}{color=[ivory]}{size=16}{b}[char.exp]") pos(190, 7)
            text("{font=fonts/Rubius.ttf}{color=[ivory]}{size=16}{b}[char.goal]") pos(190, 27)

            
        # Right frame ====================================>
        frame:
            ypos 38
            xalign 1.0
            xysize (345, 586)
            background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=0.98), 10, 10)
            has vbox spacing 1
            null height 1
            
            # Buttons ====================================>
            frame:
                background Frame(Transform("content/gfx/frame/p_frame5.png", alpha=0.9), 10, 10)
                xalign 0.5
                # ypos 5
                xysize (325, 150)
                has hbox style_group "wood" align .5, .5 spacing 5
                    
                vbox:
                    spacing 5
                    button:
                        xysize (150, 40)
                        action If(not_escaped, true=Show("girl_control"))
                        hovered tt.action('Set desired behaviour for [char.nickname].')
                        text "Girl Control"
                    button:
                        xysize (150, 40)
                        action If(not_escaped, true=[Hide("char_profile"), With(dissolve), SetVariable("eqtarget", char), Jump('char_equip')])
                        hovered tt.action('Access girls inverntory and equipment screen!')
                        text "Equipment"
                    button:
                        xysize (150, 40)
                        action [Hide("char_profile"), With(dissolve), Return(["girl", "gallery"])]
                        hovered tt.action("View this girl's gallery!")
                        text "Gallery"
            
                vbox:
                    spacing 5
                    button:
                        xysize (150, 40)
                        action If(not_escaped, true=[Hide("char_profile"), With(dissolve), Jump('girl_training')])
                        hovered tt.action("Send her to School!")
                        text "Training"
                    button:
                        xysize (150, 40)
                        action If(not_escaped, true=Show("girl_finances"))
                        hovered tt.action("Review Finances!")
                        text "Finances"
                    button:
                        xysize (150, 40)
                        action If(not_escaped, true=Return(["girl", "get_rid"]))
                        hovered tt.action("Get rid of her!")
                        text "Get Rid"
            
            # AP ====================================>
            frame:
                xalign 0.5
                # ypos 160
                xysize (300, 90)
                background ProportionalScale("content/gfx/frame/frame_ap.png", 300, 100)
                label ("[char.AP]"):
                    pos (200, 0)
                    style "content_label"
                    text_color ivory
                    text_size 28
            
            # Traits/Effects/Attacks/Magix ====================================>
            null height -25
            frame:
                background Frame(Transform("content/gfx/frame/p_frame4.png", alpha=0.6))
                xsize 335
                style_group "proper_stats"
                xanchor 1
                ypadding 7
                xpadding 8
                has vbox xoffset 3 spacing 2
                # Traits/Effects ====================================>
                hbox:
                    # Traits:
                    vbox:
                        xysize (160, 190)
                        label (u"Traits:") text_size 20 text_color ivory text_bold True xalign .5
                        viewport:
                            xysize (160, 155)
                            scrollbars "vertical"
                            draggable True
                            mousewheel True
                            has vbox spacing 1
                            for trait in list(t for t in char.traits if not any([t.basetrait, t.personality, t.race, t.elemental])):
                                if not trait.hidden:
                                    frame:
                                        xsize 147
                                        button:
                                            background Null()
                                            xsize 147
                                            action NullAction()
                                            text trait.id idle_color ivory size 15 align .5, .5 hover_color crimson text_align .5
                                            hovered tt.Action(u"%s"%trait.desc)
                                            hover_background Frame(im.MatrixColor("content/gfx/interface/buttons/choice_buttons2h.png", im.matrix.brightness(0.10)), 5, 5)
                    # Effects:
                    vbox:
                        xysize (160, 190)
                        label (u"Effects:") text_size 20 text_color ivory text_bold True xalign .5
                        viewport:
                            xysize (160, 155)
                            scrollbars "vertical"
                            draggable True
                            mousewheel True
                            has vbox spacing 1
                            for effect, val in char.effects.iteritems():
                                if val['active']:
                                    frame:
                                        xysize (147, 25)
                                        button:
                                            background Null()
                                            xysize (147, 25)
                                            action NullAction()
                                            text "[effect]" idle_color ivory size 15 align .5, .5 hover_color crimson
                                            hovered tt.Action(u"%s"%val.get("desc", "No Description availible."))
                                            hover_background Frame(im.MatrixColor("content/gfx/interface/buttons/choice_buttons2h.png", im.matrix.brightness(0.10)), 5, 5)
                    
                # Attacks/Magic ====================================>
                hbox:
                    vbox:
                        xysize (160, 146)
                        label (u"Attack:") text_size 20 text_color ivory text_bold True xalign .5 text_outlines [(3, "#3a3a3a", 0, 0), (2, "#8B0000", 0, 0), (1, "#3a3a3a", 0, 0)]
                        viewport:
                            xysize (160, 104)
                            scrollbars "vertical"
                            draggable True
                            mousewheel True
                            has vbox spacing 1
                            for entry in char.attack_skills:
                                frame:
                                    xysize (147, 25)
                                    button:
                                        background Null()
                                        xysize (147, 25)
                                        action NullAction()
                                        text "[entry.name]" idle_color ivory size 15 align .5, .5 hover_color crimson
                                        hovered tt.action(entry.desc)
                                        hover_background Frame(im.MatrixColor("content/gfx/interface/buttons/choice_buttons2h.png", im.matrix.brightness(0.10)), 5, 5)
            
                    vbox:
                        xysize (160, 146)
                        xanchor 5
                        label (u"Magic:") text_size 20 text_color ivory text_bold True xalign .5 text_outlines [(3, "#3a3a3a", 0, 0), (2, "#104E8B", 0, 0), (1, "#3a3a3a", 0, 0)]
                        viewport:
                            xysize (160, 104)
                            scrollbars "vertical"
                            draggable True
                            mousewheel True
                            has vbox spacing 1
                            for entry in char.magic_skills:
                                frame:
                                    xysize (147, 25)
                                    button:
                                        background Null()
                                        xysize (147, 25)
                                        action NullAction()
                                        text "[entry.name]" idle_color ivory size 15 align .5, .5 hover_color crimson
                                        hovered tt.action(entry.desc)
                                        hover_background Frame(im.MatrixColor("content/gfx/interface/buttons/choice_buttons2h.png", im.matrix.brightness(0.10)), 5, 5)
                            
        # Tooltip ====================================>
        frame:
            background Frame("content/gfx/frame/black_frame.png")
            pos 325, 622
            xpadding 10
            xysize (951, 100)
            has hbox spacing 1
            if isinstance(tt.value, BE_Action):
                $ element = tt.value.get_element()
                if element:
                    frame:
                        background Frame("content/gfx/frame/MC_bg3.png", 10, 10)
                        xysize (70, 70)
                        if element.icon:
                            $ img = ProportionalScale(element.icon, 70, 70)
                            add img align (0.5, 0.5)
                text tt.value.desc style "content_text" size 20 color ivory yalign 0.1
            else:
                text (u"{=content_text}{color=[ivory]}%s" % tt.value)
            
    use top_stripe(True)
    
screen girl_control():
    default char = PytGroup(the_chosen) if the_chosen else char
    modal True
    zorder 1
    
    default cb_checked = im.Scale('content/gfx/interface/icons/checkbox_checked.png', 25, 25)
    default cd_unchecked = im.Scale('content/gfx/interface/icons/checkbox_unchecked.png', 25, 25)
    default cb_some_checked = im.Scale('content/gfx/interface/icons/checkbox_some_checked.png', 25, 25)
    
    frame:
        style_group "content"
        at slide(so1=(600, 0), t1=0.7, eo2=(1300, 0), t2=0.7)
        background Frame("content/gfx/frame/p_frame52.png", 10, 10)
        xpos 936
        yalign 0.95
        xysize(343, 675)
        
        # Tooltip Related:
        default tt = Tooltip("Adjust your girls behaviour here.")
        frame:
            background Frame (Transform("content/gfx/frame/p_frame4.png", alpha=0.6), 10, 10)
            align(0.5, 0.88)
            xysize (320, 120)
            xpadding 13
            ypadding 15
            has vbox
            text (u"{color=[ivory]}%s" % tt.value) outlines [(1, "#424242", 0, 0)]
        
        frame:
            background Frame (Transform("content/gfx/frame/p_frame5.png", alpha=0.7), 10, 10)
            align (0.6, 0.08)
            xpadding 10
            ypadding 10
            xysize (225, 120)
            button:
                style_group "basic"
                xysize (150, 33)
                align (0.5, 0.05)
                action ToggleDict(char.autocontrol, "Tips")
                hovered tt.action("Allow workers to keep their tips!")
                text "Tips:" align (0.0, 0.5)
                if isinstance(char.autocontrol["Tips"], list):
                    add cb_some_checked align (1.0, 0.5)
                elif char.autocontrol['Tips']:
                    add cb_checked align (1.0, 0.5)
                else:
                    add cd_unchecked align (1.0, 0.5)

            fixed:
                align (0.5, 1.0)
                xysize (200, 30)
                hbox:
                    align (0.5, 0.0)
                    vbox:
                        xmaximum 130
                        xfill True
                        text (u"{color=[ivory]}Wage percentage:") outlines [(1, "#424242", 0, 0)]
                    vbox:
                        text "{color=[ivory]}[char.wagemod]%" outlines [(1, "#424242", 0, 0)]
                bar:
                    align (0.5, 1.0)
                    value FieldValue(char, 'wagemod', 200, max_is_zero=False, style='scrollbar', offset=0, step=1)
                    xmaximum 150
                    thumb 'content/gfx/interface/icons/move15.png'
                         
        # BE Row, Job controls + Auto-Buy/Equip
        vbox:
            style_group "basic"
            align (0.55, 0.5)
            button:
                action If(char.status not in ("slave", "various"), true=ToggleField(char, "front_row"))
                xysize (200, 32)
                text "Front Row" align (0.0, 0.5)
                if isinstance(char.front_row, list):
                    add cb_some_checked align (1.0, 0.5)
                elif char.front_row:
                    add cb_checked align (1.0, 0.5)
                elif not char.front_row:
                    add cd_unchecked align (1.0, 0.5)
            
            button:
                action ToggleDict(char.autocontrol, "Rest")
                xysize (200, 32)
                text "Auto Rest" align (0.0, 0.5)
                if isinstance(char.autocontrol['Rest'], list):
                    add cb_some_checked align (1.0, 0.5)
                elif char.autocontrol['Rest']:
                    add cb_checked align (1.0, 0.5)
                elif not char.autocontrol['Rest']:
                    add cd_unchecked align (1.0, 0.5)
             
            # Autobuy: 
            button:
                action  If(char.status not in ("slave", "various") and char.disposition > 950, true=ToggleField(char, "autobuy"))
                xysize (200, 32)
                text "Auto Buy" align (0.0, 0.5)
                if isinstance(char.autobuy, list):
                    add cb_some_checked align (1.0, 0.5)
                elif char.autobuy:
                    add cb_checked align (1.0, 0.5)
                else:
                    add cd_unchecked align (1.0, 0.5)
                    
            # Autoequip
            button:
                xysize (200, 32)
                action If(char.status == "slave" or char.disposition > 850, true=ToggleField(char, "autoequip"))
                text "Auto Equip" align (0.0, 0.5)
                if isinstance(char.autoequip, list):
                    add cb_some_checked align (1.0, 0.5)
                elif char.autoequip:
                    add cb_checked align (1.0, 0.5)
                else:
                    add cd_unchecked align (1.0, 0.5)
            # ------------------------------------------------------------------------------------------------------------------------------------->>>        
            null height 10
            if not isinstance(char, PytGroup) and char.status !="slave" and any(trait in char.traits for trait in ["Prostitute", "Stripper"]):
                button:
                    xysize (200, 32)
                    action If(char.disposition > 850, true=ToggleField(char, "master"))
                    if char.gender == "Female":
                        text "Dominatrix" align (0.0, 0.5)
                    else:
                        text "Master" align (0.0, 0.5)
                    if isinstance(char.master, list):
                        add cb_some_checked align (1.0, 0.5)
                    elif char.master:
                        add cb_checked align (1.0, 0.5)
                    else:
                        add cd_unchecked align (1.0, 0.5)

            null height 10
            if all("Prostitute" in c.traits for c  in char.lst) if isinstance(char, PytGroup) else "Prostitute" in char.traits:
                for act in char.sex_acts:
                    button:
                        xysize (200, 32)
                        action ToggleDict(char.sex_acts, act)
                        text act align (0.0, 0.5)
                        if isinstance(char.sex_acts[act], list):
                            add cb_some_checked align (1.0, 0.5)
                        elif char.sex_acts[act]:
                            add cb_checked align (1.0, 0.5)
                        else:
                            add cd_unchecked align (1.0, 0.5)
        
        button:
            style_group "basic"
            action Hide("girl_control")
            minimum(50, 30)
            align (0.5, 0.95)
            text  "OK"
        
screen confirm_girl_sale():
    modal True
    zorder 1
    
    frame:
        align(0.5, 0.5)
        minimum(300, 200)
        maximum(300, 200)
        xfill True
        yfill True
        
        if char.status == "slave":
            text("{size=-5}Are you sure you want to sell [char.name] for %d Gold?"%(int(char.fin.get_price()*0.8))) align(0.5, 0.1)
            
            hbox:
                align(0.5, 0.85)
                spacing 40
                textbutton "No":
                    action Hide("confirm_girl_sale")
                textbutton "Yes":
                    action Return(['control', 'sell'])
            
        else:
            text("{size=-5}Are you sure you want to fire the %s?"%char.name) align(0.5, 0.1)
            
            hbox:
                align(0.5, 0.85)
                spacing 40
                textbutton "No":
                    action Hide("confirm_girl_sale")
                textbutton "Yes":
                    action Return(['control', 'fire'])
        

screen girl_finances():
    modal True
    zorder 1
    
    default show_fin = "day"
    
    frame:
        at slide(so1=(0, 700), t1=0.7, so2=(0, 0), t2=0.3, eo2=(0, -config.screen_height))
        background Frame (Transform("content/gfx/frame/arena_d.png", alpha=1.2), 5, 5)
        align (0.5, 0.5)
        
        # side "c r":
        viewport id "message_vp":
            style_group "stats"
            xysize (1100, 600)
            draggable False
            mousewheel True
            if day > 1 and char.fin.game_fin_log.has_key(str(day-1)):
                $ fin_inc = char.fin.game_fin_log[str(day-1)][0]
                $ fin_exp = char.fin.game_fin_log[str(day-1)][1]
                
                if show_fin == 'day':
                    label (u"{color=[ivory]}Fin Report (Yesterday)") xalign 0.4 ypos 30 text_size 30
                    # Income:
                    vbox:
                        pos (50, 100)
                        label "Income:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in fin_inc["work"]:
                                    text ("[key]")
                                for key in fin_inc["tips"]:
                                    text ("[key]")
                                for key in fin_inc:
                                    if key not in ["work", "tips", "private"]:
                                        text ("[key]")
                            vbox:
                                null height 1
                                spacing 4
                                for key in fin_inc["work"]:
                                    $ val = fin_inc["work"][key]
                                    text "[val]" style "stats_value_text"
                                for key in fin_inc["tips"]:
                                    $ val = fin_inc['tips'][key]
                                    text "[val]" style "stats_value_text"
                                for key in fin_inc:
                                    if key not in ["work", "tips", "private"]:
                                        $ val = fin_inc[key]
                                        text "[val]" style "stats_value_text"
                    # Expense:
                    vbox:
                        pos (450, 100)
                        label "Expense:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in fin_exp["cost"]:
                                    text ("[key]")
                            vbox:
                                null height 1
                                spacing 4
                                for key in fin_exp["cost"]:
                                    $ val = fin_exp["cost"][key]
                                    text ("[val]") style "stats_value_text"
                                    
                    python:
                        total_list = list(itertools.chain(fin_inc["work"].values(),
                                                                      fin_inc["tips"].values()))
                        total_income = sum(total_list)
                        total_expenses = 0
                        for key in fin_exp["cost"]:
                            total_expenses += fin_exp["cost"][key]
                        total = total_income - total_expenses
                        
                    vbox:
                        align (0.80, 0.60)
                        text "----------------------------------------"
                        text ("Revenue: [total]"):
                            size 20
                            xpos 15
                            if total > 0:
                                color lawngreen style "stats_value_text"
                            else:
                                color red style "stats_value_text"
                            
                    hbox:
                        style_group "basic"
                        align (0.5, 0.9)
                        textbutton "Show Total" action SetScreenVariable("show_fin", 'total') minimum (200, 30)
                        textbutton "Show Personal" action SetScreenVariable("show_fin", 'personal') minimum (200, 30)
                        textbutton "Show P. Total" action SetScreenVariable("show_fin", 'personal_total') minimum (200, 30)
                    
                elif show_fin == 'total':
                    label (u"Fin Report (Game)") xalign 0.4 ypos 30 text_size 30
                    python:
                        income = dict()
                        for _day in char.fin.game_fin_log:
                            for key in char.fin.game_fin_log[_day][0]["work"]:
                                income[key] = income.get(key, 0) + char.fin.game_fin_log[_day][0]["work"][key]
                            for key in char.fin.game_fin_log[_day][0]["tips"]:
                                income[key] = income.get(key, 0) + char.fin.game_fin_log[_day][0]["tips"][key]
                                
                    # Income:
                    vbox:
                        pos (50, 100)
                        label "Income:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in income:
                                    text "[key]"
                            vbox:
                                null height 1
                                spacing 4
                                for key in income:
                                    $ val = income[key]
                                    text "[val]" style "stats_value_text"
                                    
                    # Expense:
                    python:
                        expenses = dict()
                        for _day in char.fin.game_fin_log:
                            for key in char.fin.game_fin_log[_day][1]["cost"]:
                                expenses[key] = expenses.get(key, 0) + char.fin.game_fin_log[_day][1]["cost"][key]
                    vbox:
                        pos (450, 100)
                        label "Expense:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in expenses:
                                    text ("[key]")
                            vbox:
                                null height 1
                                spacing 4
                                for key in expenses:
                                    $ val = expenses[key]
                                    text ("[val]") style "stats_value_text"
                                
                    python:
                        game_total = 0
                        for _day in char.fin.game_fin_log:
                            total_list = list(itertools.chain(char.fin.game_fin_log[_day][0]["work"].values(),
                                                                          char.fin.game_fin_log[_day][0]["tips"].values()))
                            total_income = sum(total_list)
                            total_expenses = 0
                            for key in char.fin.game_fin_log[_day][1]["cost"]:
                                total_expenses += char.fin.game_fin_log[_day][1]["cost"][key]
                            total = total_income - total_expenses
                            game_total += total
                    vbox:
                        align (0.80, 0.60)
                        text "----------------------------------------"
                        text ("Revenue: [game_total]"):
                            size 20
                            xpos 15
                            if game_total > 0:
                                color lawngreen style "stats_value_text"
                            else:
                                color red style "stats_value_text"
                        
                    hbox:
                        style_group "basic"
                        align (0.5, 0.9)
                        textbutton "Show Daily" action SetScreenVariable("show_fin", 'day') minimum(200, 30)
                        textbutton "Show Personal" action SetScreenVariable("show_fin", 'personal') minimum(200, 30)
                        textbutton "Show P. Total" action SetScreenVariable("show_fin", 'personal_total') minimum(200, 30)
                    
                elif show_fin == 'personal':
                    label (u"Personal (Yesterday)") xalign 0.4 ypos 30 text_size 30
                    
                    # Income:
                    vbox:
                        pos (50, 100)
                        label "Income:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in fin_inc["private"]:
                                    text ("[key]")
                            vbox:
                                null height 1
                                spacing 4
                                for key in fin_inc["private"]:
                                    $ val = fin_inc["private"][key]
                                    text ("[val]") style "stats_value_text"
                     
                    # Expense:
                    vbox:
                        pos (450, 100)
                        label "Expense:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in fin_exp["private"]:
                                    text ("[key]")
                            vbox:
                                null height 1
                                spacing 4
                                for key in fin_exp["private"]:
                                    $ val = fin_exp["private"][key]
                                    text ("[val]") style "stats_value_text"
                                
                    python:
                        total_income = 0
                        for key in fin_inc["private"]:
                            total_income += fin_inc["private"][key]
                        total_expenses = 0
                        for key in fin_exp["private"]:
                            total_expenses += fin_exp["private"][key]
                        total = total_income - total_expenses
                    vbox:
                        align (0.80, 0.60)
                        text "----------------------------------------"
                        text ("Revenue: [total]"):
                            size 20
                            xpos 15
                            if total > 0:
                                color lawngreen style "stats_value_text"
                            else:
                                color red style "stats_value_text"

                    hbox:
                        style_group "basic"
                        align (0.5, 0.9)
                        textbutton "Show Total" action SetScreenVariable("show_fin", 'total') minimum(200, 30)
                        textbutton "Show Daily" action SetScreenVariable("show_fin", 'daily') minimum(200, 30)
                        textbutton "Show P. Total" action SetScreenVariable("show_fin", 'personal_total') minimum(200, 30)
                    
                elif show_fin == 'personal_total':
                    label (u"Personal (Total)") xalign 0.4 ypos 30 text_size 30
                    
                    python:
                        income = dict()
                        for _day in char.fin.game_fin_log:
                            for key in char.fin.game_fin_log[_day][0]["private"]:
                                income[key] = income.get(key, 0) + char.fin.game_fin_log[_day][0]["private"][key]
                                    
                    # Income:
                    vbox:
                        pos (50, 100)
                        label "Income:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in income:
                                    text ("[key]")
                            vbox:
                                null height 1
                                spacing 4
                                for key in income:
                                    $ val = income[key]
                                    text ("[val]") style "stats_value_text"
                      
                    # Expense:
                    python:
                        expenses = dict()
                        for _day in char.fin.game_fin_log:
                            for key in char.fin.game_fin_log[_day][1]["private"]:
                                expenses[key] = expenses.get(key, 0) + char.fin.game_fin_log[_day][1]["private"][key]
                    vbox:
                        pos (450, 100)
                        label "Expense:" text_size 20
                        null height 10
                        hbox:
                            vbox:
                                xmaximum 150
                                xfill True
                                for key in expenses:
                                    text ("[key]")
                            vbox:
                                null height 1
                                spacing 4
                                for key in expenses:
                                    $ val = expenses[key]
                                    text ("[val]") style "stats_value_text"
                                
                    python:
                        total_income = sum(income.values())
                        total_expenses = sum(expenses.values())
                        game_total = total_income - total_expenses
                    vbox:
                        align (0.80, 0.60)
                        text "----------------------------------------"
                        text ("Revenue: [game_total]"):
                            size 20
                            xpos 15
                            if game_total > 0:
                                color lawngreen style "stats_value_text"
                            else:
                                color red style "stats_value_text"
                        
                    hbox:
                        style_group "basic"
                        align (0.5, 0.9)
                        textbutton "Show Daily" action SetScreenVariable("show_fin", 'day') minimum(200, 30)
                        textbutton "Show Peronal" action SetScreenVariable("show_fin", 'personal') minimum(200, 30)
                        textbutton "Show Total" action SetScreenVariable("show_fin", 'total') minimum(200, 30)
                    
            else:
                text (u"No financial records availible!") align (0.5, 0.5)

            button:
                style_group "basic"
                action Hide('girl_finances')
                minimum (250, 30)
                align (0.5, 0.96)
                text "OK"
