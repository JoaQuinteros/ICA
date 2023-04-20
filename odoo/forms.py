from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError


def add_class_to_label(original_function):
    def class_to_label_tag(self, *args, **kwargs):
        return original_function(self, attrs={"class": "fw-bold"}, label_suffix="")

    return class_to_label_tag


forms.BoundField.label_tag = add_class_to_label(forms.BoundField.label_tag)


class LoginForm(forms.Form):
    # client_id = forms.CharField(label="ID", max_length=10)
    dni = forms.CharField(
        label="DNI / CUIT",
        min_length=7,
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Número de documento o CUIT",
            }
        ),
    )

    def clean(self) -> None:
        super().clean()
        dni: str = self.cleaned_data.get("dni")
        if dni:
            if not dni.isnumeric():
                raise ValidationError(
                    {
                        "dni": ValidationError(
                            "Los datos ingresados deben ser numéricos."
                        ),
                    }
                )
            elif len(dni) not in [7, 8, 11]:
                raise ValidationError(
                    {
                        "dni": ValidationError("Solo se admiten 7, 8 u 11 dígitos."),
                    }
                )


class LoginRecoveryForm(forms.Form):
    dni_recovery = forms.CharField(
        label="DNI / CUIT",
        min_length=7,
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Número de documento o CUIT",
            }
        ),
    )
    client_id = forms.CharField(
        label="Número de cliente",
        max_length=50,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Número de cliente"}
        ),
    )

    def clean(self) -> None:
        super().clean()
        dni: str = self.cleaned_data.get("dni")
        if dni:
            if not dni.isnumeric():
                raise ValidationError(
                    {
                        "dni": ValidationError(
                            "Los datos ingresados deben ser numéricos."
                        ),
                    }
                )
            elif len(dni) not in [7, 8, 11]:
                raise ValidationError(
                    {
                        "dni": ValidationError("Solo se admiten 7, 8 u 11 dígitos."),
                    }
                )


class BaseClaimForm(forms.Form):
    def __init__(self, *args, claim_type, has_open_ticket=False, **kwargs):
        super().__init__(*args, **kwargs)
        if claim_type in ["36", "45", "56"]:
            del self.fields["files"]
        if has_open_ticket:
            del self.fields["name"]
            del self.fields["phone_number"]
            del self.fields["email"]

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control rounded-end",
            }
        ),
        label="Nombre completo",
    )

    phone_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "form-control rounded-end",
            }
        ),
        label="Número de teléfono de contacto",
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control rounded-end",
            }
        ),
        label="Email de contacto",
    )

    description = forms.CharField(
        max_length=100,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Incluya información que pueda ayudarnos a identificar y resolver su reclamo...",
                "rows": "auto",
            }
        ),
        label="Descripción",
        required=False,
    )

    files = forms.FileField(
        required=False,
        label="Adjuntar archivo (.pdf, .jpeg o .png)",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control rounded-end",
                "accept": "application/pdf, image/jpeg ,image/png",
                "data-bs-toggle": "tooltip",
                "data-bs-placement": "top",
                "data-bs-title": "Adjuntar archivo (.pdf, .jpeg o .png)",
            }
        ),
    )

    def clean(self):
        super().clean()
        name = self.cleaned_data.get("name")
        if not name or name.isnumeric():
            raise ValidationError(
                {
                    "name": ValidationError(
                        "Los datos ingresados no deben contener números."
                    ),
                }
            )

        phone_number = self.cleaned_data.get("phone_number")
        if not phone_number.isnumeric():
            raise ValidationError(
                {
                    "phone_number": ValidationError(
                        "Los datos ingresados deben ser numéricos."
                    ),
                }
            )

        # email = self.cleaned_data.get("email")
        # if not email or ["@", ".com"] not in email:
        #     raise ValidationError(
        #         {
        #             "email": ValidationError(
        #                 "Los datos ingresados deben ser de un mail correcto."
        #             ),
        #         }
        #     )

        files = self.cleaned_data.get("files")
        if files and files.size > int(settings.MAX_UPLOAD_SIZE):
            raise ValidationError(
                {
                    "files": ValidationError(
                        "El tamaño del archivo no puede superar los 5MB."
                    ),
                }
            )


class AddClaimInfoForm(forms.Form):
    def __init__(self, *args, reason_type, id, **kwargs):
        super().__init__(*args, **kwargs)
        if reason_type in [
            "request_change_of_address",
            "change_plan",
            "request_unsubscribe",
        ]:
            del self.fields["files"]

    description = forms.CharField(
        max_length=100,
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Descripción del reclamo..."}
        ),
        label="Descripción",
    )

    files = forms.FileField(
        required=False,
        label="Adjuntar archivo (deben ser .pdf, .jpeg, .png)",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": "application/pdf, image/jpeg ,image/png",
            }
        ),
    )

    def clean(self):
        super().clean()

        files = self.cleaned_data.get("files")
        if files and files.size > int(settings.MAX_UPLOAD_SIZE):
            raise ValidationError(
                {
                    "files": ValidationError(
                        "El tamaño del archivo no puede superar los 5MB."
                    ),
                }
            )
