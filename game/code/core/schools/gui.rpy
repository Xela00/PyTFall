label school_training:
    $ school = schools.values().pop()
    show screen school_training

    while 1:
        $ result = ui.interact()

        if result[0] == "set_course":
            # add_student ? 
            $ result[1].add_student(char) #I think this is the right thing to pass to add_student
            # I guess just jump back after setting the course? 
            jump return_from_school_training

        if result == ["control", "return"]:
            jump return_from_school_training

label return_from_school_training:
    hide screen school_training

    if the_chosen == None:
        jump char_profile
    else:
        jump chars_list

init python:
    def school_desc_string():
        temp = []
        temp.append("The Beautiful educational facilities in PyTFall offer any")
        temp.append("training one may require for free citizens,")
        temp.append("foreigners and slaves alike. Century old traditions will make sure")
        temp.append("that no girl taking classes here will ever be sad or unhappy.")
        temp.append("Nothing in this world is free however, so courses here")
        temp.append("might cost you a dime and if you wish to be trained")
        temp.append("by the Masters, a small fortune.")
        rv = " ".join(temp)

        return rv

screen school_training():
    # School info:
    frame:
        style_prefix "content"
        background Frame("content/gfx/frame/mes12.jpg", 10, 10)
        pos 8, 48
        padding 10, 10
        xysize (500, 666)
        has vbox
        null height 3
        label ("[school.name]") xalign .5 text_color ivory text_size 25
        null height 3
        frame:
            xalign .5
            background Null()
            foreground Frame("content/gfx/frame/MC_bg2.png", 10, 10)
            add ProportionalScale(school.img, 450, 300)
        null height 8
        default desc = school_desc_string()
        text "[desc]" color ivory
        null height 3
        text "Girls currently taking courses here:" color ivory
        null height 3
        viewport:
            xsize 580
            draggable False
            mousewheel True
            scrollbars "vertical"
            vbox:
                xmaximum 610
                spacing 10
                for c in list(c for c in chain.from_iterable(course.students for course in school.courses)):
                    hbox:
                        fixed:
                            xsize 180
                            text (u"[c.fullname]:") color ivory
                        text (u"[c.action]") color ivory

    frame:
        style_prefix "content"
        background Frame("content/gfx/frame/mes11.webp", 10, 10)
        xpos 1280-8 xanchor 1.0 ypos 48
        padding 10, 10
        xysize (760, 666)
        has viewport draggable 1 mousewheel 1 scrollbars "vertical"
        hbox:
            xsize 720 box_wrap 1
            for course in school.courses:
                button:
                    style "mmenu1_button"
                    margin 2, 2
                    padding 5, 5
                    xysize 180, 350
                    action Return(['set_course', course])#NullAction() #this should be replaced with something to select the school?
                    tooltip course.tooltip
                    vbox:
                        xalign .5
                        spacing 2
                        text course.name + " Course" xalign .5 color ivory style "dropdown_gm2_button_value_text"
                        frame:
                            xalign .5
                            background Null()
                            foreground Frame("content/gfx/frame/MC_bg2.png", 10, 10)
                            add ProportionalScale(course.img, 150, 150)
                    text "---------------------------------":
                        xalign .5
                        color ivory
                        ypos 190
                    vbox:
                        ypos 205
                        xalign .5
                        style_prefix "proper_stats"
                        frame:
                            xysize (160, 20)
                            xalign .5
                            text "Days Left":
                                xalign .02
                                color "#79CDCD"
                                hover_color ivory
                                size 15
                            text "[course.duration]/[course.days_remaining]":
                                style_suffix "value_text"
                                hover_color green
                                size 14
                                xalign .99 yoffset -1
                        frame:
                            xysize (160, 20)
                            xalign .5
                            text "Days to Complete":
                                xalign .02
                                color "#79CDCD"
                                hover_color ivory
                                size 15
                            $ days_left = course.days_to_complete - course.students_progress.get(char, 0)
                            text "[days_left]/[course.days_to_complete]":
                                style_suffix "value_text"
                                if char.tier <= course.difficulty:
                                    hover_color green
                                else:
                                    hover_color red
                                size 14
                                xalign .99 yoffset -1
                        frame:
                            xysize (160, 20)
                            xalign .5
                            text "Tier":
                                xalign .02
                                color "#79CDCD"
                                hover_color ivory
                                size 15
                            text "[course.difficulty]":
                                style_suffix "value_text"
                                if char.tier <= course.difficulty:
                                    hover_color green
                                else:
                                    hover_color red
                                size 14
                                xalign .99 yoffset -1
                        frame:
                            xysize (160, 20)
                            xalign .5
                            text "Effectiveness":
                                xalign .02
                                color "#79CDCD"
                                hover_color ivory
                                size 15
                            text "[course.effectiveness]":
                                style_suffix "value_text"
                                hover_color green
                                size 14
                                xalign .99 yoffset -1
                        frame:
                            xysize (160, 20)
                            xalign .5
                            text "Price":
                                xalign .02
                                color "#79CDCD"
                                hover_color ivory
                                size 15
                            text "[course.price]":
                                style_suffix "value_text"
                                hover_color green
                                size 14
                                xalign .99 yoffset -1
                        frame:
                            xysize (160, 20)
                            xalign .5
                            text "Status":
                                xalign .02
                                color "#79CDCD"
                                hover_color ivory
                                size 15
                            $ status = course.get_status(char)
                            text "[status]":
                                style_suffix "value_text"
                                hover_color green
                                size 14
                                xalign .99 yoffset -1

                    if char in course.completed:
                        add pscale("content/gfx/interface/images/completed_stamp.webp", 130, 130):
                            xalign .5 ypos 210



    use top_stripe(True)
