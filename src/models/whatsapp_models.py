"""
WhatsApp Business API Models

Pydantic models for WhatsApp Cloud API message structures.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Incoming Message Models (Webhook)
# ============================================================================

class Profile(BaseModel):
    """User profile information"""
    name: str


class Contact(BaseModel):
    """Contact information from incoming message"""
    profile: Profile
    wa_id: str = Field(..., description="WhatsApp ID (phone number)")


class TextMessage(BaseModel):
    """Text message content"""
    body: str


class ImageMessage(BaseModel):
    """Image message content"""
    id: str = Field(..., description="Media ID")
    mime_type: str
    sha256: str
    caption: Optional[str] = None


class AudioMessage(BaseModel):
    """Audio message content"""
    id: str = Field(..., description="Media ID")
    mime_type: str
    sha256: str
    voice: bool = Field(default=False, description="True if voice message")


class VideoMessage(BaseModel):
    """Video message content"""
    id: str = Field(..., description="Media ID")
    mime_type: str
    sha256: str
    caption: Optional[str] = None


class DocumentMessage(BaseModel):
    """Document message content"""
    id: str = Field(..., description="Media ID")
    mime_type: str
    sha256: str
    filename: Optional[str] = None
    caption: Optional[str] = None


class LocationMessage(BaseModel):
    """Location message content"""
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


class ReactionMessage(BaseModel):
    """Reaction to a message"""
    message_id: str
    emoji: str


class Context(BaseModel):
    """Message context (for replies)"""
    from_: str = Field(..., alias="from")
    id: str = Field(..., description="Message ID being replied to")


class Message(BaseModel):
    """Incoming WhatsApp message"""
    from_: str = Field(..., alias="from", description="Sender's WhatsApp ID")
    id: str = Field(..., description="Message ID")
    timestamp: str
    type: Literal["text", "image", "audio", "video", "document", "location", "reaction", "button", "interactive"]

    # Message content (only one will be populated based on type)
    text: Optional[TextMessage] = None
    image: Optional[ImageMessage] = None
    audio: Optional[AudioMessage] = None
    video: Optional[VideoMessage] = None
    document: Optional[DocumentMessage] = None
    location: Optional[LocationMessage] = None
    reaction: Optional[ReactionMessage] = None

    # Context for replies
    context: Optional[Context] = None

    @property
    def message_text(self) -> Optional[str]:
        """Get text content from any message type"""
        if self.text:
            return self.text.body
        elif self.image and self.image.caption:
            return self.image.caption
        elif self.video and self.video.caption:
            return self.video.caption
        elif self.document and self.document.caption:
            return self.document.caption
        return None

    @property
    def media_id(self) -> Optional[str]:
        """Get media ID if message contains media"""
        if self.image:
            return self.image.id
        elif self.audio:
            return self.audio.id
        elif self.video:
            return self.video.id
        elif self.document:
            return self.document.id
        return None


class Status(BaseModel):
    """Message status update"""
    id: str = Field(..., description="Message ID")
    status: Literal["sent", "delivered", "read", "failed"]
    timestamp: str
    recipient_id: str
    conversation: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None


class Value(BaseModel):
    """Webhook value object"""
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: Optional[List[Contact]] = None
    messages: Optional[List[Message]] = None
    statuses: Optional[List[Status]] = None


class Change(BaseModel):
    """Webhook change object"""
    value: Value
    field: str


class Entry(BaseModel):
    """Webhook entry object"""
    id: str
    changes: List[Change]


class WebhookPayload(BaseModel):
    """Complete webhook payload"""
    object: str
    entry: List[Entry]

    def get_messages(self) -> List[Message]:
        """Extract all messages from webhook payload"""
        messages = []
        for entry in self.entry:
            for change in entry.changes:
                if change.value.messages:
                    messages.extend(change.value.messages)
        return messages

    def get_statuses(self) -> List[Status]:
        """Extract all status updates from webhook payload"""
        statuses = []
        for entry in self.entry:
            for change in entry.changes:
                if change.value.statuses:
                    statuses.extend(change.value.statuses)
        return statuses


# ============================================================================
# Outgoing Message Models (API Requests)
# ============================================================================

class OutgoingTextMessage(BaseModel):
    """Outgoing text message"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "text"
    text: Dict[str, str]

    @classmethod
    def create(cls, to: str, body: str, preview_url: bool = False) -> "OutgoingTextMessage":
        """
        Create outgoing text message.

        Args:
            to: Recipient's WhatsApp ID (phone number)
            body: Message text
            preview_url: Enable URL previews

        Returns:
            OutgoingTextMessage instance
        """
        return cls(
            to=to,
            text={"body": body, "preview_url": preview_url}
        )


class MediaObject(BaseModel):
    """Media object for outgoing messages"""
    id: Optional[str] = None
    link: Optional[str] = None
    caption: Optional[str] = None


class OutgoingImageMessage(BaseModel):
    """Outgoing image message"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "image"
    image: MediaObject

    @classmethod
    def create(cls, to: str, media_id: Optional[str] = None, link: Optional[str] = None,
               caption: Optional[str] = None) -> "OutgoingImageMessage":
        """Create outgoing image message"""
        return cls(
            to=to,
            image=MediaObject(id=media_id, link=link, caption=caption)
        )


class OutgoingAudioMessage(BaseModel):
    """Outgoing audio message"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "audio"
    audio: MediaObject

    @classmethod
    def create(cls, to: str, media_id: Optional[str] = None,
               link: Optional[str] = None) -> "OutgoingAudioMessage":
        """Create outgoing audio message"""
        return cls(
            to=to,
            audio=MediaObject(id=media_id, link=link)
        )


class OutgoingDocumentMessage(BaseModel):
    """Outgoing document message"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "document"
    document: MediaObject

    @classmethod
    def create(cls, to: str, media_id: Optional[str] = None, link: Optional[str] = None,
               caption: Optional[str] = None, filename: Optional[str] = None) -> "OutgoingDocumentMessage":
        """Create outgoing document message"""
        doc = MediaObject(id=media_id, link=link, caption=caption)
        if filename:
            doc.filename = filename
        return cls(to=to, document=doc)


class Button(BaseModel):
    """Interactive button"""
    type: str = "reply"
    reply: Dict[str, str]

    @classmethod
    def create(cls, id: str, title: str) -> "Button":
        """Create button"""
        return cls(reply={"id": id, "title": title})


class InteractiveAction(BaseModel):
    """Interactive message action"""
    buttons: List[Button]


class InteractiveBody(BaseModel):
    """Interactive message body"""
    text: str


class Interactive(BaseModel):
    """Interactive message content"""
    type: str = "button"
    body: InteractiveBody
    action: InteractiveAction


class OutgoingInteractiveMessage(BaseModel):
    """Outgoing interactive message with buttons"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "interactive"
    interactive: Interactive

    @classmethod
    def create(cls, to: str, body: str, buttons: List[Dict[str, str]]) -> "OutgoingInteractiveMessage":
        """
        Create interactive message with buttons.

        Args:
            to: Recipient's WhatsApp ID
            body: Message body text
            buttons: List of buttons [{"id": "btn1", "title": "Button 1"}, ...]

        Returns:
            OutgoingInteractiveMessage instance
        """
        button_objects = [Button.create(btn["id"], btn["title"]) for btn in buttons]
        return cls(
            to=to,
            interactive=Interactive(
                body=InteractiveBody(text=body),
                action=InteractiveAction(buttons=button_objects)
            )
        )


class TemplateComponent(BaseModel):
    """Template component"""
    type: str
    parameters: List[Dict[str, Any]]


class TemplateLanguage(BaseModel):
    """Template language"""
    code: str = "en_US"


class Template(BaseModel):
    """Message template"""
    name: str
    language: TemplateLanguage
    components: Optional[List[TemplateComponent]] = None


class OutgoingTemplateMessage(BaseModel):
    """Outgoing template message"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: Template

    @classmethod
    def create(cls, to: str, template_name: str, language_code: str = "en_US",
               components: Optional[List[TemplateComponent]] = None) -> "OutgoingTemplateMessage":
        """Create template message"""
        return cls(
            to=to,
            template=Template(
                name=template_name,
                language=TemplateLanguage(code=language_code),
                components=components
            )
        )


class ReactionPayload(BaseModel):
    """Reaction to a message"""
    message_id: str
    emoji: str


class OutgoingReaction(BaseModel):
    """Outgoing reaction"""
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "reaction"
    reaction: ReactionPayload

    @classmethod
    def create(cls, to: str, message_id: str, emoji: str) -> "OutgoingReaction":
        """Create reaction"""
        return cls(
            to=to,
            reaction=ReactionPayload(message_id=message_id, emoji=emoji)
        )


# ============================================================================
# API Response Models
# ============================================================================

class MessageResponse(BaseModel):
    """Response from sending a message"""
    messaging_product: str
    contacts: List[Dict[str, str]]
    messages: List[Dict[str, str]]

    @property
    def message_id(self) -> Optional[str]:
        """Get the sent message ID"""
        if self.messages:
            return self.messages[0].get("id")
        return None


class ErrorDetail(BaseModel):
    """API error detail"""
    message: str
    type: str
    code: int
    error_subcode: Optional[int] = None
    fbtrace_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """API error response"""
    error: ErrorDetail


class MediaUrlResponse(BaseModel):
    """Media URL response"""
    url: str
    mime_type: str
    sha256: str
    file_size: int
    id: str
    messaging_product: str


class MarkAsReadRequest(BaseModel):
    """Request to mark message as read"""
    messaging_product: str = "whatsapp"
    status: str = "read"
    message_id: str
