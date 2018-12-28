# Events File

init -9 python:
    register_event("maria_tulip_1_event", locations=["arena_outside"], priority=1, dice=40, max_runs=1)

#just a small introduction
label maria_tulip_1_event(event):
    scene bg arena_outside
    $ m = store.female_fighters["Maria Custard"].say
    $ s = store.female_fighters["Masou Shizuka"].say

    "You walked around the arena quarters when you saw a girl with an unusual weapon."
    "She was going in your direction, so you decided to approach her and satisfy your curiosity."
    show expression store.female_fighters["Maria Custard"].get_vnsprite() as npc
    with dissolve
    m "Hi!"

    $ asked_fight_M = False
    $ menuM_skip = False
    while not menuM_skip:
        menu:
            "Ask her about...?"
            "Are you one of the fighters?" if not asked_fight_M:
                $ asked_fight_M = True
                m "Yup. I do participate with my friend Shizuka, but we usually stay out of the official ladders. {p}We are here not for the popularity."

            "So... what's the deal with that weapon of yours?":
                m "That's Tulip Cannon, my own invention. <looks proudly>"
                m "It's fueled by a compound made primarily from Hirara Alloy, which helps the projectile to acquire a better muzzle velocity."
                m "The PytFall representatives allowed me to test the new non-lethal ammunition in the city arena. \nIt seems to be working most of the time. It's so exciting!"
                $ menuM_skip = True
            "<don't bother her anymore>":
                hide npc
                with dissolve
                "Nothing else caught your attention, so you left."
                return

    m "And there's also..."
    s "Maria! It's time to go!"
    m "Coming! {w}Sorry..."

    hide npc
    with moveoutright

    "... {p}(most of the time, huh?)"
    "There was nothing else to do, so you left too."

    $ del menuM_skip
    $ del asked_fight_M
    return
