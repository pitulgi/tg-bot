from flask import Flask
app = Flask(__name__)

from flask import Flask, render_template, request
import pandas as pd

# Загружаем данные из CSV
plants_df = pd.read_csv('plantsRU.csv')
print(plants_df.columns)

FIELD_LABELS = {
    'Growth': 'Рост',
    'Soil': 'Грунт',
    'Sunlight': 'Свет',
    'Watering': 'Полив',
    'Suggestions': 'Рекомендации по уходу',
}

@app.route('/')
def index():
    # Получаем поисковый запрос, если есть
    query = request.args.get('q', '').lower()
    if query:
        filtered = plants_df[plants_df['Plant_Name'].str.lower().str.contains(query)]
    else:
        filtered = plants_df
    # Передаем 30 растений на страницу для удобства
    return render_template('index.html', plants=filtered.head(94).to_dict(orient='records'), query=query)

@app.route('/plant/<plant_name>')
def plant_card(plant_name):
    row = plants_df[plants_df['Plant_Name'] == plant_name]
    if row.empty:
    # обработка отсутствия результата
        return 'Растение не найдено'
    row = row.iloc[0]
    return render_template(
    'plant_card.html',
    plant=row,
    field_labels=FIELD_LABELS
)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=7998)
