from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate
from django.contrib import auth
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.shortcuts import render
from appService.models import *
import random
from django.conf import settings
from django.db import Error, transaction
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
import threading
from smtplib import SMTPException
import string
from django.contrib.auth.models import Group
# Create your views here.


def inicio(request):
    return render(request, "iniciarSesion.html")


def inicioAdministrador(request):
    if request.user.is_authenticated:
        datosSesion = {
            "usuario": request.user,
            "rol": request.user.groups.get().name
        }
        return render(request, "administrador/inicioAdmin.html", datosSesion)
    else:
        mensaje = "Debe iniciar seccion"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def inicioTecnico(request):
    if request.user.is_authenticated:
        datosSesion = {
            "usuario": request.user,
            "rol": request.user.groups.get().name
        }
        return render(request, "tecnico/inicioTecn.html", datosSesion)
    else:
        mensaje = "Debe iniciar seccion"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def inicioEmpleado(request):
    if request.user.is_authenticated:
        datosSesion = {
            "usuario": request.user,
            "rol": request.user.groups.get().name
        }
        return render(request, "empleado/inicioEmple.html", datosSesion)
    else:
        mensaje = "Debe iniciar seccion"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})


@csrf_exempt
def login(request):
    username = request.POST["usuario"]
    print(username)
    password = request.POST["password"]
    print(password)
    user = authenticate(username=username, password=password)
    print(user)
    if user is not None:
        auth.login(request, user)
        print("hola")
        if user.groups.filter(name='Administrador').exists():
            return redirect('/inicioAdministrador')
        elif user.groups.filter(name='Tecnico').exists():
            return redirect('/inicioTecnico')
        else:
            return redirect('/inicioEmpleado')
    else:
        mensaje = "Usuario o Contraseña no validad"
        return redirect('/')
        # return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def registroSolicitud(request):
    try:
        with transaction.atomic():
            user = request.user
            descripcion = request.POST['descripcion']
            idOficina = int(request.POST['cbOficina'])
            oficina = Oficina.objects.get(pk=idOficina)
            solicitud = Solicitud(
                usuario=user,
                descripcion=descripcion,
                oficina=oficina,
            )
            solicitud.save()
            fecha = datetime.now()
            year = fecha.year
            consecutivoCaso = Solicitud.objects.filter(
                fechaHoraCreacion__year=year).count()
            consecutivoCaso = str(consecutivoCaso).rjust(5, '0')
            codigoCaso = f"REQ-{year}-{consecutivoCaso}"
            userCaso = Usuario.objects.filter(
                groups__name__in=['Administrador']).first()
            estado = "Solicitada"
            caso = Caso(
                solicitud=solicitud,
                codigo=codigoCaso,
                casoUsuario=userCaso,
                estado=estado,
            )
            caso.save()
            asunto = 'Registro Solicitud - Mesa De Servicio'
            mensaje = (f'Cordial saludo, <b>{user.first_name} {user.last_name}</b>, nos permitimos '
                       f'informarle que su solicitud fue registrada en nuestro sistema con el número de caso '
                       f'<b>{
                codigoCaso}</b>. <br><br> Su caso será gestionado en el menor tiempo posible, '
                f'según los acuerdos de solución establecidos para la Mesa de Servicios del CTPI-CAUCA.'
                f'<br><br>Lo invitamos a ingresar a nuestro sistema en la siguiente url: '
                'http://mesadeservicioctpicauca.sena.edu.co.')
            thread = threading.Thread(
                target=enviarCorreo, args=(asunto, mensaje, [user.email]))
            thread.start()
            mensaje = "Se ha registrado su solicitud de manera exitosa"
    except Exception as e:
        transaction.rollback()
        mensaje = f"Error: {e}"
        return render(request, "error.html", {"message": mensaje})

    oficina = Oficina.objects.all()
    retorno = {"mensaje": mensaje, "oficina": oficina}
    return render(request, "empleado/solicitud.html", retorno)


def vistaSolicitud(request):
    if request.user.is_authenticated:
        oficina = Oficina.objects.all()
        datosSesion = {
            "user": request.user,
            "rol": request.user.groups.get().name,
            'oficina': oficina,
        }
        return render(request, 'empleado/solicitud.html', datosSesion)
    else:
        mensaje = "Debes iniciar Sesion"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def enviarCorreo(asunto=None, mensaje=None, destinatario=None, archivo=None):
    remitente = settings.EMAIL_HOST_USER
    template = get_template('correo.html')
    contenido = template.render({
        'mensaje': mensaje
    })
    try:
        correo = EmailMultiAlternatives(
            asunto, mensaje, remitente, destinatario
        )
        correo.attach_alternative(contenido, 'text/html')
        if archivo != None:
            correo.attach_file(archivo)
        correo.send(fail_silently=True)
        print("enviado")
    except SMTPException as error:
        print(error)


def listarCasos(request):
    try:
        mensaje = ""
        # listarCasos = Caso.objects.filter(estado = 'Solicitada')
        listarCasos = Caso.objects.all()
        tecnicos = Usuario.objects.filter(groups__name__in=['Tecnico'])

    except Error as error:
        mensaje = str(error)

    retorno = {"listarCasos": listarCasos,
               "tecnicos": tecnicos, "mensaje": mensaje}
    return render(request, "administrador/listaCasos.html", retorno)


def listarEmpleadosTecnicos(request):
    try:
        mensaje = ""
        tecnicos = Usuario.objects.filter(groups__name__in=['Tecnico'])
    except Error as error:
        mensaje = str(error)

    retorno = {"tecnicos": tecnicos, "mensaje": mensaje}
    return JsonResponse(retorno)


def asignarTecnico(request):
    if request.user.is_authenticated:
        try:
            print("Hola")
            idTecnico = int(request.POST['cbTecnico'])
            userTecnico = Usuario.objects.get(pk=idTecnico)
            idCaso = int(request.POST['idCaso'])
            caso = Caso.objects.get(pk=idCaso)
            caso.casoUsuario = userTecnico
            caso.estado = "En Proceso"
            caso.save()
            # enviar correo al tecnico
            asunto = 'Asignacion caso - Mesa de servicio'
            mensaje = f'Cordial saludo, <b>{userTecnico.first_name} {userTecnico.last_name}</b>, nos permitimos \
                informarle que se le ha asignado un caso para dar solucion. Codigo de caso: \
                <b>{caso.codigo}</b>. <br><br> Se solicita se atienda de manera oportuna \
                según los acuerdos de solución establecidos para la Mesa de Servicios del CTPI-CAUCA.\
                <br><br>Lo invitamos a ingresar al sistema para gestionar sus casos asignados en la siguiente url:\
                http://mesadeservicioctpicauca.sena.edu.co.'
            thread = threading.Thread(
                target=enviarCorreo, args=(asunto, mensaje, [userTecnico.email]))
            thread.start()
            mensaje = "Caso Asignado"
        except Error as error:
            mensaje = str(error)
        return redirect('/listarCasosAsignar/')
    else:
        mensaje = "Debe iniciar sesion"
    return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def listarCasosAsignados(request):
    if request.user.is_authenticated:
        try:
            listarCasos = Caso.objects.filter(
                estado='En Proceso', casoUsuario=request.user)
            listarTipoProcedimiento = TipoProcedimiento.objects.all().values()
            mensaje = "Listado de caso asignados"
        except Error as error:
            mensaje = str(error)
        retorno = {"mensaje": mensaje, "listarCasos": listarCasos,
                   "listaTipoSolucion": tipoSolucion, "listarTipoProcedimiento": listarTipoProcedimiento}
        return render(request, "tecnico/listarAsignados.html", retorno)
    else:
        mensaje = "Debes iniciar Sesion"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def salir(request):
    auth.logout(request)
    return redirect('/')
    # mensaje = "Has cerrado sesion"
    # return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def solucionarCaso(request):
    if request.user.is_authenticated:
        try:
            if transaction.atomic():
                procedimiento = request.POST['procedimiento']
                tipoPro = int(request.POST['cbTipoProcedimiento'])
                tipoProcedimiento = TipoProcedimiento.objects.get(pk=tipoPro)
                tipoSolucion = request.POST['cbTipoSolucion']
                idCaso = int(request.POST['idCaso'])
                caso = Caso.objects.get(pk=idCaso)
                solucionCaso = SolucionCaso(
                    caso=caso,
                    procedimiento=procedimiento,
                    tipoSolucion=tipoSolucion
                )
                solucionCaso.save()
                if (tipoSolucion == "Definitiva"):
                    caso.estado = "Finalizada"
                    caso.save()
                solucionCasoTipoProcedimientos = SolucionCasoTipoProcedimientos(
                    solucionCaso=solucionCaso,
                    tipoProcedimiento=tipoProcedimiento
                )
                solucionCasoTipoProcedimientos.save()
                solicitud = caso.solicitud
                userEmpleado = solicitud.usuario
                asunto = 'Solucion Caso - CTPI CAUCA'
                mensaje = f'Cordial saludo, <b>{userEmpleado.first_name} {userEmpleado.last_name}</b>, nos permitimos \
                informarle que se le ha dado solucion de tipo {tipoSolucion}. Al caso identificado con el codigo: \
                <b>{caso.codigo}</b>.<br>Lo invitamos a revisar el equipo y verificar la solucion\
                <br><br>Para consultar en detalle la solucion,ingresar al sistema para verificar las solicitudes registradas en la siguiente url:\
                http://mesadeservicioctpicauca.sena.edu.co.'
            thread = threading.Thread(
                target=enviarCorreo, args=(asunto, mensaje, [userEmpleado.email]))
            thread.start()
            mensaje = "Solucion Caso"

        except Error as error:
            transaction.rollback()
            mensaje = str(error)
        retorno = {"mensaje": mensaje}
        return redirect('/listarCasosAsignados/')

    else:
        mensaje = "Debes iniciar Sesion"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def listarSolicitudes(request):
    if request.user.is_authenticated:
        try:
            mensaje = ""
            listarSolicitud = Caso.objects.all()
        except Error as error:
            mensaje = str(error)
        retorno = {"mensaje": mensaje, "listarSolicitud": listarSolicitud}
        return render(request, "empleado/listarSolicitud.html", retorno)
    else:
        mensaje = "Debe iniciar sesion"
    return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def generarPassword():
    longitud = 10
    caracteres = string.ascii_lowercase + \
        string.ascii_uppercase + string.digits + string.punctuation
    password = ''
    for i in range(longitud):
        password += ''.join(random.choice(caracteres))
    return password


def registrarUsuario(request):
    if request.user.is_authenticated:
        try:
            nombres = request.POST['nombre']
            apellidos = request.POST['apellido']
            correo = request.POST['correo']
            tipo = request.POST['cbTipo']
            foto = request.FILES.get('fileFoto')
            idRol = int(request.POST['cbRol'])
            with transaction.atomic():
                user = Usuario(username=correo, first_name=nombres, last_name=apellidos, email=correo, tipoUsuario=tipo, foto=foto)
                user.save()
                rol = Group.objects.get(pk=idRol)
                user.groups.add(rol)
                if (rol.name == 'Adminstrador'):
                    user.is_staff = True
                user.save()
                passwordGenerado = generarPassword()
                print(f'password{passwordGenerado}')
                user.set_password(passwordGenerado)
                user.save()
                mensaje = "Usuario Agregado Correctamente"
                retorno = {"mensaje": mensaje}
                asunto = 'Registro Sistema Mesa de Servicio CTPI-CAUCA'
                mensaje = f'Cordial saludo, <b>{user.first_name} {user.last_name}</b>, nos permitimos \
                    informarle que usted ha sido registrado en el Sistema de Mesa de Servicio \
                    del Centro de Teleinformática y Producción Industrial CTPI de la ciudad de Popayán, \
                    con el Rol: <b>{rol.name}</b>. \
                    <br>Nos permitimos enviarle las credenciales de Ingreso a nuestro sistema.<br>\
                    <br><b>Username: </b> {user.username}\
                    <br><b>Password: </b> {passwordGenerado}\
                    <br><br>Lo invitamos a utilizar el aplicativo, donde podrá usted \
                    realizar solicitudes a la mesa de servicio del Centro. Url del aplicativo: \
                    http://mesadeservicioctpi.sena.edu.co.'
                thread = threading.Thread(
                    target=enviarCorreo, args=(asunto, mensaje, [user.email]))
                thread.start()
                return redirect("/vistaGestionarUsuarios/", retorno)
        except Error as error:
            transaction.rollback()
            mensaje = f"{error}"
            retorno = {"mensaje": mensaje}
            return render(request, 'administrador/registarUsuario.html', retorno)
    else:
        mensaje = "Debes iniciar Sesion"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})


def vistaRegistrarUsuario(request):
    if request.user.is_authenticated:
        roles = Group.objects.all()
        retorno = {"roles": roles, "user": request.user,
                'tipoUsuario': tipoUsuario, "rol": request.user.groups.get().name}
        return render(request, "administrador/registrarUsuario.html", retorno)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "registrarUsuario.html", {"mensaje": mensaje})


def vistaGestionarUsuarios(request):
    if request.user.is_authenticated:
        usuarios = Usuario.objects.all()
        retorno = {"usuarios": usuarios, "user": request.user,
                "rol": request.user.groups.get().name}
        return render(request, "administrador/gestionUsuario.html", retorno)
    else:
        mensaje = "Debe iniciar sesión"
        return render(request, "iniciarSesion.html", {"mensaje": mensaje})

    
def recuperarClave(request):
    try:
        correo = request.POST['correo']
        user = Usuario.objects.filter(email=correo).first()
        if user:
            passwordGenerado = generarPassword()
            user.set_password(passwordGenerado)
            user.save()
            mensaje = 'Contraseña Actualiza Correctamente y enviada al Correo Electrónico'
            retorno = {'mensaje': mensaje}
            asunto = 'Recuperación de Contraseña Sistema Mesa de Servicio CTPI-CAUCA'
            mensaje = f'Cordial saludo, <b>{user.first_name} {user.last_name}</b>, nos permitimos informarle que se ha generado una nueva contraseña para el ingreso del sistema. <br><b>Username:</b> {
                user.username}<br><b>Password:</b> {passwordGenerado}<br><br>Para comprobar ingrese al sistema haciendo uso de la nueva contraseña.'
            thread = threading.Thread(
                target=enviarCorreo, args=(asunto, mensaje, [user.email]))
            thread.start()
        else:
            mensaje = 'No existe usuario con el correo ingresado. Revisar'
            retorno = {'mensaje': mensaje}
    except Exception as error:
        mensaje = str(error)
    return render(request, 'iniciarSesion.html', retorno)
