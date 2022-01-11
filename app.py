#!/usr/bin/python
# -*- coding: utf-8 -*-
# uvoz potrebnih biblioteka tj modula
import ast
import mysql
import mysql.connector
from flask import Flask, render_template, request, url_for, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash

# deklaracija flask aplikacije

app = Flask(__name__)
app.secret_key = 'tajni_kljuc_aplikacije'

# konekcija za bazom

konekcija = mysql.connector.connect(passwd='nevena123', user='root',
                                    database='evidencija_studenata',
                                    port=3306,
                                    auth_plugin='mysql_native_password')

# kursor objekat koji nam omogucava izvrsavanje upita ka bazi i fetchovanje podataka iz baze

kursor = konekcija.cursor(dictionary=True)


def ulogovan():
    if 'ulogovani_korisnik' in session:
        return True
    else:
        return False


def rola():
    if ulogovan():
        return ast.literal_eval(session['ulogovani_korisnik']).pop('rola')


# logika aplikacije

# GET je dobavaljanje sa servera, POST je postavljanje tj slanje serveru

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        forma = request.form
        upit = "SELECT * FROM korisnici WHERE email=%s"
        vrednost = (forma["email"],)
        kursor.execute(upit, vrednost)
        korisnik = kursor.fetchone()

        if korisnik != None:
            if check_password_hash(korisnik["lozinka"], forma["lozinka"]):
                session['ulogovani_korisnik'] = str(korisnik)
                return redirect(url_for('korisnici'))
            else:
                return render_template('login.html')
        else: 
            return render_template("login.html")


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('ulogovani_korisnik', None)
    return redirect(url_for('login'))


@app.route('/studenti', methods=['GET'])
def studenti():
    if ulogovan():
        upit = 'SELECT * FROM studenti'
        kursor.execute(upit)
        studenti = kursor.fetchall()
        return render_template('studenti.html', studenti=studenti, rola=rola())
    else:
        return redirect(url_for("login"))


@app.route('/student_novi', methods=['GET', 'POST'])
def student_novi():
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        if request.method == 'GET':
            return render_template('student_novi.html')
        if request.method == 'POST':
            forma = request.form
            vrednosti = (
                forma['ime'],
                forma['ime-roditelja'],
                forma['prezime'],
                forma['broj-indeksa'],
                forma['godina-studija'],
                forma['jmbg'],
                forma['datum-rodjenja'],
                forma['espb'],
                forma['prosek'],
                forma['broj-telefona'],
                forma['email'],
            )
            upit = \
                """  INSERT INTO 
                    studenti(ime,ime_roditelja,prezime,broj_indeksa,godina_studija,jmbg,datum_rodjenja,espb,prosek_ocena,broj_telefona,email)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for('studenti'))
    else:
        return redirect(url_for("login"))


@app.route('/student_izmena/<id>', methods=['GET', 'POST'])
def student_izmena(id):
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        if request.method == 'GET':
            upit = 'SELECT * FROM studenti WHERE id=%s'
            vrednost = (id,)
            kursor.execute(upit, vrednost)
            student = kursor.fetchone()
            return render_template('student_izmena.html', student=student)
        if request.method == 'POST':
            forma = request.form
            upit = \
                """  UPDATE studenti SET
                        ime=%s,
                        ime_roditelja=%s,
                        prezime=%s,
                        broj_indeksa=%s,
                        godina_studija=%s,
                        jmbg=%s,
                        datum_rodjenja=%s,
                        espb=%s,
                        prosek_ocena=%s,
                        broj_telefona=%s,
                        email=%s
                        WHERE id = %s
                    """
            vrednosti = (
                forma['ime'],
                forma['ime-roditelja'],
                forma['prezime'],
                forma['broj-indeksa'],
                forma['godina-studija'],
                forma['jmbg'],
                forma['datum-rodjenja'],
                forma['espb'],
                forma['prosek'],
                forma['broj-telefona'],
                forma['email'],
                id,
            )
            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for('studenti'))
    else:
        return redirect(url_for("login"))


@app.route('/student_brisanje/<id>', methods=['POST'])
def student_brisanje(id):
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        upit = """ DELETE FROM studenti WHERE id=%s
            """
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for('studenti'))
    else:
        return redirect(url_for("login"))

@app.route("/student_pregled/<id>", methods=["GET"])
def student_pregled(id):
    upit = "SELECT * FROM studenti WHERE id = %s"
    vrednost=(id,)
    kursor.execute(upit, vrednost)
    student=kursor.fetchone()
    return render_template("student_pregled.html", student=student)


@app.route('/korisnici', methods=['GET'])
def korisnici():
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        #if request.method == "GET":
        upit = 'SELECT * FROM korisnici'  # pravljenjje upita

        # kursor koji smo rekli da sluzi za izvrsavanje upita

        kursor.execute(upit)

        # kursor vraca tupl tj set podataka u kojim imamo sve redove i tako preko fetchall vracamo taj
        # tupl objekat u korisnici

        korisnici = kursor.fetchall()

        # korisnici tupl koji pravimo preko fetchall-a stavimo u promenljivu korisnici preko koje cemo
        # ga renderovati zajedno sa html stranicom

        return render_template('korisnici.html', korisnici=korisnici)
    else:
        return redirect(url_for('login'))


# uzimamo podatke vec postojece odnosno stranicu lokalnu ali moramo i postovati nove podatke

@app.route('/korisnik_novi', methods=['GET', 'POST'])
def korisnik_novi():
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        # vracamo nas regularni templejt

        if request.method == 'GET':
            return render_template('korisnik_novi.html')

        # s druge strane post treba da ubaci nove podatke i u bazu i na stranici da renderuje nove

        if request.method == 'POST':
            forma = request.form  # trazimo celu formu i smestamo je u promenljivu

            # preko metode generate_password_hash iz modula wergzeuk.security cupamo lozinku iz forme i stavljamo
            # je u obliku hasha u promenljivu (bezbednosni razlozi da ne bi svako pri otvaranju baze mogo da vidi
            # te lozinke)

            hesovanaLozinka = generate_password_hash(forma['lozinka'])

            # redom u objekat vrednosti stavljamo nase podatke

            vrednosti = (forma['ime'], forma['prezime'], forma['email'], forma['rola'], hesovanaLozinka)

            # na osnovu izvucenih vrednosti mozemo da pravimo upit

            upit = \
                """  INSERT INTO
                        korisnici(ime,prezime,email,rola,lozinka)
                        VALUES (%s,%s,%s,%s,%s)
                    """
            kursor.execute(upit,
                           vrednosti)  # preko kursora prosledjujemo upit i objekat vrednosti koji ce ispratiti upit \
# tj popuniti ga
            konekcija.commit()  # komitovanje konekcije

            # razlika izmedju redirect i render_template je u http kodu, prva daje 302 a druga 200, a
            # render moze primiti i druge parametre koji pomazu u stvaranju sadrzaja na stranici

            return redirect(url_for('korisnici'))
    else:
        return redirect(url_for('login'))


@app.route('/korisnik_izmena/<id>', methods=['GET',
                                             'POST'])  # konkretizujemo id jer menjamo jednog korisnika at a time,
# kada se klikne na izmenu zelimo da se get pojavi forma, post da posalje na server podatke
def korisnik_izmena(id):
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))        
        if request.method == 'GET':
            # pravmo upit samo za taj kliknuti element

            upit = 'SELECT * FROM korisnici WHERE id=%s'

            # shodno tome prosledjujemo samo taj podatak u obliku tupla i stavljamo zarez

            vrednost = (id,)
            kursor.execute(upit, vrednost)
            korisnik = kursor.fetchone()

            return render_template('korisnik_izmena.html',
                                   korisnik=korisnik)

        if request.method == 'POST':
            forma = request.form
            upit = \
                """  UPDATE korisnici SET
                        ime=%s,
                        prezime=%s,
                        email=%s,
                        rola=%s,
                        lozinka=%s
                        WHERE id = %s
                    """
            vrednosti = (
                forma['ime'],
                forma['prezime'],
                forma['email'],
                forma['rola'],
                forma['lozinka'],
                id,
            )
            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for('korisnici'))
    else:
        return redirect(url_for('login'))


# moramo post i postavljamo delete dugme u formu sa post methodom i akcijom koja navodi ka korisnik_brisanje ruti

@app.route('/korisnik_brisanje/<id>', methods=['POST'])
def korisnik_brisanje(id):
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        upit = """ DELETE FROM korisnici WHERE id=%s
            """
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for('korisnici'))
    else:
        return redirect(url_for('login'))


@app.route('/predmeti', methods=['GET'])
def predmeti():
    if ulogovan():
        upit = 'SELECT * FROM predmeti'
        kursor.execute(upit)
        predmeti = kursor.fetchall()
        return render_template('predmeti.html', predmeti=predmeti)
    else:
        return redirect(url_for('login'))


@app.route('/predmet_novi', methods=['GET', 'POST'])
def predmet_novi():
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        if request.method == 'GET':
            return render_template('predmet_novi.html')
        if request.method == 'POST':
            forma = request.form
            vrednosti = (forma['sifra'], forma['naziv'],
                         forma['godina-studija'], forma['espb'],
                         forma['obavezni-izborni'])
            upit = \
                """ INSERT INTO 
                        predmeti(sifra,naziv,godina_studija,espb,obavezni_izborni)
                        VALUES(%s,%s,%s,%s,%s)
                    """
            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for('predmeti'))
    else:
        return redirect(url_for('login'))


@app.route('/predmet_izmena/<id>', methods=['GET', 'POST'])
def predmet_izmena(id):
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        if request.method == 'GET':
            vrednost = (id,)
            upit = 'SELECT * FROM predmeti WHERE id=%s'
            kursor.execute(upit, vrednost)
            predmet = kursor.fetchone()
            return render_template('predmet_izmena.html',
                                   predmet=predmet)
        if request.method == 'POST':
            forma = request.form
            vrednosti = (
                forma['sifra'],
                forma['naziv'],
                forma['godina-studija'],
                forma['espb'],
                forma['obavezni-izborni'],
                id,
            )
            upit = \
                """  UPDATE predmeti SET
                        sifra=%s,
                        naziv=%s,
                        godina_studija=%s,
                        espb=%s,
                        obavezni_izborni=%s
                        WHERE id=%s
                    """
            kursor.execute(upit, vrednosti)
            konekcija.commit()
            return redirect(url_for('predmeti'))
    else:
        return redirect(url_for('login'))


@app.route('/predmet_brisanje/<id>', methods=['POST'])
def predmet_brisanje(id):
    if ulogovan():
        if rola() == "profesor":
            return redirect(url_for("studenti"))
        upit = 'DELETE FROM predmeti WHERE id=%s'
        vrednost = (id,)
        kursor.execute(upit, vrednost)
        konekcija.commit()
        return redirect(url_for('predmeti'))
    else:
        return redirect(url_for('login'))


# pokretanje aplikacije, koristimo debug=true da bi svaka izmena sama automatski osvezivala stranicu,
# a ne stvaki put da restartujemo manuelno server

app.run(debug=True)
