# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q, Max, F, Value, CharField
from django.db.models.functions import Concat
from django.utils import timezone

from .models import Conversation, Message
from .forms import MessageForm
from users.models import CustomUser


@login_required
def inbox(request):
    """
    Display the user's message inbox.
    """
    # Get all conversations the user is part of
    conversations = Conversation.objects.filter(participants=request.user)

    # Add additional data to each conversation
    for conversation in conversations:
        # Get the other participant
        conversation.other_user = conversation.get_other_participant(request.user)

        # Get the last message
        last_message = conversation.last_message()
        conversation.last_message_content = last_message.content if last_message else ""
        conversation.last_message_time = last_message.sent_at if last_message else conversation.created_at

        # Check for unread messages
        conversation.unread_count = Message.objects.filter(
            conversation=conversation,
            sender=conversation.other_user,
            is_read=False
        ).count()

    return render(request, 'messaging/inbox.html', {
        'conversations': conversations,
    })


@login_required
def conversation_detail(request, conversation_id):
    """
    Display a conversation and allow sending messages.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Security check - only participants can view the conversation
    if request.user not in conversation.participants.all():
        django_messages.error(request, "You are not authorized to view this conversation.")
        return redirect('inbox')

    other_user = conversation.get_other_participant(request.user)

    # Mark unread messages as read
    Message.objects.filter(
        conversation=conversation,
        sender=other_user,
        is_read=False
    ).update(is_read=True)

    # Handle new message form
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            # Update conversation timestamp
            conversation.save()  # This will update the updated_at field

            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    conversation_messages = Message.objects.filter(conversation=conversation)

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'other_user': other_user,
        'conversation_messages': conversation_messages,  # Changed from 'messages' to 'conversation_messages'
        'form': form,
    })


@login_required
def start_conversation(request, user_id):
    """
    Start a new conversation with a user.
    """
    other_user = get_object_or_404(CustomUser, id=user_id)

    # Don't allow starting a conversation with yourself
    if other_user == request.user:
        django_messages.error(request, "You cannot start a conversation with yourself.")
        return redirect('inbox')

    # Check if a conversation already exists
    existing_conversation = Conversation.objects.filter(participants=request.user).filter(
        participants=other_user).first()

    if existing_conversation:
        return redirect('conversation_detail', conversation_id=existing_conversation.id)

    # Create a new conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, other_user)

    return redirect('conversation_detail', conversation_id=conversation.id)