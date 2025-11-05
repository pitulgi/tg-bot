from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes
from telegram.ext import MessageHandler, filters
from telegram.ext import CallbackQueryHandler
from db import mysql_config, add_plant, get_plants_by_user, get_plant_info, add_plant_note, delete_plant, update_plant_info, enable_notify_for_user, disable_notify_for_user, enable_notify_for_plant, update_plant_note, update_plant_last_watered
import aiomysql
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime

WEB_APP_URL = ''  # адрес из CloudPub
scheduler = AsyncIOScheduler()

async def on_startup(app):
    if not scheduler.running:
        scheduler.add_job(check_and_notify_watering, "interval", days=1, args=[app.bot])
        #scheduler.add_job(check_and_notify_watering, "cron", hour=9, minute=0, args=[app.bot])
        scheduler.start()

app = ApplicationBuilder()\
    .token('')\
    .post_init(on_startup)\
    .build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Info"), KeyboardButton("Каталог растений"), KeyboardButton("Дневник")], [KeyboardButton("Настройки уведомлений")]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True  # делает клавиатуру компактной
    )
    await update.message.reply_text("Выберите раздел:", reply_markup=reply_markup)


async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Info":
        try:
            with open("info.txt", "r", encoding="utf-8") as f:
                info = f.read()
            await update.message.reply_text(info)
        except Exception as e:
            await update.message.reply_text(f"Не удалось загрузить описание: {e}")
        return
    elif text == "Каталог растений":
        await catalog(update, context)
        return
    elif text == "Дневник":
        await diary(update, context)
        return  
    elif text == "Настройки уведомлений":
        await notifications_settings(update, context)
        return
    
    elif context.user_data.get('edit_info'):
        edit = context.user_data['edit_info']
        step = edit['step']
        value = update.message.text.strip()
        # Сохраняем новое значение если не пропущено
        if step == 'height':
            if value != ".":
                edit['updates']['height'] = float(value) if value else None
            edit['step'] = 'soil'
            await update.message.reply_text("⚙️ Введите новый тип почвы (или '.' чтобы пропустить):")
            return

        if step == 'soil':
            if value != ".":
                edit['updates']['soil'] = value if value else None
            edit['step'] = 'light'
            await update.message.reply_text("⚙️ Введите новую освещённость (или '.' чтобы пропустить):")
            return

        if step == 'light':
            if value != ".":
                edit['updates']['light'] = value if value else None
            edit['step'] = 'watering_interval'
            await update.message.reply_text("⚙️ Введите новый интервал полива (или '.' чтобы пропустить):")
            return

        if step == 'watering_interval':
            if value != ".":
                try:
                    edit['updates']['watering_interval'] = int(value)
                except ValueError:
                    edit['updates']['watering_interval'] = None
            edit['step'] = 'last_watered'
            await update.message.reply_text("⚙️ Введите новую дату последнего полива (ГГГГ-ММ-ДД, или '.' чтобы пропустить):")
            return

        if step == 'last_watered':
            if value != ".":
                edit['updates']['last_watered'] = value if value else None
            edit['step'] = 'notes'
            await update.message.reply_text("⚙️ Введите новые заметки (или '.' чтобы пропустить):")
            return

        if step == 'notes':
            if value != ".":
                edit['updates']['notes'] = value if value else None
            # Все шаги завершены — пора обновлять данные!
            try:
                await update_plant_info(
                    edit['plant_id'],
                    **edit['updates']
                )
                await update.message.reply_text("✅ Информация о растении успешно обновлена!")
            except Exception as e:
                await update.message.reply_text(f"Ошибка при обновлении: {e}")
            # Очистка режима редактирования
            context.user_data.pop('edit_info')
            context.user_data.pop('current_plant', None)
            return

    elif context.user_data.get('add_plant_step'):
        step = context.user_data['add_plant_step']
        data = context.user_data['add_plant_data']

        if step == 'name':
            data['name'] = text
            context.user_data['add_plant_step'] = 'height'
            await update.message.reply_text("📐 Введите высоту растения в см (чтобы пропустить отправьте '.'):")
            return

        if step == 'height':
            value = text.strip()
            if value == ".":
                data['height'] = None
            else:
                data['height'] = float(text) if text.strip() else None
            context.user_data['add_plant_step'] = 'soil'
            await update.message.reply_text("🪣 Введите тип почвы (чтобы пропустить отправьте '.'):")
            return

        if step == 'soil':
            value = text.strip()
            if value == ".":
                data['soil'] = None
            else:
                data['soil'] = text if text.strip() else None
            context.user_data['add_plant_step'] = 'light'
            await update.message.reply_text("☀️ Опишите освещённость (чтобы пропустить отправьте '.'):")
            return

        if step == 'light':
            value = text.strip()
            if value == ".":
                data['light'] = None
            else:
                data['light'] = text.strip() if text.strip() else None
            context.user_data['add_plant_step'] = 'watering_interval'
            await update.message.reply_text("⏳ Введите интервал полива в днях (чтобы пропустить отправьте '.'):")
            return
        
        if step == 'watering_interval':
            value = text.strip()
            if value == ".":
                data['watering_interval'] = None
            else:
                try:
                    data['watering_interval'] = int(text) if text.strip() else None
                except ValueError:
                    data['watering_interval'] = None
            context.user_data['add_plant_step'] = 'last_watered'
            await update.message.reply_text("📅 Когда вы последний раз поливали растение ГГГГ-ММ-ДД (чтобы пропустить отправьте '.'):")
            return

        if step == 'last_watered':
            value = text.strip()
            if value == ".":
                data['last_watered'] = None
            else:
                data['last_watered'] = text.strip() if text.strip() else None
            context.user_data['add_plant_step'] = 'notes'
            await update.message.reply_text("📌 Заметки (чтобы пропустить отправьте '.'):")
            return

        if step == 'notes':
            value = text.strip()
            if value == ".":
                data['notes'] = None
            else:
                data['notes'] = text.strip() if text.strip() else None

            user_id = update.effective_user.id
            try:
                await add_plant(
                    user_id=user_id,
                    name=data['name'],
                    height=data['height'],
                    soil=data['soil'],
                    light=data['light'],
                    watering_interval=data.get('watering_interval'),
                    last_watered=data.get('last_watered'),
                    notes=data.get('notes'),
                )

                # Получить ID только что добавленного растения (например, по user_id и name)
                plants = await get_plants_by_user(user_id)
                # ищем plant_id с нужным именем — предполагаем, что имя уникально (или можно расширить)
                plant = next(p for p in plants if p['name'] == data['name'])
                plant_id = plant['id']

                keyboard = [
                    [InlineKeyboardButton("Включить уведомления", callback_data=f'enable_notify_added_{plant_id}')]
                ]
                markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f'🌈 Растение "{data["name"]}" добавлено!',
                    reply_markup=markup
                )
            except Exception as e:
                await update.message.reply_text(f"Ошибка при добавлении: {e}")

            context.user_data.pop('add_plant_step')
            context.user_data.pop('add_plant_data')
            return
    
    if context.user_data.get('add_note_mode'):
        mode = context.user_data['add_note_mode']
        if mode == 'name':
            name = update.message.text.strip()
            if name not in context.user_data.get('plant_names', []):
                await update.message.reply_text("Такого растения не найдено. Введите корректное название.")
                return
            # Найти plant_id
            user_id = update.effective_user.id
            plants = await get_plants_by_user(user_id)
            plant_id = next(p['id'] for p in plants if p['name'] == name)
            context.user_data['note_plant_id'] = plant_id
            context.user_data['add_note_mode'] = 'date'
            await update.message.reply_text("📅 Введите дату записи (ГГГГ-ММ-ДД):")
            return

        if mode == 'date':
            date_text = update.message.text.strip()
            # Можно добавить простую валидацию по длине и формату
            context.user_data['note_date'] = date_text
            context.user_data['add_note_mode'] = 'note'
            await update.message.reply_text("🖋 Введите текст записи:")
            return

        if mode == 'note':
            note_text = update.message.text.strip()
            plant_id = context.user_data['note_plant_id']
            date = context.user_data['note_date']
            try:
                await add_plant_note(plant_id, date, note_text)
                await update.message.reply_text("✅ Запись добавлена!")
            except Exception as e:
                await update.message.reply_text(f"Ошибка при добавлении: {e}")
            # Сброс состояния
            context.user_data.pop('add_note_mode')
            context.user_data.pop('plant_names')
            context.user_data.pop('note_plant_id')
            context.user_data.pop('note_date')
            return
        
    elif context.user_data.get('delete_plant_mode'):
        name = update.message.text.strip()
        user_id = update.effective_user.id
        try:
            await delete_plant(user_id, name)
            await update.message.reply_text("✅ Растение удалено.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
        context.user_data.pop('delete_plant_mode')
        return

        
    elif context.user_data.get('choose_plant_mode'):
        name = update.message.text.strip()
        user_id = update.effective_user.id
        plant, notes = await get_plant_info(user_id, name)
        if not plant:
            await update.message.reply_text("Такого растения не найдено. Проверьте имя.")
        else:
            note_text = "Записи:\n" + "\n\n".join(
                f"🔸 {i+1}. {n['date']}: {n['note']}" for i, n in enumerate(notes)
            ) if notes else "Записей пока нет."
            keyboard = [
                [InlineKeyboardButton('⚙️ Редактировать', callback_data='edit_note')],
                [InlineKeyboardButton('⬅️ Назад', callback_data='my_notes')]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("\n\n" + note_text, reply_markup=markup)
            context.user_data['last_plant_name'] = name
        context.user_data.pop('choose_plant_mode')
        context
        return
    
    elif context.user_data.get('show_plant_mode'):
        name = update.message.text.strip()
        user_id = update.effective_user.id
        plant, _ = await get_plant_info(user_id, name)  # только info, без заметок
        if not plant:
            await update.message.reply_text("Такого растения не найдено. Проверьте имя.")
        else:
            info = (
                f"🪴 Название: {plant['name']}\n\n"
                f"📐 Высота: {plant['height'] or 'не указано'}\n\n"
                f"🪣 Почва: {plant['soil'] or 'не указано'}\n\n"
                f"☀️ Освещённость: {plant['light'] or 'не указано'}\n\n"
                f"⏳ Интервал полива: {plant['watering_interval'] or 'не указано'}\n\n"
                f"📅 Последний полив: {plant['last_watered'] or 'не указано'}\n\n"
                f"📌 Заметки: {plant['notes'] or 'нет'}\n"
            )
            keyboard = [
                [InlineKeyboardButton('⚙️ Редактировать информацию', callback_data='edit_info')],
                [InlineKeyboardButton('⬅️ Назад', callback_data='my_plants')]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(info, reply_markup=markup)
            context.user_data['current_plant'] = plant  # сохраняем данные для редактирования
        context.user_data.pop('show_plant_mode')
        context.user_data.pop('plant_names')
        return
    
    elif context.user_data.get('edit_note_mode'):
        mode = context.user_data['edit_note_mode']
        notes_list = context.user_data.get('edit_notes_list', [])
        if mode == 'choose':
            try:
                idx = int(update.message.text.strip()) - 1  # нумерация с 1 для юзера
            except ValueError:
                await update.message.reply_text("Пожалуйста, введите номер записи.")
                return
            if idx < 0 or idx >= len(notes_list):
                await update.message.reply_text("Номер вне диапазона. Попробуйте еще раз.")
                return
            context.user_data['edit_note_idx'] = idx
            context.user_data['edit_note_mode'] = 'text'
            await update.message.reply_text(f"⚙️ Введите новый текст для записи:\n({notes_list[idx]['date']}: {notes_list[idx]['note']})")
            return
        if mode == 'text':
            new_text = update.message.text.strip()
            idx = context.user_data['edit_note_idx']
            #print(f"notes_list = {notes_list}")
            #print(f"note = {note}")

            note = notes_list[idx]
            # Тут функция обновления записи в БД (реализуй у себя):
            try:
                await update_plant_note(note['id'], new_text)
                await update.message.reply_text("✅ Запись успешно обновлена!")
            except Exception as e:
                await update.message.reply_text(f"Ошибка: {e}")
            # Очистка режима
            context.user_data.pop('edit_note_mode')
            context.user_data.pop('edit_notes_list')
            context.user_data.pop('edit_note_idx')
            return


    else:
        await update.message.reply_text("Пожалуйста, выберите один из разделов на клавиатуре.")

async def inline_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'add_plant':
        context.user_data['add_plant_data'] = {}
        context.user_data['add_plant_step'] = 'name'
        await query.message.reply_text("🪴 Введите название растения:")  # Первый вопрос диалога
        return
    
    elif data == 'my_notes':
        user_id = update.effective_user.id
        plants = await get_plants_by_user(user_id)
        if not plants:
            await query.message.reply_text("У вас пока нет добавленных растений.")
            return
        context.user_data['plant_names'] = [p['name'] for p in plants]
        plant_list = "\n".join(f"🌱 {p['name']}" for p in plants)
        # Клавиатура с кнопкой "Добавить запись"
        keyboard = [
            [InlineKeyboardButton('📎 Добавить запись', callback_data='add_note')],
            [InlineKeyboardButton('⬅️ Назад', callback_data='back_1')]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            #f"Ваши растения:\n{plant_list}\n\n🔎 Напишите имя растения для просмотра записей.",
            f"\n🔎 Напишите имя растения для просмотра записей.",
            reply_markup=markup
        )
        context.user_data['choose_plant_mode'] = True
        return
    
    elif data == 'my_plants':
        user_id = update.effective_user.id
        plants = await get_plants_by_user(user_id)
        if not plants:
            await query.message.reply_text("У вас пока нет добавленных растений.")
            return
        context.user_data['plant_names'] = [p['name'] for p in plants]
        plant_list = "\n".join(f"🌱 {p['name']}" for p in plants)
        edit_keyboard = [
            [InlineKeyboardButton('⚙️Редактировать список', callback_data='edit_plants')],
            [InlineKeyboardButton('⬅️ Назад', callback_data='back_1')]
        ]
        edit_markup = InlineKeyboardMarkup(edit_keyboard)
        await query.message.reply_text(
            f"Ваши растения:\n{plant_list}\n\n🔎 Чтобы получить подробную информацию, введите название растения.", reply_markup=edit_markup
        )
        context.user_data['show_plant_mode'] = True
        return
    
    elif data == 'edit_plants':
        actions_keyboard = [
            [InlineKeyboardButton('🍃 Добавить растение', callback_data='add_plant')],
            [InlineKeyboardButton('🍂 Удалить растение', callback_data='del_plant')],
            [InlineKeyboardButton('⬅️ Назад', callback_data='my_plants')]
        ]
        actions_markup = InlineKeyboardMarkup(actions_keyboard)
        await query.message.reply_text(
            "Выберите действие со списком растений:",
            reply_markup=actions_markup
        )
        return
    
    elif data == 'add_note':
        user_id = update.effective_user.id
        plants = await get_plants_by_user(user_id)
        if not plants:
            await query.message.reply_text("У вас пока нет добавленных растений.")
            return
        # Сохраняем имена растений для проверки
        context.user_data['plant_names'] = [p['name'] for p in plants]
        await query.message.reply_text(
            "🌱 Напишите название растения, к которому хотите добавить запись:"
        )
        context.user_data['add_note_mode'] = 'name'
        return
    
    elif data == 'del_plant':
        context.user_data.pop('show_plant_mode', None)
        context.user_data.pop('choose_plant_mode', None)
        context.user_data.pop('add_note_mode', None)
        await query.message.reply_text("🌱 Введите название растения, которое хотите удалить:")
        context.user_data['delete_plant_mode'] = True
        return
    
    elif data == 'edit_info':
        plant = context.user_data.get('current_plant')
        if not plant:
            await query.message.reply_text("Ошибка: растение не выбрано.")
            return
        context.user_data['edit_info'] = {
            'plant_id': plant['id'],
            'name': plant['name'],  # фиксируем исходное имя
            'step': 'height',
            'updates': {}
        }
        await query.message.reply_text("⚙️ Введите новую высоту растения (или '.' чтобы пропустить):")
        return
    
    elif data == 'back_1':
        #вернуться в главное меню дневника
        await diary(update.callback_query, context)
        context.user_data.pop('show_plant_mode', None)
        context.user_data.pop('plant_names', None)
        return
    
    elif data == "enable_notify":
        # Здесь можно массово включить notify_watering для всех растений пользователя,
        # либо предложить выбрать для каждого
        user_id = update.effective_user.id
        await enable_notify_for_user(user_id)
        await query.message.reply_text("✅ Напоминания о поливе включены!")
        return

    elif data == "disable_notify":
        user_id = update.effective_user.id
        await disable_notify_for_user(user_id)
        await query.message.reply_text("❎ Напоминания о поливе отключены!")
        return
    
    elif data.startswith("enable_notify_added_"):
        plant_id = int(data.split("_")[-1])
        await enable_notify_for_plant(plant_id)   # Функция, которую нужно добавить
        await query.message.reply_text("✅ Уведомления о поливе для этого растения включены!")
        return
    
    elif data == 'edit_note':
        # Запросить номер записи (по порядку из notes)
        user_id = update.effective_user.id
        name = context.user_data.get('last_plant_name')  # добавь при выборе/вводе имени
        plant, notes = await get_plant_info(user_id, name)
        if not notes or len(notes) == 0:
            await query.message.reply_text("Нет записей для редактирования.")
            return
        context.user_data['edit_note_mode'] = 'choose'
        context.user_data['edit_notes_list'] = notes  # сохраняем список для выбора
        await query.message.reply_text(
            "⚙️ Введите номер записи, которую хотите изменить:"
        )
        return
    
    elif data.startswith("mark_watered_"):
        plant_id = int(data.split("_")[-1])
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')

        # Функция в твоём db.py:
        await update_plant_last_watered(plant_id, today)
        await query.message.reply_text("✅ Дата последнего полива обновлена!")
        return


    
async def notifications_settings(update, context):
    keyboard = [
        [InlineKeyboardButton("Включить напоминания", callback_data="enable_notify")],
        [InlineKeyboardButton("Отключить напоминания", callback_data="disable_notify")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ Настройки уведомлений по поливу:",
        reply_markup=markup
    )

async def check_and_notify_watering(bot):
    conn = await aiomysql.connect(**mysql_config)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("""
            SELECT * FROM plants WHERE notify_watering=1
        """)
        plants = await cur.fetchall()
        for plant in plants:
            # Определим, пора ли поливать
            last = plant['last_watered']
            period = plant['watering_interval']
            user_id = plant['user_id']
            name = plant['name']
            if not last or not period:
                continue

            if isinstance(last, str):
                last_dt = datetime.datetime.strptime(last, "%Y-%m-%d").date()
            else:
                last_dt = last

            next_date = last_dt + datetime.timedelta(days=period)
            today = datetime.date.today()
            if today >= next_date:
                try:
                    keyboard = [
                        [InlineKeyboardButton("Отметить полив", callback_data=f"mark_watered_{plant['id']}")]
                    ]
                    markup = InlineKeyboardMarkup(keyboard)
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🌱 Напоминание: растение '{name}' пора полить!",
                        reply_markup=markup
                    )
                except Exception:
                    pass
    conn.close()

async def diary(update, context):
    keyboard = [
        [InlineKeyboardButton('🪴 Мои растения', callback_data='my_plants')],
        [InlineKeyboardButton('📌 Мои записи', callback_data='my_notes')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите пункт:', reply_markup=reply_markup)

async def catalog(update, context):
    keyboard = [[InlineKeyboardButton('Открыть каталог', web_app=WebAppInfo(url=WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Нажмите, чтобы открыть:', reply_markup=reply_markup)

app = ApplicationBuilder().token('').post_init(on_startup).build()

app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters.TEXT, reply_handler))
app.add_handler(CommandHandler('catalog', catalog))
app.add_handler(CallbackQueryHandler(inline_callback_handler))


app.run_polling() 

