from django import forms
from .models import Ticket, TicketComment, Category, SLA


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['description'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 5})


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'status', 'assigned_to']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['assigned_to'].queryset = User.objects.filter(role__in=['agent', 'admin'])
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['description'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 5})


class MultipleFileInput(forms.FileInput):
    """Widget that allows selecting multiple files — works on Django 4.x and 6.x."""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data if d]
        return [single_file_clean(data, initial)] if data else []


class TicketCommentForm(forms.ModelForm):
    attachments = MultipleFileField(required=False)

    class Meta:
        model = TicketComment
        fields = ['content', 'is_internal']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['content'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your comment here...'})
        # Only show internal option to agents/admins
        if self.user and self.user.role == 'user':
            self.fields.pop('is_internal')


class TicketRatingForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['rating', 'rating_comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget = forms.Select(
            choices=Ticket.RATING_CHOICES,
            attrs={'class': 'form-select'}
        )
        self.fields['rating_comment'].widget = forms.Textarea(
            attrs={'class': 'form-control', 'rows': 3}
        )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SLAForm(forms.ModelForm):
    class Meta:
        model = SLA
        fields = ['priority', 'response_time_hours', 'resolution_time_hours', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TicketSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search tickets...'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Ticket.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'All Priorities')] + Ticket.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
