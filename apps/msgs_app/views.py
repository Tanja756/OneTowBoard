from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils import timezone
import logging

from .models import Message
from .forms import MessageForm
from listings.models import Listing
from apps.utils import get_device_template

logger = logging.getLogger(__name__)


@login_required
def send_message_view(request, listing_id):
    """Отправка сообщения автору объявления."""
    listing = get_object_or_404(Listing, pk=listing_id, status='active')

    if listing.author == request.user:
        messages.error(request, 'Вы не можете отправить сообщение самому себе.')
        return redirect('listings:detail', pk=listing_id)

    if not request.user.profile.email_verified:
        messages.error(request, 'Для отправки сообщений необходимо подтвердить email.')
        return redirect('users:profile')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.listing = listing
            msg.sender = request.user
            msg.recipient = listing.author
            msg.save()
            _send_email_notification(msg)
            messages.success(request, 'Сообщение отправлено.')
            return redirect('msgs_app:conversation', listing_id=listing_id, user_id=listing.author_id)
    else:
        form = MessageForm()

    template = get_device_template(request, 'msgs_app/send.html')
    return render(request, template, {'form': form, 'listing': listing})


@login_required
def reply_message_view(request, message_id):
    """Ответ на существующее сообщение."""
    original = get_object_or_404(Message, pk=message_id)

    if request.user not in (original.sender, original.recipient):
        messages.error(request, 'У вас нет доступа к этому сообщению.')
        return redirect('msgs_app:inbox')

    recipient = original.recipient if request.user == original.sender else original.sender

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.listing = original.listing
            msg.sender = request.user
            msg.recipient = recipient
            msg.parent = original if original.parent is None else original.parent
            msg.save()
            _send_email_notification(msg)
            messages.success(request, 'Ответ отправлен.')
            return redirect('msgs_app:conversation', listing_id=original.listing_id, user_id=recipient.id)
    else:
        form = MessageForm()

    template = get_device_template(request, 'msgs_app/reply.html')
    return render(request, template, {'form': form, 'original': original, 'listing': original.listing})


@login_required
def inbox_view(request):
    """Список переписок пользователя."""
    messages_qs = Message.objects.filter(
        Q(sender=request.user, is_sender_deleted=False) |
        Q(recipient=request.user, is_recipient_deleted=False)
    ).select_related('sender', 'recipient', 'listing').order_by('-created_at')

    conversations = {}
    for msg in messages_qs:
        other_user = msg.recipient if msg.sender == request.user else msg.sender
        key = (msg.listing_id, other_user.id)

        if key not in conversations:
            conversations[key] = {
                'listing': msg.listing,
                'other_user': other_user,
                'last_message': msg,
                'unread_count': 0,
            }
        else:
            if msg.created_at > conversations[key]['last_message'].created_at:
                conversations[key]['last_message'] = msg

        if msg.recipient == request.user and not msg.is_read:
            conversations[key]['unread_count'] += 1

    sorted_convos = sorted(
        conversations.values(),
        key=lambda c: c['last_message'].created_at,
        reverse=True
    )

    total_unread = sum(c['unread_count'] for c in sorted_convos)

    template = get_device_template(request, 'msgs_app/inbox.html')
    return render(request, template, {
        'conversations': sorted_convos,
        'total_unread': total_unread,
    })


@login_required
def conversation_view(request, listing_id, user_id):
    """Просмотр переписки с конкретным пользователем по объявлению.

    СТРОГАЯ ПРОВЕРКА ДОСТУПА:
    Пользователь может просматривать переписку, только если он является
    отправителем или получателем хотя бы одного НЕУДАЛЁННОГО сообщения
    в этой переписке. Третьи лица (даже зная URL) не имеют доступа.
    """
    listing = get_object_or_404(Listing, pk=listing_id)
    other_user = get_object_or_404(User, pk=user_id)

    is_participant = Message.objects.filter(
        listing=listing,
        sender__in=[request.user, other_user],
        recipient__in=[request.user, other_user],
    ).filter(
        Q(sender=request.user, is_sender_deleted=False) |
        Q(recipient=request.user, is_recipient_deleted=False)
    ).exists()

    if not is_participant:
        messages.error(request, 'У вас нет доступа к этой переписке.')
        return redirect('msgs_app:inbox')

    messages_qs = Message.objects.filter(
        listing=listing,
        sender__in=[request.user, other_user],
        recipient__in=[request.user, other_user],
    ).filter(
        Q(sender=request.user, is_sender_deleted=False) |
        Q(recipient=request.user, is_recipient_deleted=False) |
        Q(sender=other_user, is_sender_deleted=False) |
        Q(recipient=other_user, is_recipient_deleted=False)
    ).select_related('sender').order_by('created_at')

    unread = messages_qs.filter(recipient=request.user, is_read=False)
    now = timezone.now()
    unread.update(is_read=True, read_at=now)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.listing = listing
            msg.sender = request.user
            msg.recipient = other_user
            msg.save()
            _send_email_notification(msg)
            return redirect('msgs_app:conversation', listing_id=listing_id, user_id=user_id)
    else:
        form = MessageForm()

    template = get_device_template(request, 'msgs_app/conversation.html')
    return render(request, template, {
        'messages': messages_qs,
        'listing': listing,
        'other_user': other_user,
        'form': form,
    })


@login_required
def delete_conversation_view(request, listing_id, user_id):
    """Удаление переписки (soft delete для пользователя).

    СТРОГАЯ ПРОВЕРКА ДОСТУПА:
    Только участник переписки может её удалить.
    """
    if request.method != 'POST':
        return redirect('msgs_app:inbox')

    listing = get_object_or_404(Listing, pk=listing_id)
    other_user = get_object_or_404(User, pk=user_id)

    is_participant = Message.objects.filter(
        listing=listing,
        sender__in=[request.user, other_user],
        recipient__in=[request.user, other_user],
    ).filter(
        Q(sender=request.user, is_sender_deleted=False) |
        Q(recipient=request.user, is_recipient_deleted=False)
    ).exists()

    if not is_participant:
        messages.error(request, 'У вас нет доступа к этой переписке.')
        return redirect('msgs_app:inbox')

    Message.objects.filter(
        listing=listing,
        sender=request.user,
        recipient=other_user,
    ).update(is_sender_deleted=True)

    Message.objects.filter(
        listing=listing,
        sender=other_user,
        recipient=request.user,
    ).update(is_recipient_deleted=True)

    messages.success(request, 'Переписка удалена.')
    return redirect('msgs_app:inbox')


def _send_email_notification(message):
    """Отправка email-уведомления о новом сообщении."""
    try:
        recipient = message.recipient
        recipient_email = recipient.email
        if not recipient_email:
            return

        subject = f'Новое сообщение от {message.sender.username} — {message.listing.title[:50]}'
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        conversation_url = f'{site_url}/messages/conversation/{message.listing.id}/{message.sender.id}/'

        text_message = (
            f'Здравствуйте, {recipient.username}!\n\n'
            f'Вам пришло новое сообщение от пользователя {message.sender.username} '
            f'по объявлению "{message.listing.title}".\n\n'
            f'Текст сообщения:\n{message.text}\n\n'
            f'Ответить: {conversation_url}\n\n'
            f'---\n{settings.SITE_NAME}'
        )

        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=True,
        )
    except Exception as e:
        logger.exception(f'Ошибка отправки email уведомления: {e}')