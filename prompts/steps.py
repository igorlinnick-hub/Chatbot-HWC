from config import CALENDLY_LINK

CONVERSATION_STEPS = {
    1: {
        "send_first": True,
        "message": "Hey, thanks for the follow. Are you here for the content or exploring ways to better manage your anxiety?",
        "mirror_before_next": True,
        "emotional_weight": "low",
    },
    2: {
        "send_first": False,
        "message": "I'm wondering, where in your life do you find your anxiety showing up for you the most?",
        "mirror_before_next": True,
        "emotional_weight": "medium",
    },
    3: {
        "send_first": False,
        "message": "I'm curious, if you were somehow able to stop the anxiety what would that do for you?",
        "mirror_before_next": True,
        "emotional_weight": "medium",
    },
    4: {
        "send_first": False,
        "message": "And what do you think is preventing you from being able to feel better in general already besides the anxiety?",
        "mirror_before_next": True,
        "emotional_weight": "high",
    },
    5: {
        "send_first": False,
        "message": "I'm wondering, how important is it for you to make a change now",
        "mirror_before_next": True,
        "emotional_weight": "high",
    },
    6: {
        "send_first": False,
        "message": "Could I make a suggestion?",
        "mirror_before_next": True,
        "emotional_weight": "low",
        "wait_for_yes": True,
    },
    7: {
        "send_first": False,
        "message": "I know you've mentioned you've been trying to solve this for {duration}, so what we could do is let you set up a free session directly with me to better understand what you've been going through so far, where you want to be and how I could possibly help you overcome {pain_point}.",
        "follow_up": "Would that be helpful for you?",
        "split_messages": True,
        "mirror_before_next": False,
        "emotional_weight": "high",
        "wait_for_yes": True,
    },
    8: {
        "send_first": False,
        "messages": [
            "Alright, happy to help.",
            "Do you have 2 mins to pick a time that's convenient for you to chat, if I send you my calendar? To make it easier for you.",
        ],
        "split_messages": True,
        "mirror_before_next": False,
        "emotional_weight": "low",
        "wait_for_yes": True,
    },
    9: {
        "send_first": False,
        "messages": [
            "Great, here's my calendar:",
            CALENDLY_LINK,
        ],
        "follow_up": "And let me know once you're done so that I can check everything went through properly for you… sometimes calendars act weird",
        "split_messages": True,
        "mirror_before_next": False,
        "emotional_weight": "low",
        "is_final": True,
    },
}
