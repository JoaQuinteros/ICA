from typing import Any, List

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from odoo.models import Claim


def add_class_to_label(original_function) -> Any:
    def class_to_label_tag(self, *args, **kwargs) -> Any:
        required_field = format_html('<span class="text-info fw-bold"> *</span>')
        label_suffix = required_field if self.field.required else ""
        return original_function(
            self, attrs={"class": "fw-bold m-2"}, label_suffix=label_suffix
        )

    return class_to_label_tag


forms.BoundField.label_tag = add_class_to_label(forms.BoundField.label_tag)

class LoginForm(forms.Form):
    # client_id = forms.CharField(label="ID", max_length=10)
    dni = forms.CharField(
        label = "DNI / CUIT", 
        max_length = 11,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Número de documento o CUIT',
            }
        )
    )

    def clean(self) -> None:
        super().clean()
        dni: str = self.cleaned_data.get("dni")
        # client_id: str = self.cleaned_data.get("client_id")
        # if not client_id.isnumeric():
        #     raise ValidationError(
        #         {
        #             "client_id": ValidationError(
        #                 "Los datos ingresados deben ser numéricos."
        #             ),
        #         },
        #     )
        if dni and not dni.isnumeric():
            raise ValidationError(
                {
                    "dni": ValidationError(
                        "Los datos ingresados deben ser numéricos."
                    ),
                }
            )


class ClaimForm(forms.Form):
    
    REASON_CHOICES = [
        ('ADMIN', 'Administrativo'),
        ('TECHNIC', 'Técnico'),
    ]


    reason = forms.ChoiceField(
        choices = REASON_CHOICES,
        widget = forms.Select(
            attrs = {
                'class': 'form-select',
            }
        ),
        label = "Motivo",
    )

    description = forms.CharField(
        max_length = 100,
        widget = forms.Textarea(
            attrs = {
                'class': 'form-control',
                'placeholder': 'Descripción del reclamo...'
            }
        ),
        label = 'Descripción',
    )


class ClaimForm2(forms.ModelForm):
    class Meta:
        model = Claim
        fields: List[str] = ['reason', 'description']