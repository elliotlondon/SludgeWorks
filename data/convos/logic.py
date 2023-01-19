import core.g
import data.convos.gilbert as gilbert


def get_convo(entity_tag: str) -> [None, dict]:
    """Function which returns the conversation for the given init entity tag, by loading from the corresponding
    {tag}.py file in the parent directory. Returns none if the file does not exist, so no convo."""

    # Firstly, handle whether there is a failed quest that stops any interactions.
    quest = None
    for q in core.g.engine.quests.active_quests:
        if entity_tag in q.name and not q.failed:
            quest = q
            break
        elif entity_tag in q.name and q.failed:
            return None

    # Handle loading logic for each quest here.
    # Faster and easier to do it the dumb way rather than some importlib shenanigans.
    if entity_tag == 'gilbert':
        # First encounter on floor 1
        if core.g.engine.game_world.current_floor == 1:
            if not quest:
                return gilbert.gilbert_1_init
            else:
                return gilbert.gilbert_1_met
        # 2nd encounter on floor 2
        elif core.g.engine.game_world.current_floor == 3:
            if not quest:
                return gilbert.gilbert_3_default
            elif quest.step == 0:
                for item in core.g.engine.player.inventory.items:
                    if item.tag == 'moire_beast_hide':
                        return gilbert.gilbert_3_started_hide
                return gilbert.gilbert_3_started_nohide
            elif quest.step == 1:
                return gilbert.gilbert_3_init
            elif quest.step == 2:
                return gilbert.gilbert_3_started
    else:
        # All other entities do not talk with the player and give generic no reply messages.
        return None
