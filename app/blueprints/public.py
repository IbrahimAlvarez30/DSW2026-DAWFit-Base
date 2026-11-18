from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from app.models import db, Actividad

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/actividades")
def mostrar_actividades():
    consulta = Actividad.query
    palabra = request.args.get("busqueda", "")

    consultaCheck = request.args.get("solo_con_plazas", "")

    if palabra:
        consulta = consulta.filter(Actividad.nombre.contains(palabra))
        print(f"estoy filtrando {palabra}")
    if consultaCheck:
        consulta = consulta.filter(Actividad.plazas_libres > 0)
    actividades = consulta.all()

    deporte_fav = request.cookies.get("deporte_fav")

    return render_template(
        "catalogo.html",
        lista_actividades=actividades,
        deporte_fav=deporte_fav,
    )


@public_bp.route("/actividad/<int:act_id>")
def ver_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>")
def guardar_preferencia(deporte):
    respuesta = make_response(redirect(url_for("public.mostrar_actividades")))
    respuesta.set_cookie(
        "deporte_fav",
        deporte,
        max_age=15 * 24 * 60 * 60,
        httponly=True,
        samesite="Lax",
    )
    return respuesta


@public_bp.route("/limpiar-preferencia")
def limpiar_preferencia():
    respuesta = make_response(redirect(url_for("public.mostrar_actividades")))
    respuesta.delete_cookie("deporte_fav")
    return respuesta


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    session.permanent = True
    reservas = session.get("reservas", [])

    if actividad.plazas_libres <= 0:
        flash("Esta actividad no tiene plazas libres.", "error")
    elif act_id in reservas:
        flash("Ya estás apuntado a esta actividad.", "error")
    elif len(reservas) >= 3:
        flash("Solo puedes tener 3 actividades en tu lista de reservas.", "error")
    else:
        reservas.append(act_id)
        session["reservas"] = reservas
        session.modified = True
        flash(f"Te has apuntado a {actividad.nombre}.", "exito")

    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas")
@login_required
def ver_reservas():
    ids = session.get("reservas", [])
    actividades = Actividad.query.filter(Actividad.id.in_(ids)).all()

    total_sin_descuento = sum(act.cuota for act in actividades)
    descuento_aplicado = len(ids) == 3
    if descuento_aplicado:
        total_final = total_sin_descuento * 0.80
    else:
        total_final = total_sin_descuento

    return render_template(
        "reservas.html",
        actividades=actividades,
        total_sin_descuento=total_sin_descuento,
        descuento_aplicado=descuento_aplicado,
        total_final=total_final,
    )


@public_bp.route("/reservas/cancelar/<int:act_id>", methods=["POST"])
@login_required
def cancelar_reserva(act_id):
    reservas = session.get("reservas", [])
    if act_id in reservas:
        reservas.remove(act_id)
        session["reservas"] = reservas
        session.modified = True
        flash("Actividad quitada de tu lista de reservas.", "info")
    else:
        flash("Esa actividad no estaba en tu lista.", "error")
    return redirect(url_for("public.ver_reservas"))


@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():
    ids = session.get("reservas", [])
    if not ids:
        flash("No tienes actividades para confirmar.", "error")
        return redirect(url_for("public.ver_reservas"))

    actividades = Actividad.query.filter(Actividad.id.in_(ids)).all()
    for act in actividades:
        act.plazas_libres -= 1
    db.session.commit()

    session.pop("reservas", None)
    flash("Inscripciones confirmadas correctamente.", "exito")
    return redirect(url_for("public.mostrar_actividades"))
