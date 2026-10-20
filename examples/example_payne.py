from objectionengine2.renderer import render_comment_list
from objectionengine2.beans.comment import Comment

comments = [
    Comment(
        user_name="Payne",
        text_content="The prosecution is ready, Your Honor.",
    ),
    Comment(
        user_name="Phoenix",
        text_content="The, um, defense is ready, Your Honor.",
    ),
]
render_comment_list(comments, assigned_characters={"Payne": "payne", "Phoenix": "phoenix"})
