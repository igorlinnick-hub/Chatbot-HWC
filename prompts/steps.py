from config import BOOKING_LINK

CONVERSATION_STEPS = {
    1: {
        "send_first": True,
        "message": "Aloha, thanks for the follow. Are you here for the content or exploring how we could support your wellness journey?",
        "mirror_before_next": True,
        "emotional_weight": "low",
    },
    2: {
        "send_first": False,
        "message": "I'm wondering, what area of your wellness are you most wanting to work on right now?",
        "mirror_before_next": True,
        "emotional_weight": "medium",
    },
    3: {
        "send_first": False,
        "message": "I'm curious, if you were able to really shift this, what would that change open up for you?",
        "mirror_before_next": True,
        "emotional_weight": "medium",
    },
    4: {
        "send_first": False,
        "message": "And what do you think has been getting in the way of feeling your best already?",
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
        "message": "I know you've been navigating this for {duration}, so what we could do is set you up with a free discovery call with one of our coaches to really understand where you've been, where you want to be, and how the clinic could help you with {pain_point}.",
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
            "Do you have 2 mins to pick a time that's convenient for you, if I send over the calendar? Want to make it easy.",
        ],
        "split_messages": True,
        "mirror_before_next": False,
        "emotional_weight": "low",
        "wait_for_yes": True,
    },
    9: {
        "send_first": False,
        "messages": [
            "Great, here's the calendar:",
            BOOKING_LINK,
        ],
        "follow_up": "And let me know once you're done so I can check it went through properly... calendars sometimes act weird.",
        "split_messages": True,
        "mirror_before_next": False,
        "emotional_weight": "low",
        "is_final": True,
    },
}
