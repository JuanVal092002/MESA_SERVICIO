from django.db import models
from django.contrib.auth.models import AbstractUser

tipoOficiona = [('Administrativo', "Administrativo"),
                ('Formacion', "Formacion")]
tipoUsuario = [('Administrador', "Administrador"),('Instructor', "Instructor")]
estadoCaso = [('Solicitada', 'Solicitada'), ('En Proceso','En Proceso'), ('Finalizada', 'Finalizada')]
tipoSolucion = [('Parcial', 'Parcial'), ('Definitiva', 'Definitiva')]


class Oficina(models.Model):
    Oficina = models.CharField(max_length=15, choices=tipoOficiona)
    nombre = models.CharField(max_length=50, unique=True)
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True)
    fechaHoraActualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.nombre


class Usuario(AbstractUser):
    foto = models.ImageField(upload_to="fotos/", null=True, blank=True)
    tipoUsuario = models.CharField(max_length=50, choices=tipoUsuario)
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True)
    fechaHoraActualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.username


class Solicitud(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    descripcion = models.TextField(max_length=1000)
    oficina = models.ForeignKey(Oficina, on_delete=models.PROTECT)
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True)
    fechaHoraActualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.descripcion


class Caso(models.Model):
    solicitud = models.ForeignKey(Solicitud, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=20, unique=True)
    casoUsuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    estado = models.CharField(
        max_length=20, choices=estadoCaso, default="Solicitada")
    fechaHoraActualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.solicitud.descripcion


class TipoProcedimiento(models.Model):
    nombre = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(max_length=2000, default='sin descripcion')
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True)
    fechaHoraActualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.nombre


class SolucionCaso(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.PROTECT)
    procedimiento = models.TextField(max_length=2000)
    tipoSolucion = models.CharField(max_length=20, choices=tipoSolucion)
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True)
    fechaHoraActualizacion = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.procedimiento


class SolucionCasoTipoProcedimientos(models.Model):
    solucionCaso = models.ForeignKey(SolucionCaso, on_delete=models.PROTECT)
    tipoProcedimiento = models.ForeignKey(
        TipoProcedimiento, on_delete=models.PROTECT)
