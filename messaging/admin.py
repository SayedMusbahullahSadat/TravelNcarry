# messaging/admin.py
from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sent_at',)
    fields = ('sender', 'content', 'is_read', 'sent_at')


class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'created_at', 'updated_at')
    search_fields = ('participants__username', 'participants__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]

    def get_participants(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])

    get_participants.short_description = 'Participants'


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'is_read', 'sent_at')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('sender__username', 'content')
    readonly_fields = ('sent_at',)


admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)