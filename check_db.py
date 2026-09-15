import sqlite3

conn = sqlite3.connect('backend/db.sqlite3')
cur = conn.cursor()
cur.execute('''
SELECT p.ticker, p.status 
FROM portfolio_position p 
JOIN model_mgmt_strategyprofile s ON p.strategy_id = s.id 
WHERE s.name = 'Aggressive 6/3' AND p.entry_date = '2026-08-27'
''')
rows = cur.fetchall()
print(f'Total positions on Aug 27: {len(rows)}')
for r in rows:
    print(r)
