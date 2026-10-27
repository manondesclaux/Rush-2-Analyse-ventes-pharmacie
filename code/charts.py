import sys, json
import pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = sys.argv[1]
R = json.load(open(f'{OUT}/results.json'))
INK, MUTE, GRID = '#1B2A2F', '#6B7B80', '#E3E8E6'
GREEN, MINT, CORAL, SAND, BLUE = '#0B5D4B', '#3FB68E', '#E4572E', '#C9A227', '#2F6690'
plt.rcParams.update({'font.family': 'Arial', 'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': MUTE,
                     'xtick.color': MUTE, 'ytick.color': MUTE, 'axes.spines.top': False, 'axes.spines.right': False})
MOIS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

def save(fig, name):
    fig.tight_layout(); fig.savefig(f'{OUT}/{name}.png', dpi=200); plt.close(fig)

# 1. Saisonnalité
fig, ax = plt.subplots(figsize=(7, 3.2))
for c, col in [('N02BE', GREEN), ('R03', BLUE), ('R06', SAND), ('N05B', MUTE)]:
    ax.plot(range(12), R['season_index'][c], color=col, lw=2.2 if c != 'N05B' else 1.4, label=c)
    ax.text(11.2, R['season_index'][c][11], c, color=col, va='center', fontsize=9, fontweight='bold')
ax.axhline(1, color=GRID, lw=1); ax.set_xticks(range(12)); ax.set_xticklabels(MOIS)
ax.set_ylabel('Indice (1 = mois moyen)'); ax.grid(axis='y', color=GRID); ax.set_xlim(-0.3, 12)
ax.set_title('Saisonnalité des ventes par groupe (moyenne/jour du mois ÷ moyenne annuelle)', loc='left', fontsize=10, color=INK)
save(fig, 'g_saison')

# 2. Erreur de prévision : meilleure méthode vs naïf
F = R['forecast']; atc = list(F)
naive = [F[c]['methods']['Naïf (mois précédent)']['mape'] for c in atc]
best = [F[c]['methods'][F[c]['best']]['mape'] for c in atc]
fig, ax = plt.subplots(figsize=(7, 3.2)); x = np.arange(len(atc))
ax.bar(x - 0.2, naive, 0.38, color=GRID, label='Prévision naïve (mois précédent)')
cols = [GREEN if F[c]['verdict'] == 'Oui' else (CORAL if F[c]['verdict'] == 'Non' else SAND) for c in atc]
ax.bar(x + 0.2, best, 0.38, color=cols, label='Meilleure méthode testée')
for i, v in enumerate(best): ax.text(i + 0.2, v + 0.8, f'{v:.0f}%', ha='center', fontsize=8, color=INK)
ax.set_xticks(x); ax.set_xticklabels(atc); ax.set_ylabel('Erreur moyenne (MAPE, %)')
ax.legend(frameon=False, fontsize=8, loc='upper left'); ax.grid(axis='y', color=GRID)
ax.set_title('Erreur de prévision M+1 sur 24 mois tenus à l\'écart (oct. 2017 – sept. 2019)', loc='left', fontsize=10, color=INK)
save(fig, 'g_prevision')

# 3. Profil horaire
hs = R['hour_share_total']; hrs = list(range(7, 23))
fig, ax = plt.subplots(figsize=(7, 3))
vals = [hs[str(h)] for h in hrs]
ax.bar(hrs, vals, color=[GREEN if v >= 8 else MINT for v in vals])
ax.set_xticks(hrs); ax.set_xticklabels([f'{h}h' for h in hrs], fontsize=8)
ax.set_ylabel('% du volume'); ax.grid(axis='y', color=GRID)
ax.set_title('Répartition des ventes par heure (tous groupes, 2014–2019)', loc='left', fontsize=10, color=INK)
save(fig, 'g_heures')

# 4. Grippe vs paracétamol
j = pd.read_csv(f'{OUT}/weekly_flu.csv', index_col=0, parse_dates=True)
fig, ax = plt.subplots(figsize=(7, 3)); ax2 = ax.twinx()
ax.plot(j.index, j['N02BE'], color=GREEN, lw=1.2, label='N02BE vendus / semaine')
ax2.fill_between(j.index, j['flu'], color=CORAL, alpha=.25, lw=0, label='Syndromes grippaux /100 000 hab.')
ax.set_ylabel('N02BE / semaine', color=GREEN); ax2.set_ylabel('Incidence grippe', color=CORAL)
ax2.spines['right'].set_visible(True); ax2.spines['top'].set_visible(False)
ax.set_title('Paracétamol (N02BE) et épidémies de grippe — Réseau Sentinelles', loc='left', fontsize=10, color=INK)
save(fig, 'g_grippe')

# 5. Granularité / risque
fig, ax = plt.subplots(figsize=(7, 2.6))
lv = ['Heure', 'Jour', 'Semaine', 'Mois']
v = [R['hourly_N05C_rows_le2'], R['daily_N05C_le2_pct'], R['weekly_N05C_le2_pct'], R['monthly_N05C_le2_pct']]
ax.barh(lv[::-1], v[::-1], color=[GREEN, SAND, CORAL, CORAL])
for i, x in enumerate(v[::-1]): ax.text(x + 1, i, f'{x:.0f} %', va='center', fontsize=9, color=INK)
ax.set_xlim(0, 100)
ax.set_xlabel('% des ventes non nulles de N05C portant sur 1 ou 2 unités')
ax.set_title('Plus la granularité est fine, plus une vente = une personne', loc='left', fontsize=10, color=INK)
save(fig, 'g_risque')
print('ok')
