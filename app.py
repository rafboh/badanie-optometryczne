from flask import Flask, render_template, request, jsonify, redirect, Response
import sqlite3, json, os
from datetime import datetime

app = Flask(__name__)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'optometry.db')

def get_db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = get_db()
    c.execute('''CREATE TABLE IF NOT EXISTS exams (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT DEFAULT '',
        exam_date    TEXT DEFAULT '',
        optometrist  TEXT DEFAULT '',
        data         TEXT DEFAULT '{}',
        created_at   TEXT DEFAULT '',
        updated_at   TEXT DEFAULT ''
    )''')
    c.commit(); c.close()

def now_str():
    return datetime.now().strftime('%d.%m.%Y %H:%M')

@app.context_processor
def utility():
    def has_any(d, *args):
        """Accept keys as individual strings, a list, or mixed."""
        keys = []
        for a in args:
            if isinstance(a, (list, tuple)):
                keys.extend(a)
            else:
                keys.append(a)
        return any(str(d.get(k) or '').strip() for k in keys)

    def has_prefix(d, prefix):
        return any(str(v or '').strip() for k, v in d.items() if k.startswith(prefix))

    return dict(has_any=has_any, has_prefix=has_prefix)

# ── Generator raportu tekstowego ─────────────────────────────────────────────
def fmt_text(data, exam):
    out = []
    W = 76

    def hr(c='='): out.append(c * W)
    def blank(): out.append('')
    def sec(title):
        blank(); hr('-')
        out.append(title.upper()); hr('-')
    def sub(title):
        blank()
        out.append(f'  {title}')
        out.append('  ' + '·' * (len(title) + 2))
    def fld(label, *vals, unit=''):
        parts = [str(v).strip() for v in vals if str(v or '').strip()]
        if parts:
            v = '  '.join(parts) + (f' {unit}' if unit else '')
            out.append(f'  {label:<38}: {v}')
    def txt(label, value):
        v = str(value or '').strip()
        if not v: return
        if label: out.append(f'  {label}:')
        for ln in v.splitlines():
            out.append(f'    {ln}')

    def d(k): return str(data.get(k) or '').strip()
    def has(*keys): return any(str(data.get(k) or '').strip() for k in keys)

    # ── Nagłówek ──────────────────────────────────────────────────────────────
    hr()
    out.append('ARKUSZ BADANIA OPTOMETRYCZNEGO')
    out.append('Refrakcja oraz ocena jakości widzenia')
    out.append('Standard Badania Optometrycznego PTOO (aktualizacja 2025)')
    hr()
    blank()
    fld('Nr karty / ID', d('card_id'))
    fld('Data badania',  d('exam_date'))
    fld('Optometrysta',  d('optometrist'))
    fld('Wygenerowano',  exam.get('updated_at', ''))

    # ── Sekcja 1 ──────────────────────────────────────────────────────────────
    sec('1. Dane osobowe pacjenta')
    fld('Imię i nazwisko',        d('patient_name'))
    fld('PESEL / data urodzenia', d('pesel'))
    fld('Telefon / e-mail',       d('phone_email'))
    fld('Zawód / praca wzrokowa', d('occupation'))

    # ── Sekcja 2 ──────────────────────────────────────────────────────────────
    s2 = has('main_complaint','correction_type','last_exam_date','correction_comfort',
              'usage_hours','general_diseases','medications','allergies',
              'eye_diseases','family_history','screen_hours')
    if s2:
        sec('2. Wywiad')
        if has('main_complaint'):
            sub('2.1. Skarga główna')
            txt('', d('main_complaint'))
        if has('correction_type','last_exam_date','correction_comfort','usage_hours'):
            sub('2.2. Dotychczasowa korekcja')
            fld('Rodzaj korekcji',         d('correction_type'))
            fld('Data ostatniego badania', d('last_exam_date'))
            fld('Komfort korekcji',        d('correction_comfort'))
            fld('Czas użytkowania',        d('usage_hours'), unit='h/dobę')
        if has('general_diseases','medications','allergies','eye_diseases',
               'family_history','screen_hours'):
            sub('2.3. Wywiad ogólny i okulistyczny')
            fld('Choroby ogólne',          d('general_diseases'))
            fld('Przyjmowane leki',        d('medications'))
            fld('Alergie',                 d('allergies'))
            fld('Choroby / urazy oczu',    d('eye_diseases'))
            fld('Wywiad rodzinny (oczy)',   d('family_history'))
            fld('Praca przy ekranie',      d('screen_hours'), unit='h/dobę')

    # ── Sekcja 3 ──────────────────────────────────────────────────────────────
    VA  = ['va_op_far_nc','va_op_far_c','va_op_near_nc','va_op_near_c',
           'va_ol_far_nc','va_ol_far_c','va_ol_near_nc','va_ol_near_c',
           'va_ou_far_nc','va_ou_far_c','va_ou_near_nc','va_ou_near_c']
    BIN = ['stereo_test','stereo_result','binocular_far_method','binocular_far_result',
           'binocular_near_method','binocular_near_result']
    PRE = ['dominant_eye_far','dominant_eye_near','eye_mov_versions','eye_mov_ductions',
           'visual_field','amsler_op','amsler_ol','ppa_op','ppa_ol',
           'ppk_break','ppk_recovery','color_test','color_result',
           'iop_op','iop_ol','iop_method']
    if has(*VA, *BIN, *PRE):
        sec('3. Badania wstępne')
        if has(*VA):
            sub('3.1. Ostrość wzroku (VA)')
            COL = f"  {'Oko':<8}{'Dal bk':^12}{'Dal ck':^12}{'Bliż bk':^12}{'Bliż ck':^12}"
            out.append(COL); out.append('  ' + '─'*56)
            for eye, p in [('OP','va_op'),('OL','va_ol'),('OPL','va_ou')]:
                out.append(f"  {eye:<8}{d(p+'_far_nc') or '—':^12}{d(p+'_far_c') or '—':^12}"
                           f"{d(p+'_near_nc') or '—':^12}{d(p+'_near_c') or '—':^12}")
        if has(*BIN):
            sub('3.2. Widzenie obuoczne – wstępne')
            if has('stereo_test','stereo_result'):
                arc = f"{d('stereo_result')}\" arc" if d('stereo_result') else ''
                fld('Stereoskopia', d('stereo_test'), arc)
            if has('binocular_far_method','binocular_far_result'):
                fld('Forie/tropie – dal', d('binocular_far_method'), d('binocular_far_result'))
            if has('binocular_near_method','binocular_near_result'):
                fld('Forie/tropie – bliż', d('binocular_near_method'), d('binocular_near_result'))
        if has(*PRE):
            sub('3.3–3.10. Pozostałe badania wstępne')
            if has('dominant_eye_far','dominant_eye_near'):
                fld('3.3. Oko dominujące',
                    f"Dal: {d('dominant_eye_far') or '—'}  Bliż: {d('dominant_eye_near') or '—'}")
            if has('eye_mov_versions','eye_mov_ductions'):
                fld('3.4. Ruchy oczu',
                    f"Wersje: {d('eye_mov_versions')}  Dukcje: {d('eye_mov_ductions')}")
            if has('visual_field'):
                fld('3.5. Pole widzenia', d('visual_field'))
            if has('amsler_op','amsler_ol'):
                fld('3.6. Test Amslera',
                    f"OP: {d('amsler_op') or '—'}  OL: {d('amsler_ol') or '—'}")
            if has('ppa_op','ppa_ol'):
                fld('3.7. PPA',
                    f"OP: {d('ppa_op') or '—'} cm  OL: {d('ppa_ol') or '—'} cm")
            if has('ppk_break','ppk_recovery'):
                fld('3.8. PPK',
                    f"Break: {d('ppk_break') or '—'} cm  Rec.: {d('ppk_recovery') or '—'} cm")
            if has('color_test','color_result'):
                fld('3.9. Widzenie barw', d('color_test'), d('color_result'))
            if has('iop_op','iop_ol'):
                met = f" ({d('iop_method')})" if d('iop_method') else ''
                fld('3.10. IOP',
                    f"OP: {d('iop_op') or '—'} mmHg  OL: {d('iop_ol') or '—'} mmHg{met}")

    # ── Sekcja 4 ──────────────────────────────────────────────────────────────
    def refr_tbl(title, prefix):
        keys = [prefix+s for s in ['_op_sph','_op_cyl','_ol_sph','_ol_cyl']]
        if not has(*keys): return
        sub(title)
        H = f"  {'Oko':<6}{'Sph':>9}{'Cyl':>9}{'Axis':>7}{'Add':>7}{'Pryzmat':>13}{'PD':>7}"
        out.append(H); out.append('  ' + '─'*58)
        for eye, ep in [('OP', prefix+'_op'), ('OL', prefix+'_ol')]:
            out.append(f"  {eye:<6}{d(ep+'_sph') or '—':>9}{d(ep+'_cyl') or '—':>9}"
                       f"{d(ep+'_axis') or '—':>7}{d(ep+'_add') or '—':>7}"
                       f"{d(ep+'_prism') or '—':>13}{d(ep+'_pd') or '—':>7}")

    FOF     = ['fof_op_sph','fof_op_cyl','fof_ol_sph','fof_ol_cyl']
    AUTO    = ['auto_op_sph','auto_op_cyl','auto_ol_sph','auto_ol_cyl']
    KER     = ['ker_op_k1','ker_op_k2','ker_ol_k1','ker_ol_k2']
    OBJ_VA  = ['obj_va_op_far','obj_va_op_near','obj_va_ol_far',
               'obj_va_ol_near','obj_va_ou_far','obj_va_ou_near']
    if has(*FOF, *AUTO, *KER, *OBJ_VA):
        sec('4. Refrakcja przedmiotowa (obiektywna)')
        refr_tbl('4.0. Frontofokometria', 'fof')
        if has(*AUTO):
            sub('4.1. Autorefraktometria / skiaskopia')
            H = f"  {'Oko':<6}{'Sph':>9}{'Cyl':>9}{'Axis':>7}{'Metoda':<18}{'Cykloplegia':<14}"
            out.append(H); out.append('  ' + '─'*66)
            for eye, ep in [('OP','auto_op'),('OL','auto_ol')]:
                out.append(f"  {eye:<6}{d(ep+'_sph') or '—':>9}{d(ep+'_cyl') or '—':>9}"
                           f"{d(ep+'_axis') or '—':>7}{d(ep+'_method') or '—':<18}{d(ep+'_cyclo') or '—':<14}")
        if has(*KER):
            sub('4.2. Keratometria')
            H = f"  {'Oko':<6}{'K1':<22}{'K2':<22}{'ΔK':>8}"
            out.append(H); out.append('  ' + '─'*60)
            for eye, ep in [('OP','ker_op'),('OL','ker_ol')]:
                out.append(f"  {eye:<6}{d(ep+'_k1') or '—':<22}{d(ep+'_k2') or '—':<22}{d(ep+'_dk') or '—':>8}")
        if has(*OBJ_VA):
            sub('4.3. Ostrość wzroku z korekcją przedmiotową')
            H = f"  {'Oko':<10}{'Dal z kor. obj.':^18}{'Bliż z kor. obj.':^18}{'Uwagi'}"
            out.append(H); out.append('  ' + '─'*60)
            for eye, pfx in [('OP (OD)','obj_va_op'),('OL (OS)','obj_va_ol'),('OPL (OU)','obj_va_ou')]:
                far   = d(pfx+'_far')   or '—'
                near  = d(pfx+'_near')  or '—'
                notes = d(pfx+'_notes') or ''
                if far != '—' or near != '—' or notes:
                    out.append(f"  {eye:<10}{far:^18}{near:^18}{notes}")

    # ── Sekcja 5 ──────────────────────────────────────────────────────────────
    SUBJ    = ['subj_op_sph','subj_op_cyl','subj_op_axis','subj_ol_sph','subj_ol_cyl']
    BBAL    = ['binocular_balance','mpmva_op','mpmva_ol']
    FBIN    = ['far_bino_method','far_bino_result','phoria_far_h','verg_bo_pos','verg_bi_pos']
    SUBJ_VA = ['subj_va_op_far','subj_va_ol_far','subj_va_ou_far',
               'subj_va_op_near','subj_va_ol_near','subj_va_ou_near']
    if has(*SUBJ, *BBAL, *FBIN, *SUBJ_VA):
        sec('5. Refrakcja podmiotowa (subiektywna) – dal')
        if has(*SUBJ):
            sub('5.1–5.2. Monokularna refrakcja podmiotowa')
            H = f"  {'Oko':<6}{'Sph':>9}{'Cyl':>9}{'Axis':>7}{'VA':>8}"
            out.append(H); out.append('  ' + '─'*42)
            for eye, ep in [('OP','subj_op'),('OL','subj_ol')]:
                out.append(f"  {eye:<6}{d(ep+'_sph') or '—':>9}{d(ep+'_cyl') or '—':>9}"
                           f"{d(ep+'_axis') or '—':>7}{d(ep+'_va') or '—':>8}")
        if has(*BBAL):
            sub('5.3. Refrakcja obuoczna')
            fld('Metoda równoważenia', d('binocular_balance'))
            if has('mpmva_op','mpmva_ol'):
                fld('MPMVA', f"OP: {d('mpmva_op') or '—'} D  OL: {d('mpmva_ol') or '—'} D")
        if has(*SUBJ_VA):
            sub('5.5. Ostrość wzroku z korekcją podmiotową')
            COL = f"  {'Oko':<10}{'Dal z kor. subj.':^20}{'Bliż z kor. subj.':^20}"
            out.append(COL); out.append('  ' + '─'*50)
            for eye, pfx in [('OP (OD)','subj_va_op'),('OL (OS)','subj_va_ol'),('OPL (OU)','subj_va_ou')]:
                far  = d(pfx+'_far')  or '—'
                near = d(pfx+'_near') or '—'
                if far != '—' or near != '—':
                    out.append(f"  {eye:<10}{far:^20}{near:^20}")
        if has(*FBIN):
            sub('5.4. Widzenie obuoczne w korekcji dal')
            if has('far_bino_method','far_bino_result'):
                fld('Forie/tropie', d('far_bino_method'), d('far_bino_result'))
            if has('phoria_far_h','phoria_far_v'):
                fld('Forie (Δ)', f"Horyz.: {d('phoria_far_h') or '—'}  Wert.: {d('phoria_far_v') or '—'}")
            if has('verg_bo_pos','verg_bo_blur','verg_bo_break'):
                fld('Wergencje BO',
                    f"{d('verg_bo_pos') or '—'}/{d('verg_bo_blur') or '—'}/{d('verg_bo_break') or '—'} Δ")
            if has('verg_bi_pos','verg_bi_blur','verg_bi_break'):
                fld('Wergencje BI',
                    f"{d('verg_bi_pos') or '—'}/{d('verg_bi_blur') or '—'}/{d('verg_bi_break') or '—'} Δ")

    # ── Sekcja 6 ──────────────────────────────────────────────────────────────
    ACC  = ['amp_acc_op','amp_acc_ol','add_preliminary','add_range_from']
    NBIN = ['near_bino_method','phoria_near_h','aca_ratio','near_verg_bo']
    AFAC = ['acc_facility_mono','acc_facility_bino','acc_response_op','final_add']
    if has(*ACC, *NBIN, *AFAC):
        sec('6. Widzenie bliskie')
        if has(*ACC):
            sub('6.1–6.3. Akomodacja i dodatek')
            if has('amp_acc_op','amp_acc_ol'):
                fld('6.1. Amplituda akomodacji',
                    f"OP: {d('amp_acc_op') or '—'} D  OL: {d('amp_acc_ol') or '—'} D  ({d('amp_acc_method')})")
            if has('add_preliminary'):
                fld('6.2. Wstępny Add',
                    f"+{d('add_preliminary')} D  odl.: {d('add_working_dist') or '—'} cm")
            if has('add_range_from','add_range_to'):
                fld('6.3. Zakres ostrego widzenia',
                    f"{d('add_range_from') or '—'} – {d('add_range_to') or '—'} cm")
        if has(*NBIN):
            sub('6.4. Widzenie obuoczne z bliska')
            if has('near_bino_method','near_bino_result'):
                fld('Forie/tropie', d('near_bino_method'), d('near_bino_result'))
            if has('phoria_near_h','phoria_near_v'):
                fld('Forie (Δ)', f"Horyz.: {d('phoria_near_h') or '—'}  Wert.: {d('phoria_near_v') or '—'}")
            if has('aca_ratio'):
                fld('AC/A', d('aca_ratio'), unit='Δ/D')
            if has('near_verg_bo','near_verg_bi'):
                fld('Wergencje BO/BI',
                    f"BO: {d('near_verg_bo') or '—'}  BI: {d('near_verg_bi') or '—'}")
        if has(*AFAC):
            sub('6.5–6.7. Sprawność i odpowiedź akomodacji')
            if has('acc_facility_mono','acc_facility_bino'):
                fld('6.5. Sprawność akomodacji',
                    f"Mono: {d('acc_facility_mono') or '—'} cpm  Bino: {d('acc_facility_bino') or '—'} cpm")
            if has('acc_response_op','acc_response_ol'):
                fld('6.6. Odpowiedź akomodacji',
                    f"OP: {d('acc_response_op') or '—'} D  OL: {d('acc_response_ol') or '—'} D"
                    f"  ({d('acc_response_method')})")
            if has('final_add'):
                fld('6.7. Ostateczny Add', f"+{d('final_add')} D")

    # ── Sekcja 7 ──────────────────────────────────────────────────────────────
    SNAMES = ['film_łzowy','powieki','spojówka_gałk','spojówka_tarck','rogówka',
              'rąbek','twardówka','tęczówka','komora','soczewka']
    SLBL   = {'film_łzowy':'Film łzowy','powieki':'Powieki/brzegi',
              'spojówka_gałk':'Spojówka gałk.','spojówka_tarck':'Spojówka tarck.',
              'rogówka':'Rogówka','rąbek':'Rąbek','twardówka':'Twardówka',
              'tęczówka':'Tęczówka','komora':'Komora prz.','soczewka':'Soczewka'}
    FNAMES = ['tarczka','arkada_g','arkada_d','plamka','obwód','ciałosz']
    FLBL   = {'tarczka':'Tarcza n.wzr. (C/D)','arkada_g':'Arkada górna',
              'arkada_d':'Arkada dolna','plamka':'Pole plamkowe',
              'obwód':'Obwód siatkówki','ciałosz':'Ciało szkliste'}

    slit_keys   = [f'slit_op_grade_{n}' for n in SNAMES] + \
                  [f'slit_ol_grade_{n}' for n in SNAMES] + \
                  [f'slit_op_desc_{n}'  for n in SNAMES] + \
                  [f'slit_ol_desc_{n}'  for n in SNAMES]
    fundus_keys = [f'fundus_op_{n}' for n in FNAMES] + \
                  [f'fundus_ol_{n}' for n in FNAMES] + ['fundus_notes']

    if has(*slit_keys, *fundus_keys):
        sec('7. Badanie w lampie szczelinowej')
        if has(*slit_keys):
            sub('7.1. Przedni odcinek oka')
            H = f"  {'Element':<24}{'OP-st':>6}{'OL-st':>6}  {'OP – opis':<20}{'OL – opis':<20}"
            out.append(H); out.append('  ' + '─'*78)
            for key in SNAMES:
                og = d(f'slit_op_grade_{key}'); olg = d(f'slit_ol_grade_{key}')
                od = d(f'slit_op_desc_{key}');  old = d(f'slit_ol_desc_{key}')
                if og or olg or od or old:
                    out.append(f"  {SLBL[key]:<24}{og or '—':>6}{olg or '—':>6}  "
                               f"{od or '':<20}{old or '':<20}")
        if has(*fundus_keys):
            sub('7.2. Tylny odcinek oka')
            H = f"  {'Element':<26}{'OP':<26}{'OL':<26}"
            out.append(H); out.append('  ' + '─'*78)
            for key in FNAMES:
                op_v = d(f'fundus_op_{key}'); ol_v = d(f'fundus_ol_{key}')
                if op_v or ol_v:
                    out.append(f"  {FLBL[key]:<26}{op_v or '—':<26}{ol_v or '—':<26}")
            if d('fundus_notes'):
                out.append(f"  Uwagi: {d('fundus_notes')}")

    # ── Sekcja 8 ──────────────────────────────────────────────────────────────
    CS  = ['cs_op','cs_ol','glare_op','glare_ol','hoa_op','hoa_ol','pupil_op','pupil_ol']
    VAS = ['vas_far','vas_near','vas_day','vas_eve','vas_night','vas_3d','vas_aste','vas_total']
    if has(*CS, *VAS):
        sec('8. Ocena jakości widzenia')
        if has(*CS):
            sub('8.1. Wrażliwość na kontrast i jakość obrazu')
            for param, ok, ol in [
                ('Wrażliwość na kontrast','cs_op','cs_ol'),
                ('Olśnienie / zmierzch','glare_op','glare_ol'),
                ('HOA / RMS','hoa_op','hoa_ol'),
                ('Średnica źrenicy','pupil_op','pupil_ol')
            ]:
                if has(ok, ol):
                    fld(param, f"OP: {d(ok) or '—'}  OL: {d(ol) or '—'}")
        if has(*VAS):
            sub('8.2. Subiektywna ocena widzenia (0–10)')
            VAS_LBLS = [
                ('vas_far','Ostrość – dal'),       ('vas_near','Ostrość – bliż'),
                ('vas_day','Komfort – dzień'),      ('vas_eve','Komfort – wieczór'),
                ('vas_night','Widzenie zmierzchowe'),('vas_3d','Głębia (3D)'),
                ('vas_aste','Brak zmęczenia'),      ('vas_total','Satysfakcja ogólna')
            ]
            for key, label in VAS_LBLS:
                v = d(key)
                if v:
                    out.append(f"  {label:<32}: {v} / 10")

    # ── Sekcja 9 ──────────────────────────────────────────────────────────────
    FIN = ['final_op_sph','final_op_cyl','final_ol_sph','final_ol_cyl']
    REC = ['referral','vision_therapy','hygiene_advice',
           'followup_date','followup_text','additional_notes']
    if has('diagnosis', *FIN, 'lens_type', *REC):
        sec('9. Diagnoza optometryczna i zalecenia')
        if has('diagnosis'):
            sub('9.1. Rozpoznanie optometryczne')
            txt('', d('diagnosis'))
        if has(*FIN):
            sub('9.2. Końcowa zalecana korekcja okularowa')
            H = f"  {'Oko':<6}{'Sph':>9}{'Cyl':>9}{'Axis':>7}{'Add':>7}{'Pryzmat':>13}{'PD':>7}"
            out.append(H); out.append('  ' + '─'*58)
            for eye, ep in [('OP','final_op'),('OL','final_ol')]:
                out.append(f"  {eye:<6}{d(ep+'_sph') or '—':>9}{d(ep+'_cyl') or '—':>9}"
                           f"{d(ep+'_axis') or '—':>7}{d(ep+'_add') or '—':>7}"
                           f"{d(ep+'_prism') or '—':>13}{d(ep+'_pd') or '—':>7}")
            fld('Typ soczewek',   d('lens_type'))
            fld('Powłoki/filtry', d('lens_coatings'))
        if has(*REC):
            sub('9.3. Zalecenia i dalsze postępowanie')
            ref = d('referral')
            if ref:
                reason = d('referral_reason')
                fld('Skierowanie', ref, f"– {reason}" if reason else '')
            fld('Ćwiczenia wzrokowe', d('vision_therapy'))
            txt('Higiena / ergonomia', d('hygiene_advice'))
            fc = d('followup_date') or d('followup_text')
            if fc:
                fld('Termin kontroli', fc)
            txt('Uwagi dodatkowe', d('additional_notes'))

    # ── Stopka ────────────────────────────────────────────────────────────────
    blank(); hr()
    out.append('Podstawa: Standard Badania Optometrycznego PTOO (aktualizacja 2025).')
    out.append('Zakres badania dostosowany do indywidualnych potrzeb pacjenta.')
    hr()
    return '\n'.join(out)

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    c = get_db()
    if q:
        rows = c.execute(
            "SELECT id,patient_name,exam_date,optometrist,updated_at FROM exams "
            "WHERE patient_name LIKE ? ORDER BY updated_at DESC",
            ('%' + q + '%',)
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT id,patient_name,exam_date,optometrist,updated_at "
            "FROM exams ORDER BY updated_at DESC LIMIT 200"
        ).fetchall()
    c.close()
    return render_template('index.html', exams=rows, q=q)

@app.route('/new')
def new_exam():
    return render_template('form.html', exam_id=0, init_data='{}')

@app.route('/exam/<int:eid>')
def edit_exam(eid):
    c = get_db()
    row = c.execute('SELECT * FROM exams WHERE id=?', (eid,)).fetchone()
    c.close()
    if not row:
        return redirect('/')
    return render_template('form.html', exam_id=eid, init_data=row['data'])

@app.route('/api/save', methods=['POST'])
def api_save():
    fd = request.get_json(force=True) or {}
    eid = fd.pop('__id', 0)
    patient_name = fd.get('patient_name', '')
    exam_date    = fd.get('exam_date', '')
    optometrist  = fd.get('optometrist', '')
    data_str = json.dumps(fd, ensure_ascii=False)
    now = now_str()
    c = get_db()
    if eid:
        c.execute(
            'UPDATE exams SET patient_name=?,exam_date=?,optometrist=?,data=?,updated_at=? WHERE id=?',
            (patient_name, exam_date, optometrist, data_str, now, eid)
        )
    else:
        cur = c.execute(
            'INSERT INTO exams(patient_name,exam_date,optometrist,data,created_at,updated_at) VALUES(?,?,?,?,?,?)',
            (patient_name, exam_date, optometrist, data_str, now, now)
        )
        eid = cur.lastrowid
    c.commit(); c.close()
    return jsonify({'ok': True, 'id': eid})

@app.route('/report/<int:eid>')
def report(eid):
    c = get_db()
    row = c.execute('SELECT * FROM exams WHERE id=?', (eid,)).fetchone()
    c.close()
    if not row:
        return redirect('/')
    data = json.loads(row['data'])
    return render_template('report.html', exam=dict(row), data=data)

@app.route('/text/<int:eid>')
def text_export(eid):
    c = get_db()
    row = c.execute('SELECT * FROM exams WHERE id=?', (eid,)).fetchone()
    c.close()
    if not row:
        return redirect('/')
    data = json.loads(row['data'])
    txt = fmt_text(data, dict(row))
    patient = (data.get('patient_name') or f'badanie_{eid}').replace(' ', '_')
    filename = f"badanie_{patient}.txt"
    return Response(
        txt,
        mimetype='text/plain; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@app.route('/delete/<int:eid>', methods=['POST'])
def delete_exam(eid):
    c = get_db()
    c.execute('DELETE FROM exams WHERE id=?', (eid,))
    c.commit(); c.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    print('\n  Aplikacja Optometryczna')
    print('  Otwórz Chrome: http://localhost:5000\n')
    app.run(debug=False, port=5000, host='127.0.0.1')
