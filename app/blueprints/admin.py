import os
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, login_manager, Actividad
from app.forms import ActividadForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

"""ejercicio 2.3"""


@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()
    if form.validate_on_submit():
        nueva = Actividad(
            nombre=form.nombre.data,
            deporte=form.deporte.data,
            cuota=form.cuota.data,
            plazas_libres=form.plazas_libres.data,
        )
        archivo = form.archivo_imagen.data
        if archivo:
            nueva.imagen = guardar_cartel(archivo, nueva.deporte)

        db.session.add(nueva)
        db.session.commit()
        flash("Actividad creada correctamente.", "exito")
        return redirect(url_for("public.mostrar_actividades"))

    return render_template(
        "actividad_form.html", form=form, titulo="Nueva Actividad Deportiva"
    )


@admin_bp.before_request
def proteger_zona_admin():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.es_monitor:
        abort(403)


@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad, nombre_original=actividad.nombre)

    if form.validate_on_submit():
        actividad.nombre = form.nombre.data
        actividad.deporte = form.deporte.data
        actividad.cuota = form.cuota.data
        actividad.plazas_libres = form.plazas_libres.data

        archivo = form.archivo_imagen.data
        if archivo:
            nueva_imagen = guardar_cartel(archivo, actividad.deporte)
            if actividad.imagen and actividad.imagen != nueva_imagen:
                ruta_antigua = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], actividad.imagen
                )
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)
            actividad.imagen = nueva_imagen

        db.session.commit()
        flash("Actividad actualizada correctamente.", "exito")
        return redirect(url_for("public.mostrar_actividades"))

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)

    if actividad.plazas_libres == 0:
        flash("No se puede eliminar una actividad con el cupo lleno.", "error")
        return redirect(url_for("public.mostrar_actividades"))

    if actividad.imagen:
        ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], actividad.imagen)
        if os.path.exists(ruta):
            os.remove(ruta)

    db.session.delete(actividad)
    db.session.commit()
    flash("Actividad eliminada correctamente.", "exito")
    return redirect(url_for("public.mostrar_actividades"))


"""ejercicio 2.3"""


def guardar_cartel(archivo, deporte):
    """Guarda el archivo en disco como <deporte>_<nombre_seguro> y devuelve ese nombre."""
    """Limpia el nombre original que subió el monitor"""
    nombre_seguro = secure_filename(archivo.filename)
    prefijo = secure_filename(deporte.lower())
    """Se construye el nombre seguro"""
    nombre_final = f"{prefijo}_{nombre_seguro}"
    """current_app.config["UPLOAD_FOLDER"] Lee la carpeta configurada"""
    carpeta = current_app.config["UPLOAD_FOLDER"]
    """Lo crea si no existe"""
    os.makedirs(carpeta, exist_ok=True)
    """Guarda fisicamente el archivo en el disco"""
    archivo.save(os.path.join(carpeta, nombre_final))
    return nombre_final
