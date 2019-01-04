#####################################################################################################
#
#Credits:
#    SusanTheCat - the original code for jigsaw puzzle
#
#    PyTom - "image location picker" code
#
#
#####################################################################################################

init python:

    def piece_dragged(drags, drop):

        if not drop:
            return

        p_x = drags[0].drag_name[0]
        p_y = drags[0].drag_name[1]
        t_x = drop.drag_name[0]
        t_y = drop.drag_name[1]

        a = []
        a.append(drop.drag_joined)
        a.append((drags[0], 3, 3))
        drop.drag_joined(a)

        if p_x == t_x and p_y == t_y:
            renpy.music.play("content/sfx/sound/jp/Pat.mp3", channel="sound")
            my_x = int(int(p_x)*active_area_size*x_scale_index)-int(grip_size*x_scale_index)+puzzle_field_offset
            my_y = int(int(p_y)*active_area_size*y_scale_index)-int(grip_size*y_scale_index)+puzzle_field_offset
            drags[0].snap(my_x,my_y, delay=.1)
            drags[0].draggable = False
            placedlist[int(p_x),int(p_y)] = True

            for i in range(0, grid_width):
                for j in range(0, grid_height):
                    if not placedlist[i, j]:
                        return
            return True
        return


label jigsaw_puzzle_start:
    hide screen gallery
    scene bg jigsaw
    with dissolve

    $ grid_width = 3       # default value
    $ grid_height = 3       # default value
    $ puzzle_field_size = 655       # should be less then minimal of config.screen_width and config.screen_height values
    $ puzzle_field_offset = 50       # the offset from top left corner
    $ puzzle_piece_size = 450       # the size of stencil images that are used to create puzzle piece
    $ grip_size = 75       # see "_how_to_make_a_tile.png" file
    $ active_area_size = puzzle_piece_size - (grip_size * 2)

    $ img_to_play  = ProportionalScale("/".join([gallery.girl.path_to_imgfolder, gallery.imagepath]), puzzle_field_size, puzzle_field_size)
    $ img_width, img_height = img_to_play.true_size()
    $ renpy.call_screen("control_scr", img_to_play)
    # $ chosen_img = jigsaw_img

    python:

        # img_width, img_height = renpy.image_size(chosen_img)
#
        # # scales down an image to fit the puzzle_field_size
        # if img_width >= img_height and img_width > puzzle_field_size:
            # img_scale_down_index = round( (1.00 * puzzle_field_size / img_width), 6)
            # img_to_play = im.FactorScale(chosen_img, img_scale_down_index)
            # img_width = int(img_width * img_scale_down_index)
            # img_height = int(img_height * img_scale_down_index)
#
        # elif img_height >= img_width and img_height > puzzle_field_size:
            # img_scale_down_index = round( (1.00 * puzzle_field_size / img_height), 6)
            # img_to_play = im.FactorScale(chosen_img, img_scale_down_index)
            # img_width = int(img_width * img_scale_down_index)
            # img_height = int(img_height * img_scale_down_index)
#
        # else:
            # img_to_play = chosen_img
#
        x_scale_index = round( (1.00 * (img_width/grid_width)/active_area_size), 6)
        y_scale_index = round( (1.00 * (img_height/grid_height)/active_area_size), 6)

        # mainimage = im.Composite((int(img_width+(grip_size*2)*x_scale_index), int(img_height+(grip_size*2)*y_scale_index)),(int(grip_size*x_scale_index), int(grip_size*y_scale_index)), img_to_play)
        mainimage = im.Composite((int(img_width+(grip_size*2)*x_scale_index), int(img_height+(grip_size*2)*y_scale_index)),(int(grip_size*x_scale_index), int(grip_size*y_scale_index)), img_to_play)
        # some calculations
        top_row = []
        for i in range (0, grid_width):
            top_row.append(i)

        bottom_row = []
        for i in range (0, grid_width):
            bottom_row.append(grid_width*(grid_height-1)+i)

        left_column = []
        for i in range (0, grid_height):
            left_column.append(grid_width*i)

        right_column = []
        for i in range (0, grid_height):
            right_column.append(grid_width*i + (grid_width-1) )

        # randomly makes the shape of each puzzle piece
        # (starts from top row, fills it in from left to right, then - next row)
        jigsaw_grid = []
        for i in range(0,grid_height):
            for j in range (0,grid_width):
                jigsaw_grid.append([9,9,9,9])   # [top, right, bottom, left]

        for i in range(0,grid_height):
            for j in range (0,grid_width):
                if grid_width*i+j not in top_row:
                    if jigsaw_grid[grid_width*(i-1)+j][2] == 1:
                        jigsaw_grid[grid_width*i+j][0] = 2
                    else:
                        jigsaw_grid[grid_width*i+j][0] = 1
                else:
                    jigsaw_grid[grid_width*i+j][0] = 0

                if grid_width*i+j not in right_column:
                    jigsaw_grid[grid_width*i+j][1] = randint(1,2)
                else:
                    jigsaw_grid[grid_width*i+j][1] = 0

                if grid_width*i+j not in bottom_row:
                    jigsaw_grid[grid_width*i+j][2] = randint(1,2)
                else:
                    jigsaw_grid[grid_width*i+j][2] = 0

                if grid_width*i+j not in left_column:
                    if jigsaw_grid[grid_width*i+j-1][1] == 1:
                        jigsaw_grid[grid_width*i+j][3] = 2
                    else:
                        jigsaw_grid[grid_width*i+j][3] = 1
                else:
                    jigsaw_grid[grid_width*i+j][3] = 0


        # makes description for each puzzle piece
        piecelist = dict()
        imagelist = dict()
        placedlist = dict()
        testlist = dict()

        for i in range(0,grid_width):
            for j in range (0,grid_height):
                piecelist[i,j] = [int(randint(0, (config.screen_width * .9 - puzzle_field_size))+puzzle_field_size), int(randint(0, (config.screen_height * .8)))]

                temp_img = im.Crop(mainimage, int(i*active_area_size*x_scale_index), int(j*active_area_size*y_scale_index), int(puzzle_piece_size*x_scale_index), int(puzzle_piece_size*y_scale_index))

                # makes puzzle piece image using its shape description and tile pieces
                # (will rotate them to form top, right, bottom and left sides of puzzle piece)
                xsize = round_int(puzzle_piece_size*x_scale_index)
                ysize = round_int(puzzle_piece_size*y_scale_index)
                fixed = Fixed(xysize=(xsize, ysize))

                d = Transform("content/gfx/interface/images/jp/_00%s.png"%(jigsaw_grid[grid_width*j+i][0]), rotate=0, rotate_pad=False, zoom=1.0)
                d = Transform(d, size=(xsize, ysize))
                fixed.add(AlphaMask(temp_img, d))
                d = Transform("content/gfx/interface/images/jp/_00%s.png"%(jigsaw_grid[grid_width*j+i][1]), rotate=270, rotate_pad=False, zoom=1.0)
                d = Transform(d, size=(xsize, ysize))
                fixed.add(AlphaMask(temp_img, d))
                d = Transform("content/gfx/interface/images/jp/_00%s.png"%(jigsaw_grid[grid_width*j+i][2]), rotate=180, rotate_pad=False, zoom=1.0)
                d = Transform(d, size=(xsize, ysize))
                fixed.add(AlphaMask(temp_img, d))
                d = Transform("content/gfx/interface/images/jp/_00%s.png"%(jigsaw_grid[grid_width*j+i][3]), rotate=90, rotate_pad=False, zoom=1.0)
                d = Transform(d, size=(xsize, ysize))
                fixed.add(AlphaMask(temp_img, d))
                imagelist[i, j] = fixed
                placedlist[i, j] = False

    jump puzzle

label puzzle:
    scene bg gallery
    call screen jigsaw
    with dissolve
    jump win

label win:
    scene bg gallery
    show expression img_to_play at Position(xalign=.5,yalign=.5)
    with dissolve

    "Congratulations!"
    menu:
        "Play again?"

        "Yes":
            jump jigsaw_puzzle_start

        "No":
            jump gallery


screen control_scr(preview):

    # if img_width>600 or img_height>600:
        # if img_width > img_height:
            # $ preview_scale = 600.00 / img_width
        # else:
            # $ preview_scale = 600.00 / img_height
    # else:
        # $ preview_scale = 1

    # $ preview = im.FactorScale(current_file, preview_scale)

    add preview xpos 450 ypos 100

    vbox:
        style_group "basic"
        pos (390, 100)
        spacing 20
        for i in range (2, 11):
            textbutton "[i]" action [SetVariable("grid_height", i), renpy.restart_interaction]

    hbox:
        style_group "basic"
        pos (450, 60)
        spacing 15
        for i in range (2, 11):
            textbutton "[i]" action [SetVariable("grid_width", i), renpy.restart_interaction]

    $ number_of_pieces = (grid_width*grid_height)
    frame:
        align (.01, .01)
        xpadding 20
        ypadding 20
        style_group "content"
        background Frame("content/gfx/frame/blue_wood.webp", 5, 5)
        label "[number_of_pieces] pieces!" text_size 35 text_color ivory align (.5, .5)

    button:
        xysize (100, 40)
        style_group "basic"
        text "Done" size 35
        # action If(current_file != 0, Return(current_file))
        action Return()
        align (.5, .98)

    imagebutton:
        align (1.0, .0)
        idle (im.Scale("content/gfx/interface/buttons/close.png", 60, 60))
        hover (im.MatrixColor(im.Scale("content/gfx/interface/buttons/close.png", 60, 60), im.matrix.brightness(.15)))
        action Jump("gallery")

screen jigsaw():

    key "rollback" action NullAction()
    key "rollforward" action NullAction()

    add im.Scale("content/gfx/frame/_puzzle_field.webp", img_width, img_height) pos (puzzle_field_offset, puzzle_field_offset)

    draggroup:
        for i in xrange(0, grid_width):
            for j in xrange(0, grid_height):
                $ name = "%s%s"%(i, j)
                $ my_x = i*int(active_area_size*x_scale_index)+puzzle_field_offset
                $ my_y = j*int(active_area_size*y_scale_index)+puzzle_field_offset
                drag:
                    drag_name name
                    child im.Scale("content/gfx/frame/_blank_space.webp", int(active_area_size*x_scale_index), int(active_area_size*y_scale_index) )
                    draggable False
                    xpos my_x ypos my_y

        for i in range(0, grid_width):
            for j in range(0, grid_height):
                $ name = "%s%s piece"%(i, j)
                drag:
                    drag_name name
                    child imagelist[i,j]
                    #droppable False
                    dragged piece_dragged
                    xpos piecelist[i, j][0] ypos piecelist[i, j][1]

    imagebutton:
        align(1.0, .0)
        idle (im.Scale("content/gfx/interface/buttons/close.png", 60, 60))
        hover (im.MatrixColor(im.Scale("content/gfx/interface/buttons/close.png", 60, 60), im.matrix.brightness(.15)))
        action Jump("gallery")
