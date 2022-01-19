import ast
import csv
from curses import meta
import io
import os
import mysql
import mysql.connector
from flask import Flask, render_template, request, url_for, redirect, session, Response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "tajni_kljuc_aplikacije"

UPLOAD_FOLDER = "static/uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "evidencija.atvss@gmail.com"
app.config["MAIL_PASSWORD"] = "atvss123loz"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)

konekcija = mysql.connector.connect(
    passwd="nevena123",
    user="root",
    database="evidencija_studenata_Nevena",
    port=3306,
    auth_plugin="mysql_native_password",
)

kursor = konekcija.cursor(dictionary=True)


def send_email(ime, prezime, email, lozinka):
    msg = Message(subject="Korisnički nalog",
                  sender="ATVSS Evidencija studenata", recipients=[email],)
    msg.html = render_template(
        "email.html", ime=ime, prezime=prezime,  lozinka=lozinka)
    mail.send(msg)
    return "Sent"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        forma = request.form
        upit = "SELECT * FROM korisnici WHERE email=%s"
        vrednost = (forma["email"],)
        kursor.execute(upit, vrednost)
        korisnik = kursor.fetchone()

        if korisnik != None:
            if check_password_hash(korisnik["lozinka"], forma["lozinka"]):
                session["ulogovani_korisnik"] = str(korisnik)
                return redirect(url_for("korisnici"))
            else:
                return render_template("login.html")
        else:
            return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("ulogovani_korisnik", None)
    return redirect(url_for("login"))


@app.route("/studenti", methods=["GET"])
def studenti():
    strana = request.args.get("page", "1")
    offset = int(strana) * 10 - 10
    prethodna_strana = ""
    sledeca_strana = "/studenti?page=2"
    if "=" in request.full_path:
        split_path = request.full_path.split("=")
        del split_path[-1]
        sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
        prethodna_strana = "=".join(split_path) + "=" + str(int(strana) - 1)

    args = request.args.to_dict()
    order_by = "id"
    order_type = "asc"

    if "order_by" in args:
        order_by = args["order_by"].lower()
        if (
            "prethodni_order_by" in args
            and args["prethodni_order_by"] == args["order_by"]
        ):
            if args["order_type"] == "asc":
                order_type = "desc"

    s_ime = "%%"
    s_prezime = "%%"
    s_broj_indeksa = "%%"
    s_godina_studija = "%%"
    s_prosek_ocena_od = "0"
    s_prosek_ocena_do = "10"

    if "prosek_ocena_od" in args:
        if args["prosek_ocena_od"] == "":
            s_prosek_ocena_od = "0"
        else:
            s_prosek_ocena_od = args["prosek_ocena_od"]
    if "prosek_ocena_do" in args:
        if args["prosek_ocena_do"] == "":
            s_prosek_ocena_do = "10"
        else:
            s_prosek_ocena_do = args["prosek_ocena_do"]
    s_espb_od = "0"
    s_espb_do = "240"
    if "espb_od" in args:
        if args["espb_od"] == "":
            s_espb_od = "0"
        else:
            s_espb_od = args["espb_od"]
    if "espb_do" in args:
        if args["espb_do"] == "":
            s_espb_do = "240"
        else:
            s_espb_do = args["espb_do"]

    if "ime" in args:
        s_ime = "%" + args["ime"] + "%"
    if "prezime" in args:
        s_prezime = "%" + args["prezime"] + "%"
    if "broj_indeksa" in args:
        s_broj_indeksa = "%" + args["broj_indeksa"] + "%"
    if "godina_studija" in args:
        s_godina_studija = "%" + args["godina_studija"] + "%"

    upit = "SELECT * FROM studenti WHERE ime LIKE %s AND prezime LIKE %s AND broj_indeksa LIKE %s AND godina_studija LIKE %s AND espb >= %s AND espb <= %s AND prosek_ocena >= %s AND prosek_ocena <= %s ORDER BY " + \
        order_by + " " + order_type + " LIMIT 5 OFFSET %s"
    vrednosti = (
        s_ime,
        s_prezime,
        s_broj_indeksa,
        s_godina_studija,
        s_espb_od,
        s_espb_do,
        s_prosek_ocena_od,
        s_prosek_ocena_do,
        offset,
    )
    kursor.execute(upit, vrednosti)
    studenti = kursor.fetchall()
    return render_template("studenti.html", studenti=studenti, strana=strana, sledeca_strana=sledeca_strana, prethodna_strana=prethodna_strana, order_type=order_type, args=args)


@app.route("/student_novi", methods=["GET", "POST"])
def student_novi():
    if request.method == "GET":
        return render_template("student_novi.html")
    if request.method == "POST":
        forma = request.form
        naziv_slike = ""
        if "slika" in request.files:
            file = request.files["slika"]

            if file.filename:
                naziv_slike = forma["jmbg"] + file.filename
                file.save(os.path.join(
                    app.config["UPLOAD_FOLDER"], naziv_slike))

        vrednosti = (
            forma["ime"],
            forma["ime-roditelja"],
            forma["prezime"],
            forma["broj-indeksa"],
            forma["godina-studija"],
            forma["jmbg"],
            forma["datum-rodjenja"],
            forma["espb"],
            forma["prosek"],
            forma["broj-telefona"],
            forma["email"],
            naziv_slike,
        )
        upit = "INSERT INTO studenti (ime,ime_roditelja,prezime,broj_indeksa,godina_studija,jmbg,datum_rodjenja,espb,prosek_ocena,broj_telefona,email,slika) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for("studenti"))


@app.route("/student_izmena/<id>", methods=["GET", "POST"])
def student_izmena(id):
    if request.method == "GET":
        upit = "SELECT * FROM studenti WHERE id=%s"
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        student = kursor.fetchone()
        return render_template("student_izmena.html", student=student)
    if request.method == "POST":
        forma = request.form
        naziv_slike = ""
        if "slika" in request.files:
            file = request.files["slika"]
            if file.filename:
                naziv_slike = forma["jmbg"] + file.filename
                file.save(os.path.join(
                    app.config["UPLOAD_FOLDER"], naziv_slike))

        upit = "UPDATE studenti SET ime=%s, ime_roditelja=%s, prezime=%s, broj_indeksa=%s, godina_studija=%s, jmbg=%s, datum_rodjenja=%s, espb=%s, prosek_ocena=%s,broj_telefona=%s, email=%s, slika=%s WHERE id = %s"

        vrednosti = (
            forma["ime"],
            forma["ime-roditelja"],
            forma["prezime"],
            forma["broj-indeksa"],
            forma["godina-studija"],
            forma["jmbg"],
            forma["datum-rodjenja"],
            forma["espb"],
            forma["prosek"],
            forma["broj-telefona"],
            forma["email"],
            naziv_slike,
            id
        )

        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for("studenti"))


@app.route("/student_brisanje/<id>", methods=["GET", "POST"])
def student_brisanje(id):
    upit = """ DELETE FROM studenti WHERE id=%s
            """
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()
    return redirect(url_for("studenti"))


@app.route("/student_pregled/<id>", methods=["GET"])
def student_pregled(id):
    if request.method == "GET":
        studentUpit = "SELECT * FROM studenti WHERE id = %s"
        vrednost = (id,)
        kursor.execute(studentUpit, vrednost)
        student = kursor.fetchone()

        predmetUpit = "SELECT * FROM predmeti"
        kursor.execute(predmetUpit)
        predmeti = kursor.fetchall()

        oceneUpit = "SELECT * FROM predmeti JOIN ocene ON predmeti.id=ocene.predmet_id WHERE ocene.student_id = %s"
        vrednost = (id,)
        kursor.execute(oceneUpit, vrednost)
        ocene = kursor.fetchall()

        return render_template("student_pregled.html", student=student, predmeti=predmeti, ocene=ocene)


@app.route("/ocena_nova/<id>", methods=["POST"])
def ocena_nova(id):
    forma = request.form
    upit = " INSERT INTO ocene (student_id, predmet_id, ocena, datum) VALUES (%s, %s, %s, %s)"
    vrednosti = (id,
                 forma['predmet'],
                 forma['ocena'],
                 forma['datum']
                 )
    kursor.execute(upit, vrednosti)
    konekcija.commit()

    # PROSEK OCENA
    upit = "SELECT AVG(ocena) AS rezultat FROM ocene WHERE student_id = %s"
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    prosek_ocena = kursor.fetchone()

    # ESPB
    upit = "SELECT SUM(espb) AS rezultat FROM predmeti WHERE id IN (SELECT predmet_id FROM ocene WHERE student_id = %s)"
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    espb = kursor.fetchone()

    # Izmeni tabelu student
    upit = "UPDATE studenti SET espb = %s, prosek_ocena = %s WHERE id=%s"
    vrednosti = (espb['rezultat'], prosek_ocena['rezultat'], id)
    kursor.execute(upit, vrednosti)
    konekcija.commit()
    student = kursor.fetchone()

    return redirect(url_for('student_pregled', id=id, espb=espb, prosek_ocena=prosek_ocena, student=student))


@app.route("/ocena_izmena/<id>", methods=["GET", "POST"])
def ocena_izmena(id):
    if request.method == "GET":
        vrednost = (id,)
        upit = "SELECT * FROM ocene WHERE id=%s"
        kursor.execute(upit, vrednost)
        ocena = kursor.fetchone()
        return render_template("ocena_izmena.html", ocena=ocena)
    if request.method == "POST":
        forma = request.form
        upit = "UPDATE ocene SET ocena = %s WHERE id = %s"
        vrednosti = (forma["ocena"], id)
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for("studenti"))


@app.route("/ocena_brisanje/<id>", methods=["GET", "POST"])
def ocena_brisanje(id):
    upit = "DELETE FROM ocene WHERE id=%s"
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()
    return redirect(url_for("studenti"))


@app.route("/korisnici", methods=["GET"])
def korisnici():
    if request.method == "GET":
        strana = request.args.get("page", "1")
        offset = int(strana) * 10 - 10
        prethodna_strana = ""
        sledeca_strana = "/korisnici?page=2"
        if "=" in request.full_path:
            split_path = request.full_path.split("=")
            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(
                split_path) + "=" + str(int(strana) - 1)
        upit = """
            SELECT * FROM korisnici
            LIMIT 10 OFFSET %s
        """
        vrednosti = (
            offset,
        )
        kursor.execute(upit, vrednosti)
        korisnici = kursor.fetchall()
        return render_template("korisnici.html", korisnici=korisnici, strana=strana, sledeca_strana=sledeca_strana, prethodna_strana=prethodna_strana)


@app.route("/korisnik_novi", methods=["GET", "POST"])
def korisnik_novi():
    if request.method == "GET":
        return render_template("korisnik_novi.html")

    if request.method == "POST":
        forma = request.form
        hesovanaLozinka = generate_password_hash(forma["lozinka"])
        vrednosti = (
            forma["ime"],
            forma["prezime"],
            forma["email"],
            forma["rola"],
            hesovanaLozinka,
        )
        upit = """  INSERT INTO
                        korisnici(ime,prezime,email,rola,lozinka)
                        VALUES (%s,%s,%s,%s,%s)
                    """
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        send_email(forma["ime"], forma["prezime"],
                   forma["email"], forma["lozinka"])
        return redirect(url_for("korisnici"))


@app.route("/korisnik_izmena/<id>", methods=["GET", "POST"])
def korisnik_izmena(id):
    if request.method == "GET":
        upit = "SELECT * FROM korisnici WHERE id=%s"
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        korisnik = kursor.fetchone()
        return render_template("korisnik_izmena.html", korisnik=korisnik)

    if request.method == "POST":
        forma = request.form
        hesovanaLozinka = generate_password_hash(forma["lozinka"])
        upit = """  UPDATE korisnici SET
                        ime=%s,
                        prezime=%s,
                        email=%s,
                        rola=%s,
                        lozinka=%s
                        WHERE id = %s
                    """
        vrednosti = (
            forma["ime"],
            forma["prezime"],
            forma["email"],
            forma["rola"],
            hesovanaLozinka,
            id,
        )
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for("korisnici"))


@app.route("/korisnik_brisanje/<id>", methods=["GET", "POST"])
def korisnik_brisanje(id):
    upit = """ DELETE FROM korisnici WHERE id=%s
            """
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()
    return redirect(url_for("korisnici"))


@app.route("/predmeti", methods=["GET"])
def predmeti():
    if request.method == "GET":
        strana = request.args.get("page", "1")
        offset = int(strana) * 10 - 10
        prethodna_strana = ""
        sledeca_strana = "/predmeti?page=2"
        if "=" in request.full_path:
            split_path = request.full_path.split("=")
            del split_path[-1]
            sledeca_strana = "=".join(split_path) + "=" + str(int(strana) + 1)
            prethodna_strana = "=".join(
                split_path) + "=" + str(int(strana) - 1)
        upit = """
            SELECT * FROM predmeti 
            LIMIT 10 OFFSET %s
        """
        vrednosti = (
            offset,
        )
        kursor.execute(upit, vrednosti)
        predmeti = kursor.fetchall()
        return render_template("predmeti.html", predmeti=predmeti, strana=strana, sledeca_strana=sledeca_strana, prethodna_strana=prethodna_strana)


@app.route("/predmet_novi", methods=["GET", "POST"])
def predmet_novi():
    if request.method == "GET":
        return render_template("predmet_novi.html")
    if request.method == "POST":
        forma = request.form
        vrednosti = (
            forma["sifra"],
            forma["naziv"],
            forma["godina-studija"],
            forma["espb"],
            forma["obavezni-izborni"],
        )
        upit = """ INSERT INTO 
                        predmeti(sifra,naziv,godina_studija,espb,obavezni_izborni)
                        VALUES(%s,%s,%s,%s,%s)
                    """
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for("predmeti"))


@app.route("/predmet_izmena/<id>", methods=["GET", "POST"])
def predmet_izmena(id):
    if request.method == "GET":
        vrednost = (id,)
        upit = "SELECT * FROM predmeti WHERE id=%s"
        kursor.execute(upit, vrednost)
        predmet = kursor.fetchone()
        return render_template("predmet_izmena.html", predmet=predmet)
    if request.method == "POST":
        forma = request.form
        vrednosti = (
            forma["sifra"],
            forma["naziv"],
            forma["godina-studija"],
            forma["espb"],
            forma["obavezni-izborni"],
            id,
        )
        upit = """  UPDATE predmeti SET
                        sifra=%s,
                        naziv=%s,
                        godina_studija=%s,
                        espb=%s,
                        obavezni_izborni=%s
                        WHERE id=%s
                    """
        kursor.execute(upit, vrednosti)
        konekcija.commit()
        return redirect(url_for("predmeti"))


@app.route("/predmet_brisanje/<id>", methods=["GET", "POST"])
def predmet_brisanje(id):
    upit = """ DELETE FROM predmeti WHERE id=%s
            """
    vrednost = (id,)
    kursor.execute(upit, vrednost)
    konekcija.commit()
    return redirect(url_for("predmeti"))


@app.route("/export/<tip>")
def export(tip):
    switch = {
        "studenti": "SELECT * FROM studenti",
        "korisnici": "SELECT * FROM korisnici",
        "predmeti": "SELECT * FROM predmeti",
        }
    upit = switch.get(tip)

    kursor.execute(upit)
    rezultat = kursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    for row in rezultat:
        red = []
        for value in row.values():
            red.append(str(value))
        writer.writerow(red)

    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=" + tip + ".csv"},)

app.run(debug=True)
