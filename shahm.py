import os
import heroku3
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

ENTER_API_KEY = 1
ENTER_ENV_VARS = 2
DEPLOY_APP = 3
SEND_TXT_FILE = 4

user_env_vars = {}

TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
HEROKU_APP_NAME = 'YOUR_HEROKU_APP_NAME'

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحبًا! من فضلك أرسل مفتاح Heroku API الخاص بك.")
    return ENTER_API_KEY

def enter_api_key(update: Update, context: CallbackContext):
    api_key = update.message.text.strip()
    os.environ['HEROKU_API_KEY'] = api_key

    try:
        heroku_account = heroku.account_info()
        update.message.reply_text(f'تم قبول مفتاح Heroku API. سيتم الآن بدء عملية النشر.')

        github_url = 'https://github.com/lml10l/test/tarball/HuRe/'
        response = requests.get(github_url)
        if response.status_code == 200 and 'app.json' in response.text:
            update.message.reply_text(f'تم العثور على ملف app.json. جارٍ جلب متغيرات البيئة...')

            app_json_url = github_url.replace('/tarball/', '/tree/')
            app_json_response = requests.get(app_json_url + 'app.json')
            app_json_content = app_json_response.text

            try:
                app_json_data = json.loads(app_json_content)
                env_vars = app_json_data.get('env', {})
                for var_name, var_value in env_vars.items():
                    user_env_vars[var_name] = None

                env_var_names = "\n".join(user_env_vars.keys())
                update.message.reply_text(
                    f'المتغيرات المطلوبة:\n{env_var_names}\n\nمن فضلك أرسل قيم المتغيرات واحدة تلو الأخرى.'
                )
                return ENTER_ENV_VARS

            except Exception as e:
                update.message.reply_text(f'خطأ في تحليل ملف app.json: {str(e)}')

        else:
            update.message.reply_text('خطأ: لم يتم العثور على ملف app.json في الرابط المقدم.')

    except Exception as e:
        update.message.reply_text(f'خطأ في التحقق من مفتاح Heroku API أو بدء عملية النشر. من فضلك حاول مرة أخرى.')
        return ConversationHandler.END

def enter_env_vars(update: Update, context: CallbackContext):
    var_name = list(user_env_vars.keys())[0]
    user_env_vars[var_name] = update.message.text.strip()

    if user_env_vars[var_name]:
        user_env_vars.pop(var_name)

    if user_env_vars:
        var_name = list(user_env_vars.keys())[0]
        update.message.reply_text(
            f'تم تعبئة {var_name}. الرجاء إرسال القيمة التالية لـ {var_name}.'
        )
    else:
        update.message.reply_text('تم تعبئة جميع المتغيرات بنجاح. جارٍ بدء عملية النشر...')
        deploy_app(update.message.chat_id)
        return DEPLOY_APP

def deploy_app(chat_id):
    try:
        heroku_app = heroku.apps()[HEROKU_APP_NAME]
        heroku_app.get_builds().create(
            source_blob={'url': github_url},
            overrides={'buildpacks': [{'url': 'heroku/python'}]}
        )
        update.message.reply_text(f'تم بدء عملية النشر على Heroku لتطبيق {HEROKU_APP_NAME}.')
        update.message.reply_text(f'يرجى الانتظار حتى يتم نشر التطبيق بنجاح...')
    except Exception as e:
        update.message.reply_text(f'خطأ في بدء عملية النشر. من فضلك حاول مرة أخرى.')
        return ConversationHandler.END

def send_txt_file(update: Update, context: CallbackContext):
    txt_file_content = "تم نشر التطبيق بنجاح!"
    with open("deployed_app.txt", "w") as file:
        file.write(txt_file_content)

    update.message.reply_text("تم نشر التطبيق بنجاح. إليك ملف نصي:", reply_markup=ReplyKeyboardRemove())
    with open("deployed_app.txt", "rb") as file:
        update.message.bot.send_document(chat_id=update.message.chat_id, document=file)

    return ConversationHandler.END

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        ENTER_API_KEY: [MessageHandler(Filters.text & ~Filters.command, enter_api_key)],
        ENTER_ENV_VARS: [MessageHandler(Filters.text & ~Filters.command, enter_env_vars)],
        DEPLOY_APP: [MessageHandler(Filters.text & ~Filters.command, send_txt_file)],
    },
    fallbacks=[]
)

updater.dispatcher.add_handler(conversation_handler)

updater.start_polling()
updater.idle()