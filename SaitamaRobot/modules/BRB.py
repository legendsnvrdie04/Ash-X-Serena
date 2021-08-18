import random, html
import time
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import (DisableAbleCommandHandler,
                                          DisableAbleMessageHandler)
from SaitamaRobot.modules.sql import afk_sql as sql
from SaitamaRobot.modules.users import get_user_id
from telegram import MessageEntity, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters, MessageHandler, run_async

AFK_GROUP = 7
AFK_REPLY_GROUP = 8
afk_time = " "

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += " ".join(time_list)

    return ping_time


@run_async
def afk(update: Update, context: CallbackContext):
    global afk_time
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user

    if not user:  # ignore channels
        return

    if user.id in [777000, 1087968824]:
        return
    #afk_time = float(time.time()) 
    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nYour afk reason was shortened to 100 characters."
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_text("{} is now offline !! {}".format(
            fname, notice))
    except BadRequest:
        pass


@run_async
def no_longer_afk(update: Update, context: CallbackContext):
    global afk_time 
    user = update.effective_user
    message = update.effective_message
    msg_id = message.message_id
    if not user:  # ignore channels
        return
    #wht_time = get_readable_time((time.time() - afk_time))
    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  #dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = ['{} is here!! Yayy!!!', '{} is awake!! kek!!', '{} r u feeling good now? Meow!!' , 
                       'A huge meteor..... oh no thts {} !! ', '{}-kun pops outta nowhere, !!' , 
                       ' Intensity Intensifies as {} is here!!!',
                       '{}-kun i saw u were sleeping with a bot!!! kek!!!', 'unoo.... eto... {} KuN! i s here!!! meowww!!' 
                      ] 




            chosen_option = random.choice(options)
            update.effective_message.reply_text(chosen_option.format(firstname))
        except:
            print("Exception")
            return


@run_async
def reply_afk(update: Update, context: CallbackContext):
    global afk_time 
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    #wht_time = get_readable_time((time.time() - afk_time))
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION])

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset +
                                                   ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print("Error: Could not fetch userid {} for AFK module"
                          .format(user_id))
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    global afk_time 
    #wht_time = get_readable_time((time.time() - afk_time))
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)
        if not user.reason:
            if int(userc_id) == int(user_id):
                return
            res = "{} is Offline !!".format(fst_name)
            update.effective_message.reply_text(res, parse_mode = "html")
        else:
            if int(userc_id) == int(user_id):
                return
            res = "{} is Offline!\nReason: <code>{}</code>".format(html.escape(fst_name), html.escape(user.reason))
            update.effective_message.reply_text(res, parse_mode="html")


__help__ = """
 • `/afk <reason>`*:* mark yourself as AFK(away from keyboard) or Offline
 • `brb <reason>`*:* same as the afk command - but not a command.
When marked as AFK, any mentions will be replied to with a message to say you're not available!
"""

AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r"^(?i)brb(.*)$"), afk, friendly="afk")
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.group, reply_afk)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)

__mod_name__ = "BRB"
__command_list__ = ["afk"]
__handlers__ = [(AFK_HANDLER, AFK_GROUP), (AFK_REGEX_HANDLER, AFK_GROUP),
                (NO_AFK_HANDLER, AFK_GROUP),
                (AFK_REPLY_HANDLER, AFK_REPLY_GROUP)]
