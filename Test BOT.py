import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import random

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем вопросы из файла
def load_questions(file_path):
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        i = 0
        while i < len(lines):
            question = lines[i].strip()
            answers = [lines[i+1].strip(), lines[i+2].strip(), lines[i+3].strip(), lines[i+4].strip()]
            correct_answer = int(lines[i+5].strip())
            questions.append((question, answers, correct_answer))
            i += 7  # Переходим к следующему вопросу (6 строк для вопросов и ответов + 1 строка для пустой строки)
    return questions

questions = load_questions('questions.md')
user_results = {}

# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Добро пожаловать в квиз! Напишите /quiz, чтобы начать.')

# Обработчик команды /quiz
async def quiz(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    context.user_data['score'] = 0
    context.user_data['current_question'] = 0
    context.user_data['questions'] = random.sample(questions, 10)
    await ask_question(update, context)

async def ask_question(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    current_question = context.user_data['current_question']
    question, answers, _ = context.user_data['questions'][current_question]

    keyboard = [[InlineKeyboardButton(answers[i], callback_data=str(i)) for i in range(4)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(question, reply_markup=reply_markup)

# Обработчик нажатия кнопок с вариантами ответов
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selected_answer = int(query.data)
    current_question = context.user_data['current_question']
    question, answers, correct_answer = context.user_data['questions'][current_question]

    if selected_answer == correct_answer:
        context.user_data['score'] += 1
        feedback = "Правильно!"
    else:
        feedback = "Неправильно!"

    context.user_data['current_question'] += 1

    if context.user_data['current_question'] < 10:
        await query.edit_message_text(text=f"{feedback} Следующий вопрос...")
        await ask_question(query, context)
    else:
        score = context.user_data['score']
        user_results[user_id] = score
        await query.edit_message_text(text=f"{feedback} Квиз завершен! Ваш результат: {score}/10")
        save_results()

# Сохраняем результаты в файл
def save_results():
    with open('results.txt', 'w') as f:
        for user_id, score in user_results.items():
            f.write(f"{user_id}:{score}\n")

# Обработчик команды /stats для отображения статистики
async def stats(update: Update, context: CallbackContext) -> None:
    stats_message = "Статистика игроков:\n"
    for user_id, score in user_results.items():
        stats_message += f"Пользователь {user_id}: {score}/10\n"
    await update.message.reply_text(stats_message)

def main() -> None:
    application = Application.builder().token("Токен Бота").build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("    ", stats))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()