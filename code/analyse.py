"""Régénère les statistiques du classeur « Pharmacie_Analyse 2 » à partir des quatre exports CSV.
Contrôle au passage que l'onglet Historique du classeur est identique à l'export journalier.
Sortie : results.json (chiffres de la note et des présentations).
Usage : python analyse.py <dossier rush-2> <Pharmacie_Analyse 2.xlsx> <grippe Sentinelles .csv> <dossier sortie>"""
import sys, json
import numpy as np, pandas as pd
import openpyxl

CSV_DIR, WB, FLU, OUT = sys.argv[1:5]
ATC = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']
R = {}

# ---------- 1. Lecture des exports (dates au format mois/jour/année) ----------
daily = pd.read_csv(f'{CSV_DIR}/Pharma_Ventes_Daily.csv')
daily['date'] = pd.to_datetime(daily['datum'], format='%m/%d/%Y')
daily = daily[['date'] + ATC].set_index('date').astype(float)   # colonne « Hour » de l'export journalier écartée
hourly = pd.read_csv(f'{CSV_DIR}/Pharma_Ventes_Hourly.csv')
hourly['dt'] = pd.to_datetime(hourly['datum'], format='%m/%d/%Y %H:%M')
weekly = pd.read_csv(f'{CSV_DIR}/Pharma_Ventes_Weekly.csv'); weekly['date'] = pd.to_datetime(weekly['datum'], format='%m/%d/%Y')
monthly = pd.read_csv(f'{CSV_DIR}/Pharma_Ventes_Monthly.csv'); monthly['date'] = pd.to_datetime(monthly['datum'])

# ---------- 2. Contrôle du classeur Pharmacie_Analyse 2 ----------
wb = openpyxl.load_workbook(WB, data_only=True, read_only=True)
rows = list(wb['Historique'].values)
hist = pd.DataFrame(rows[1:], columns=rows[0]).dropna(subset=['Date'])
hist['Date'] = pd.to_datetime(hist['Date'])
hist = hist.set_index('Date')[ATC].apply(pd.to_numeric, errors='coerce')
R['wb_hist_rows'] = len(hist)
R['wb_hist_nulls'] = int(hist.isna().sum().sum())
R['wb_hist_maxdiff_vs_export'] = float((hist - daily.loc[hist.index]).abs().max().max())
R['wb_sheets'] = wb.sheetnames

R['period'] = [str(daily.index.min().date()), str(daily.index.max().date())]
R['n_days'] = len(daily)
full_range = pd.date_range(daily.index.min(), daily.index.max())
R['missing_days'] = int(len(full_range) - len(daily))
R['neg_values'] = int((daily < 0).sum().sum())
R['nan_values'] = int(daily.isna().sum().sum())

# Contrôles croisés
h2d = hourly.groupby(hourly['dt'].dt.normalize())[ATC].sum()
common = h2d.index.intersection(daily.index)
R['chk_hourly_vs_daily_maxdiff'] = float((h2d.loc[common] - daily.loc[common]).abs().max().max())
R['chk_hourly_days'] = len(h2d)
d2w = daily.resample('W-SUN').sum()
wk = weekly.set_index('date')[ATC]
cw = d2w.index.intersection(wk.index)
R['chk_daily_vs_weekly_maxdiff'] = float((d2w.loc[cw] - wk.loc[cw]).abs().max().max())
d2m = daily.resample('ME').sum()
mo = monthly.set_index('date')[ATC]
cm = d2m.index.intersection(mo.index)
diff = (d2m.loc[cm] - mo.loc[cm])
bad = (diff.abs() > 0.01)
R['chk_monthly_cells_diff'] = int(bad.sum().sum()); R['chk_monthly_cells'] = int(bad.size)
R['chk_monthly_rel_gap'] = float(diff.sum().sum() / mo.loc[cm].sum().sum())
R['chk_monthly_months_with_gap'] = sorted({str(i.date())[:7] for i in bad.index[bad.any(axis=1)]})
oct14 = (d2m.loc['2014-10-31'] / mo.loc['2014-10-31'] - 1)
R['oct2014_gap'] = {c: round(float(oct14[c]) * 100, 1) for c in ATC}

# Mois complets uniquement (janv 2014 commence le 2, oct 2019 tronqué)
m = d2m.copy()
ndays = daily.resample('ME').size()
m = m[(m.index > '2014-01-31') & (m.index < '2019-10-31')]
ndays = ndays.loc[m.index]
R['complete_months'] = [str(m.index.min().date())[:7], str(m.index.max().date())[:7], len(m)]

# ---------- 3. Statistiques descriptives ----------
d = daily[(daily.index >= '2014-02-01') & (daily.index <= '2019-09-30')]
stats = {}
tot = d.sum().sum()
for c in ATC:
    s = d[c]
    stats[c] = dict(total=round(s.sum(), 1), share=round(s.sum() / tot * 100, 1), mean=round(s.mean(), 2),
                    median=round(s.median(), 2), std=round(s.std(), 2), cv=round(s.std() / s.mean(), 2),
                    p95=round(s.quantile(.95), 1), max=round(s.max(), 1),
                    zero_days=int((s == 0).sum()), zero_pct=round((s == 0).mean() * 100, 1))
R['stats'] = stats
# Saisonnalité : indice mensuel (moyenne/jour du mois calendaire ÷ moyenne globale)
dm = d.groupby(d.index.month).mean()
R['season_index'] = {c: [round(v, 2) for v in (dm[c] / d[c].mean()).tolist()] for c in ATC}
# Jour de semaine
wd = d.groupby(d.index.dayofweek).mean()
R['weekday_index'] = {c: [round(v, 2) for v in (wd[c] / d[c].mean()).tolist()] for c in ATC}
R['weekday_total'] = [round(v, 1) for v in d.sum(axis=1).groupby(d.index.dayofweek).mean().tolist()]
# Heures
hh = hourly[(hourly['dt'] >= '2014-02-01') & (hourly['dt'] < '2019-10-01')].copy()
hh['h'] = hh['dt'].dt.hour
hp = hh.groupby('h')[ATC].sum()
R['hour_share_total'] = {int(k): round(v, 2) for k, v in (hp.sum(axis=1) / hp.sum().sum() * 100).items()}
R['hour_share_N05'] = {int(k): round(v, 2) for k, v in ((hp['N05B'] + hp['N05C']) / (hp['N05B'] + hp['N05C']).sum() * 100).items()}
# Années (moyenne/jour)
yr = daily[(daily.index >= '2014-02-01') & (daily.index <= '2019-09-30')].groupby(lambda x: x.year).mean()
R['year_mean_per_day'] = {c: {int(y): round(v, 2) for y, v in yr[c].items()} for c in ATC}
R['year_total_per_day'] = {int(y): round(v, 1) for y, v in yr.sum(axis=1).items()}
# Granularité / risque ré-identification
hz = hh[['N05B', 'N05C']]
R['hourly_rows_N05C_eq_1'] = int((hh['N05C'] > 0).sum())
R['hourly_rows_N05C_nonzero_pct'] = round((hh['N05C'] > 0).mean() * 100, 1)
R['hourly_N05C_rows_le2'] = round(((hh['N05C'] > 0) & (hh['N05C'] <= 2)).sum() / max((hh['N05C'] > 0).sum(), 1) * 100, 1)
R['hourly_N05B_rows_le2'] = round(((hh['N05B'] > 0) & (hh['N05B'] <= 2)).sum() / max((hh['N05B'] > 0).sum(), 1) * 100, 1)
R['daily_N05C_le2_pct'] = round(((d['N05C'] > 0) & (d['N05C'] <= 2)).sum() / max((d['N05C'] > 0).sum(), 1) * 100, 1)
wN = d['N05C'].resample('W-SUN').sum(); wN = wN[wN > 0]
R['weekly_N05C_le2_pct'] = round(float((wN <= 2).mean() * 100), 1)
R['monthly_N05C_le2_pct'] = round(float(((m['N05C'] > 0) & (m['N05C'] <= 2)).sum() / (m['N05C'] > 0).sum() * 100), 1)
R['hourly_N05B_nonzero_pct'] = round((hh['N05B'] > 0).mean() * 100, 1)
R['monthly_N05C_min'] = float(m['N05C'].min()); R['monthly_N05C_mean'] = round(float(m['N05C'].mean()), 1)
R['non_integer_share'] = {c: round(float(((d[c] % 1).abs() > 1e-6).mean() * 100), 1) for c in ATC}

# ---------- 4. Test de prévision (origine glissante) ----------
# Cible : volume du mois t+1. Chaque prévision n'utilise que les mois antérieurs.
# Test principal sur les 24 derniers mois complets (oct. 2017 -> sept. 2019),
# test de robustesse sur 33 mois (janv. 2017 -> sept. 2019).
def fc_naive(hist, nd_hist, nd_next):
    return hist[-1] / nd_hist[-1] * nd_next
def fc_snaive(hist, nd_hist, nd_next):
    return hist[-12] / nd_hist[-12] * nd_next
def fc_ma3(hist, nd_hist, nd_next):
    return np.sum(hist[-3:]) / np.sum(nd_hist[-3:]) * nd_next
def fc_seas_level(hist, nd_hist, nd_next):
    # niveau = moyenne/jour des 12 derniers mois ; saisonnalité = indice moyen du même mois calendaire
    # les années précédentes (valeur du mois / moyenne des 12 mois centrés, sans regarder le futur)
    rate = np.array(hist) / np.array(nd_hist); t = len(rate)
    level = rate[-12:].mean()
    si = []
    for k in range(t - 12, -1, -12):
        lo, hi = k - 6, k + 6
        if lo >= 0 and hi <= t:
            si.append(rate[k] / rate[lo:hi].mean())
    return level * (np.mean(si) if si else 1.0) * nd_next
def fc_stocks_trend(hist, nd_hist, nd_next):
    # logique de l'onglet Stocks : droite sur les ventes/jour du même mois les années passées, prolongée d'un an
    rate = np.array(hist) / np.array(nd_hist); t = len(rate)
    ks = list(range(t - 12, -1, -12))[::-1]
    if len(ks) < 2: return rate[-12] * nd_next
    a_, b_ = np.polyfit(ks, rate[ks], 1)
    return max(0.0, a_ * t + b_) * nd_next
METHODS = {'Naïf (mois précédent)': fc_naive, 'Saisonnier naïf (même mois N-1)': fc_snaive,
           'Moyenne 3 mois': fc_ma3, 'Niveau 12 mois × saisonnalité': fc_seas_level}
vals = m.values; nd = ndays.values.astype(float); idxs = m.index

def backtest(TEST):
    out = {}
    allm = dict(METHODS, **{'Tendance onglet Stocks': fc_stocks_trend})
    for j, c in enumerate(ATC):
        y = vals[:, j]
        errs = {k: [] for k in allm}; act = []
        for t in range(len(y) - TEST, len(y)):
            hist, ndh = list(y[:t]), list(nd[:t])
            act.append(y[t])
            for k, f in allm.items():
                errs[k].append(f(hist, ndh, nd[t]) - y[t])
        act = np.array(act)
        res = {k: dict(mae=round(float(np.abs(np.array(e)).mean()), 1),
                       mape=round(float(np.mean(np.abs(np.array(e)) / act) * 100), 1)) for k, e in errs.items()}
        base = res['Naïf (mois précédent)']['mae']
        best = min(METHODS, key=lambda k: res[k]['mae'])          # la tendance Stocks est mesurée, pas candidate
        out[c] = dict(methods=res, best=best, gain_vs_naive=round((1 - res[best]['mae'] / base) * 100, 1),
                      mean_month=round(float(act.mean()), 1))
    return out

fc_res = backtest(24); fc33 = backtest(33)
R['forecast_test_window'] = [str(idxs[-24].date())[:7], str(idxs[-1].date())[:7]]
R['forecast_test_window_33'] = [str(idxs[-33].date())[:7], str(idxs[-1].date())[:7]]
# Verdict : la meilleure méthode doit battre la prévision naïve sur les DEUX périodes de test
for c in ATC:
    f24, f33 = fc_res[c], fc33[c]
    b = f24['methods'][f24['best']]
    robust = f24['gain_vs_naive'] > 0 and f33['gain_vs_naive'] > 0
    if robust and b['mape'] < 15: v = 'Oui'
    elif robust and b['mape'] < 25: v = 'Partiellement'
    elif f24['methods']['Naïf (mois précédent)']['mape'] < 15: v = 'Naïf suffisant'
    else: v = 'Non'
    f24['verdict'] = v
    f24['gain_vs_naive_33'] = f33['gain_vs_naive']; f24['best_33'] = f33['best']
    f24['mape_best_33'] = f33['methods'][f33['best']]['mape']
    f24['stocks_trend_mape'] = f24['methods']['Tendance onglet Stocks']['mape']
    f24['stocks_trend_mape_33'] = f33['methods']['Tendance onglet Stocks']['mape']
    f24['naive_mape_33'] = f33['methods']['Naïf (mois précédent)']['mape']
R['forecast'] = fc_res
vol = {c: S_ for c, S_ in zip(ATC, m.sum().values)}
R['forecast_share_oui'] = round(sum(vol[c] for c in ATC if fc_res[c]['verdict'] == 'Oui') / sum(vol.values()) * 100, 1)
R['forecast_share_oui_partiel'] = round(sum(vol[c] for c in ATC if fc_res[c]['verdict'] in ('Oui', 'Partiellement')) / sum(vol.values()) * 100, 1)
# Prévision opérationnelle oct. 2019 (historique complet) : méthode retenue, ou mois précédent si elle ne bat pas le naïf
for j, c in enumerate(ATC):
    f = METHODS[fc_res[c]['best']] if fc_res[c]['verdict'] in ('Oui', 'Partiellement') else fc_naive
    fc_res[c]['oct2019_forecast'] = round(float(f(list(vals[:, j]), list(nd), 31)), 0)
    fc_res[c]['oct2018_actual'] = round(float(d2m.loc['2018-10-31', c]), 0)

# ---------- 5. Donnée externe : grippe (Réseau Sentinelles) ----------
flu = pd.read_csv(FLU, comment='#')
flu['monday'] = pd.to_datetime(flu['week'].astype(str) + '1', format='%G%V%u')
flu = pd.to_numeric(flu.set_index('monday')['inc100'], errors='coerce').sort_index()
wkly = daily.resample('W-MON', label='left', closed='left').sum()
wkly = wkly[(wkly.index >= '2014-01-06') & (wkly.index <= '2019-09-30')]
j = wkly.join(flu.rename('flu'), how='inner')
corr = {c: round(float(j[c].corr(j['flu'])), 2) for c in ATC}
R['flu_corr'] = corr
R['flu_weeks'] = len(j)
# Régression N02BE ~ grippe : part de variance expliquée
for c in ['N02BE', 'R03', 'M01AE']:
    r2 = j[c].corr(j['flu']) ** 2
    R.setdefault('flu_r2', {})[c] = round(float(r2) * 100, 1)
# Semaines épidémiques (inc100 > 150, ~seuil Sentinelles) vs autres
epi = j['flu'] > 150
R['flu_epi_weeks'] = int(epi.sum())
R['flu_epi_uplift'] = {c: round(float(j.loc[epi, c].mean() / j.loc[~epi, c].mean() - 1) * 100, 1) for c in ATC}
# Prévision N02BE améliorée par grippe ? (test mensuel simple)
fm = flu.resample('ME').mean()
R['flu_series_used'] = 'Sentinelles indicateur 3 (syndromes grippaux), France, incidence /100 000 hab., hebdomadaire'

json.dump(R, open(f'{OUT}/results.json', 'w'), ensure_ascii=False, indent=1, default=str)

# ---------- 6. Séries pour graphiques ----------
m.to_csv(f'{OUT}/monthly_complete.csv')
ndays.to_csv(f'{OUT}/ndays.csv')
j.to_csv(f'{OUT}/weekly_flu.csv')
hp.to_csv(f'{OUT}/hour_profile.csv')
print(json.dumps(R, ensure_ascii=False, indent=1, default=str)[:9000])
