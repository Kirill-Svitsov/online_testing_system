from django import forms
import json


class AnswerForm(forms.Form):
    question_id = forms.IntegerField(widget=forms.HiddenInput())
    question_text = forms.CharField(widget=forms.HiddenInput())
    question_type = forms.CharField(widget=forms.HiddenInput())
    choices = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        question_type = self.initial.get('question_type', '')
        choices = json.loads(self.initial.get('choices', '[]'))

        if question_type == 'single':
            self.fields['answer'] = forms.ChoiceField(
                choices=[(choice, choice) for choice in choices],
                widget=forms.RadioSelect(),
                required=True
            )
        elif question_type == 'multiple':
            # Для множественного выбора используем MultipleChoiceField
            self.fields['answer'] = forms.MultipleChoiceField(
                choices=[(choice, choice) for choice in choices],
                widget=forms.CheckboxSelectMultiple(),
                required=False
            )
        else: # TODO для ответов текстом
            self.fields['answer'] = forms.CharField(
                widget=forms.Textarea(attrs={'rows': 3}),
                required=True
            )