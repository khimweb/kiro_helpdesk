from django import template

register = template.Library()


@register.simple_tag
def get_other_user(conversation, user):
    """Get the other participant in a private conversation."""
    return conversation.get_other_participant(user)
