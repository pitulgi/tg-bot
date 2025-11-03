import aiomysql
import asyncio

mysql_config = {
    "host": "localhost",         # или твой хост MySQL
    "port": 3306,
    "user": "root",              # имя пользователя
    "password": "toropova",      # пароль
    "db": "plant_bot",
    "autocommit": True
}

# Создание пула соединений
async def get_pool():
    return await aiomysql.create_pool(**mysql_config)

# Добавить растение
async def add_plant(
    user_id: int,
    name: str,
    height: float = None,
    soil: str = None,
    light: str = None,
    watering_interval: int = None,
    last_watered: str = None,   # формат 'YYYY-MM-DD' или None
    notes: str = None,
):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        sql = """
            INSERT INTO plants (
                user_id, name, height, soil, light, watering_interval,
                last_watered, notes
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        await cur.execute(sql, (
            user_id, name, height, soil, light, watering_interval,
            last_watered, notes
        ))
    conn.close()

# Получить все растения пользователя
async def get_plants(pool, user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT name FROM plants WHERE user_id=%s", (user_id,)
            )
            rows = await cur.fetchall()
            return [row[0] for row in rows]

async def get_plants_by_user(user_id):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT id, name FROM plants WHERE user_id=%s", (user_id,))
        result = await cur.fetchall()
    conn.close()
    return result

async def get_plant_info(user_id, plant_name):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "SELECT * FROM plants WHERE user_id=%s AND name=%s", (user_id, plant_name)
        )
        plant = await cur.fetchone()
        notes = []
        if plant:
            await cur.execute(
                "SELECT id, date, note FROM plant_notes WHERE plant_id=%s ORDER BY date DESC", (plant['id'],)
            )
            notes = await cur.fetchall()
    conn.close()
    return plant, notes

async def delete_plant(user_id, name):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        await cur.execute(
            "DELETE FROM plants WHERE user_id=%s AND name=%s", (user_id, name)
        )
    conn.close()


async def add_plant_note(plant_id, date, note):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO plant_notes (plant_id, date, note) VALUES (%s, %s, %s)",
            (plant_id, date, note)
        )
    conn.close()

async def update_plant_info(plant_id, height=None, soil=None, light=None, watering_interval=None, last_watered=None, notes=None):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        # Собираем только непустые поля
        fields = []
        values = []
        if height is not None:
            fields.append('height=%s')
            values.append(height)
        if soil is not None:
            fields.append('soil=%s')
            values.append(soil)
        if light is not None:
            fields.append('light=%s')
            values.append(light)
        if watering_interval is not None:
            fields.append('watering_interval=%s')
            values.append(watering_interval)
        if last_watered is not None:
            fields.append('last_watered=%s')
            values.append(last_watered)
        if notes is not None:
            fields.append('notes=%s')
            values.append(notes)
        if not fields:
            conn.close()
            return  # ничего не надо обновлять
        sql = f"UPDATE plants SET {', '.join(fields)} WHERE id=%s"
        values.append(plant_id)
        await cur.execute(sql, tuple(values))
    conn.close()

async def enable_notify_for_user(user_id):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        await cur.execute("UPDATE plants SET notify_watering=1 WHERE user_id=%s", (user_id,))
    conn.close()

async def disable_notify_for_user(user_id):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        await cur.execute("UPDATE plants SET notify_watering=0 WHERE user_id=%s", (user_id,))
    conn.close()

async def enable_notify_for_plant(plant_id):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        await cur.execute("UPDATE plants SET notify_watering=1 WHERE id=%s", (plant_id,))
        await conn.commit()
    conn.close()

async def update_plant_note(note_id, new_text):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        await cur.execute("UPDATE plant_notes SET note=%s WHERE id=%s", (new_text, note_id))
        await conn.commit()
    conn.close()

async def update_plant_last_watered(plant_id, water_date):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor() as cur:
        await cur.execute("UPDATE plants SET last_watered=%s WHERE id=%s", (water_date, plant_id))
        await conn.commit()
    conn.close()

# --------------------
# Проверочная функция!
# --------------------
async def test_connection_and_structure():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Проверка подключения
                await cur.execute("SELECT 1;")
                result = await cur.fetchone()
                print("Подключение к базе успешно:", result)

                # Проверка существования таблицы
                await cur.execute("SHOW TABLES LIKE 'plants';")
                table_result = await cur.fetchone()
                if table_result:
                    print("Таблица 'plants' существует!")
                else:
                    print("Таблица 'plants' не найдена!")

                # Проверка существования таблицы
                await cur.execute("SHOW TABLES LIKE 'plant_events';")
                table_result = await cur.fetchone()
                if table_result:
                    print("Таблица 'plants_events' существует!")
                else:
                    print("Таблица 'plants_events' не найдена!")

        pool.close()
        await pool.wait_closed()
    except Exception as e:
        print("Ошибка:", e)

# ------------ Запуск теста ------------
if __name__ == "__main__":
    asyncio.run(test_connection_and_structure())
