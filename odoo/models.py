from django.db import models


class Client(models.Model):
    name = models.CharField(
        verbose_name="Nombre y apellido",
        max_length=100,
    )
    dni = models.CharField(
        verbose_name="DNI",
        max_length=8,
    )
    address = models.CharField(
        verbose_name="Dirección",
        max_length=100,
    )
    cellphone = models.CharField(
        verbose_name="Teléfono",
        max_length=10,
    )
    credit = models.FloatField(
        verbose_name="Deuda",
    )


class Service(models.Model):

    class ServiceTypeChoices(models.IntegerChoices):
        MEGAS3 = 1, '3 Megas'
        MEGAS5 = 2, '5 Megas'
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name="Cliente",
    )
    is_active = models.BooleanField(
        verbose_name="Activo",
        default=True,
    )
    service_type = models.IntegerField(
        verbose_name="Tipo de Servicio",
        choices=ServiceTypeChoices.choices,
    )
    lat = models.CharField(
        verbose_name="Latitud",
        max_length=10,
        blank=True,
        null=True,
    )
    lng = models.CharField(
        verbose_name="Longitud",
        max_length=10,
        blank=True,
        null=True,
    )
    has_active_claim = models.BooleanField(
        verbose_name="Tiene reclamo activo"
    )
    

class Claim(models.Model):

    class ReasonChoices(models.TextChoices):
        ADMINISTRATIVO = 'administrativo', 'Administrativo'
        TECNICO = 'tecnico', 'Técnico'
    
    class StatusChoices(models.TextChoices):
        INGRESADO = 'ingresado', 'Ingresado'
        ASIGNADO = 'asignado', 'Asignado'
        EN_PROCESO = 'en_proceso', 'En Proceso'
        TERMINADO = 'terminado', 'Terminado'

    reason = models.CharField(
        verbose_name="Motivo",
        max_length=20,
        choices=ReasonChoices.choices,
    )
    description = models.TextField(
        verbose_name="Descripción",
        max_length=200,
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="claims",
        verbose_name="Servicio"
    )
    status = models.CharField(
        verbose_name="Estado",
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.INGRESADO,
    )    

