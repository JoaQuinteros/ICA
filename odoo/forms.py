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


class BaseClaimForm(forms.Form):
    def __init__(self, *args, has_open_claim, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if has_open_claim:
            self.fields.pop("reason")
            self.fields.pop("name")
            self.fields.pop("phone_number")
            self.fields.pop("email")
            self.fields.pop("files")
    
    reason = forms.ChoiceField(
        widget = forms.HiddenInput(),
    )

    name = forms.CharField(
        max_length = 100,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
            }
        ),
        label = 'Nombre completo',
    )

    phone_number = forms.CharField(
        max_length = 10,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
            }
        ),
        label = 'Número de teléfono de contacto',
    )
    
    email = forms.EmailField(
        widget = forms.EmailInput(
            attrs = {
                'class': 'form-control',
            }
        ),
        label = 'Email de contacto',
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
    
    files = forms.FileField(
        label = "Puede adjuntar archivo", 
        widget = forms.ClearableFileInput(
            attrs = {
                'class': 'form-control',
            }
        ),
    )
    

class TechnicalClaimForm(BaseClaimForm):
    pass


class ClaimForm2(forms.ModelForm):
    class Meta:
        model = Claim
        fields: List[str] = ['reason', 'description']