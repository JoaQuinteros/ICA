from typing import Any, List

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
import os
from odoo.models import Claim
from django.conf import settings


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
    def __init__(self, *args, reason_type, id,**kwargs) -> None:
        super().__init__(*args, **kwargs)
        if reason_type == "request_change_of_address":
            self.fields.pop("files", '')
        elif reason_type == "change_plan":
            self.fields.pop("files", '')
        elif reason_type == "request_unsubscribe":
            self.fields.pop("files", '')


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
    
    email = forms.EmailField(required=True,
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
        required = False, 
        label = "Adjuntar archivo (deben ser .pdf, .jpeg, .png)", 
        widget = forms.ClearableFileInput(
            attrs = {
                'class': 'form-control','accept':'application/pdf, image/jpeg ,image/png',
            }
        ),
    )

    def clean(self) -> None:
        super().clean()
        name: str = self.cleaned_data.get("name")
        if name is None or name.isnumeric():
            raise ValidationError(
                {
                    "name": ValidationError(
                        "Los datos ingresados no deben contener numéros."
                    ),
                }
            )
        
        phone_number: str = self.cleaned_data.get("phone_number")
        print(phone_number.isnumeric())
        if phone_number.isnumeric() is False:
            raise ValidationError(
                {
                    "phone_number": ValidationError(
                        "Los datos ingresados deben ser numéricos."
                    ),
                }
            )
        
        email: str = self.cleaned_data.get("email")
        if email is not None and ('@' not in email or '.com' not in email):
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Los datos ingresados deben ser de un mail correcto."
                    ),
                }
            )


        files = self.cleaned_data.get("files")
        if files != None and files.size > int(settings.MAX_UPLOAD_SIZE):
            raise ValidationError(
                {
                    "files": ValidationError(
                        "El tamaño del archivo no puede superar los 5MB"
                    ),
                }
            )
        
                #allow_empty_file = True,

class AddInfoCalimForm(forms.Form):
    def __init__(self, *args, reason_type, id,**kwargs) -> None:
        super().__init__(*args, **kwargs)
        if reason_type == "request_change_of_address":
            self.fields.pop("files", '')
        elif reason_type == "change_plan":
            self.fields.pop("files", '')
        elif reason_type == "request_unsubscribe":
            self.fields.pop("files", '')
   
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
        required = False, 
        label = "Adjuntar archivo (deben ser .pdf, .jpeg, .png)", 
        widget = forms.ClearableFileInput(
            attrs = {
                'class': 'form-control','accept':'application/pdf, image/jpeg ,image/png',
            }
        ),
    )

    def clean(self) -> None:
        super().clean()
        
        files = self.cleaned_data.get("files")
        if files != None and files.size > int(settings.MAX_UPLOAD_SIZE):
            raise ValidationError(
                {
                    "files": ValidationError(
                        "El tamaño del archivo no puede superar los 5MB"
                    ),
                }
            )