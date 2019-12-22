import html
from typing import Optional, List

import telegram.ext as tg
from telegram import Message, Chat, Update, Bot, ParseMode, User, MessageEntity
from telegram import TelegramError
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html, mention_markdown

import haruka.modules.sql.blsticker_sql as sql
from haruka import dispatcher, SUDO_USERS, LOGGER, OWNER_ID
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.chat_status import can_delete, is_user_admin, user_not_admin, user_admin, \
		bot_can_delete, is_bot_admin
from haruka.modules.helper_funcs.filters import CustomFilters
from haruka.modules.helper_funcs.misc import split_message
from haruka.modules.warns import warn
from haruka.modules.log_channel import loggable
from haruka.modules.sql import users_sql
from haruka.modules.connection import connected

from haruka.modules.helper_funcs.alternate import send_message

from haruka.modules.translations.strings import tld


@run_async
def blackliststicker(bot: Bot, update: Update, args: List[str]):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
		
	conn = connected(bot, update, chat, user.id, need_admin=False)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if chat.type == "private":
			return
		else:
			chat_id = update.effective_chat.id
			chat_name = chat.title
		
	sticker_list = (tld(chat.id, "<b>Blacklist of stickers currently at {}:</b>\n").format(chat_name))

	all_stickerlist = sql.get_chat_stickers(chat_id)

	if len(args) > 0 and args[0].lower() == 'copy':
		for trigger in all_stickerlist:
			sticker_list += "<code>{}</code>\n".format(html.escape(trigger))
	elif len(args) == 0:
		for trigger in all_stickerlist:
			sticker_list += " - <code>{}</code>\n".format(html.escape(trigger))

	split_text = split_message(sticker_list)
	for text in split_text:
		if sticker_list == (tld(chat.id, "<b>Daftar hitam stiker saat saat ini di {}:</b>\n").format(chat_name).format(chat_name)):
			send_message(update.effective_message, (tld(chat.id, "No blblacklist sticker on <b>{}</b>!").format(chat_name)), parse_mode=ParseMode.HTML)
			return
	send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_blackliststicker(bot: Bot, update: Update):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	words = msg.text.split(None, 1)

	conn = connected(bot, update, chat, user.id)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		chat_id = update.effective_chat.id
		if chat.type == "private":
			return
		else:
			chat_name = chat.title

	if len(words) > 1:
		text = words[1].replace('https://t.me/addstickers/', '')
		to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
		added = 0
		for trigger in to_blacklist:
			try:
				get = bot.getStickerSet(trigger)
				sql.add_to_stickers(chat_id, trigger.lower())
				added += 1
			except BadRequest:
				send_message(update.effective_message, tl(update.effective_message, "Stiker `{}` tidak dapat di temukan!").format(trigger), parse_mode="markdown")

		if added == 0:
			return

		if len(to_blacklist) == 1:
			send_message(update.effective_message, tl(update.effective_message, "Stiker <code>{}</code> ditambahkan ke daftar hitam stiker di <b>{}</b>!").format(html.escape(to_blacklist[0]), chat_name),
				parse_mode=ParseMode.HTML)
		else:
			send_message(update.effective_message, tl(update.effective_message, "<code>{}</code> stiker ditambahkan ke daftar hitam stiker di <b>{}</b>!").format(added, chat_name), parse_mode=ParseMode.HTML)
	elif msg.reply_to_message:
		added = 0
		trigger = msg.reply_to_message.sticker.set_name
		if trigger == None:
			send_message(update.effective_message, tl(update.effective_message, "Stiker tidak valid!"))
			return
		try:
			get = bot.getStickerSet(trigger)
			sql.add_to_stickers(chat_id, trigger.lower())
			added += 1
		except BadRequest:
			send_message(update.effective_message, tl(update.effective_message, "Stiker `{}` tidak dapat di temukan!").format(trigger), parse_mode="markdown")

		if added == 0:
			return

		send_message(update.effective_message, tl(update.effective_message, "Stiker <code>{}</code> ditambahkan ke daftar hitam stiker di <b>{}</b>!").format(trigger, chat_name), parse_mode=ParseMode.HTML)
	else:
		send_message(update.effective_message, tl(update.effective_message, "Beri tahu saya stiker apa yang ingin Anda tambahkan ke daftar hitam stiker."))

@run_async
@user_admin
def unblackliststicker(bot: Bot, update: Update):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	words = msg.text.split(None, 1)

	conn = connected(bot, update, chat, user.id)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		chat_id = update.effective_chat.id
		if chat.type == "private":
			return
		else:
			chat_name = chat.title


	if len(words) > 1:
		text = words[1].replace('https://t.me/addstickers/', '')
		to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
		successful = 0
		for trigger in to_unblacklist:
			success = sql.rm_from_stickers(chat_id, trigger.lower())
			if success:
				successful += 1

		if len(to_unblacklist) == 1:
			if successful:
				send_message(update.effective_message, (tld(chat.id, "Stiker <code>{}</code> dihapus dari daftar hitam di <b>{}</b>!").format(html.escape(to_unblacklist[0]), chat_name),
							   parse_mode=ParseMode.HTML))
			else:
				send_message(update.effective_message, (tld(chat.id, "Ini tidak ada di daftar hitam stiker...!")))

		elif successful == len(to_unblacklist):
			send_message(update.effective_message, (tld(chat.id, "Stiker <code>{}</code> dihapus dari daftar hitam di <b>{}</b>!").format(
					successful, chat_name), parse_mode=ParseMode.HTML))

		elif not successful:
			send_message(update.effective_message, (tld(chat.id, "Tidak satu pun stiker ini ada, sehingga tidak dapat dihapus.").format(
					successful, len(to_unblacklist) - successful), parse_mode=ParseMode.HTML))

		else:
			send_message(update.effective_message, (tld(chat.id, 
				"Stiker <code>{}</code> dihapus dari daftar hitam. {} Tidak ada, "
				"jadi tidak dihapus.").format(successful, len(to_unblacklist) - successful),
				parse_mode=ParseMode.HTML))
	elif msg.reply_to_message:
		trigger = msg.reply_to_message.sticker.set_name
		if trigger == None:
			send_message(update.effective_message, (tld(chat.id, "Stiker tidak valid!")))
			return
		success = sql.rm_from_stickers(chat_id, trigger.lower())

		if success:
			send_message(update.effective_message, (tld(chat.id, "Stiker <code>{}</code> dihapus dari daftar hitam di <b>{}</b>!").format(trigger, chat_name),
							   parse_mode=ParseMode.HTML))
		else:
			send_message(update.effective_message, (tld(chat.id, "{} tidak ada di daftar hitam stiker...!").format(trigger)))
	else:
		send_message(update.effective_message, (tld(chat.id, "Beri tahu saya stiker apa yang ingin Anda tambahkan ke daftar hitam stiker.")))

@run_async
@loggable
@user_admin
def blacklist_mode(bot: Bot, update: Update, args: List[str]):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]

	conn = connected(bot, update, chat, user.id, need_admin=True)
	if conn:
		chat = dispatcher.bot.getChat(conn)
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if update.effective_message.chat.type == "private":
			send_message(update.effective_message, tl(update.effective_message, "Anda bisa lakukan command ini pada grup, bukan pada PM"))
			return ""
		chat = update.effective_chat
		chat_id = update.effective_chat.id
		chat_name = update.effective_message.chat.title

	if args:
		if args[0].lower() == 'off' or args[0].lower() == 'nothing' or args[0].lower() == 'no':
			settypeblacklist = tl(update.effective_message, 'di matikan')
			sql.set_blacklist_strength(chat_id, 0, "0")
		elif args[0].lower() == 'del' or args[0].lower() == 'delete':
			settypeblacklist = tl(update.effective_message, 'di biarkan, pesannya akan dihapus')
			sql.set_blacklist_strength(chat_id, 1, "0")
		elif args[0].lower() == 'warn':
			settypeblacklist = tl(update.effective_message, 'di peringati')
			sql.set_blacklist_strength(chat_id, 2, "0")
		elif args[0].lower() == 'mute':
			settypeblacklist = tl(update.effective_message, 'di bisukan')
			sql.set_blacklist_strength(chat_id, 3, "0")
		elif args[0].lower() == 'kick':
			settypeblacklist = tl(update.effective_message, 'di tendang')
			sql.set_blacklist_strength(chat_id, 4, "0")
		elif args[0].lower() == 'ban':
			settypeblacklist = tl(update.effective_message, 'di blokir')
			sql.set_blacklist_strength(chat_id, 5, "0")
		elif args[0].lower() == 'tban':
			if len(args) == 1:
				teks = (tld(chat.id, """Sepertinya Anda mencoba menetapkan nilai sementara untuk blacklist sticker, tetapi belum menentukan waktu; gunakan `/blstickermode tban <timevalue>`.

Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu."""))
				send_message(update.effective_message, teks, parse_mode="markdown")
				return
			settypeblacklist = (tld(chat.id, 'di blokir sementara selama {}').format(args[1]))
			sql.set_blacklist_strength(chat_id, 6, str(args[1]))
		elif args[0].lower() == 'tmute':
			if len(args) == 1:
				teks = (tld(chat.id, """Sepertinya Anda mencoba menetapkan nilai sementara untuk blacklist sticker, tetapi belum menentukan waktu; gunakan `/blstickermode tmute <timevalue>`.

Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu."""))
				send_message(update.effective_message, teks, parse_mode="markdown")
				return
			settypeblacklist = (tld(chat.id, 'di bisukan sementara selama {}').format(args[1]))
			sql.set_blacklist_strength(chat_id, 7, str(args[1]))
		else:
			send_message(update.effective_message, (tld(chat.id, "Saya hanya mengerti off/del/warn/ban/kick/mute/tban/tmute!")))
			return
		if conn:
			text = (tld(chat.id, "Mode blacklist sticker diubah, Pengguna akan `{}` pada *{}*!").format(settypeblacklist, chat_name))
		else:
			text = (tld(chat.id, "Mode blacklist sticker diubah, Pengguna akan `{}`!").format(settypeblacklist)
		send_message(update.effective_message, text, parse_mode="markdown"))
		return "<b>{}:</b>\n" \
				"<b>Admin:</b> {}\n" \
				"Changed sticker blacklist mode. Will {}.".format(html.escape(chat.title),
																			mention_html(user.id, user.first_name), settypeblacklist)
	else:
		getmode, getvalue = sql.get_blacklist_setting(chat.id)
		if getmode == 0:
			settypeblacklist = (tld(chat.id, "tidak aktif"))
		elif getmode == 1:
			settypeblacklist = (tld(chat.id, "hapus"))
		elif getmode == 2:
			settypeblacklist = (tld(chat.id, "warn"))
		elif getmode == 3:
			settypeblacklist = (tld(chat.id, "mute"))
		elif getmode == 4:
			settypeblacklist = (tld(chat.id, "kick"))
		elif getmode == 5:
			settypeblacklist = (tld(chat.id, "ban"))
		elif getmode == 6:
			settypeblacklist = (tld(chat.id, "banned sementara selama {}").format(getvalue))
		elif getmode == 7:
			settypeblacklist = (tld(chat.id, "mute sementara selama {}").format(getvalue))
		if conn:
			text = (tld(chat.id, "Mode blacklist sticker saat ini disetel ke *{}* pada *{}*.").format(settypeblacklist, chat_name))
		else:
			text = (tld(chat.id, "Mode blacklist saat ini disetel ke *{}*.").format(settypeblacklist)
		send_message(chat.id, text, parse_mode=ParseMode.MARKDOWN))
	return ""

@run_async
@user_not_admin
def del_blackliststicker(bot: Bot, update: Update):
	chat = update.effective_chat  # type: Optional[Chat]
	message = update.effective_message  # type: Optional[Message]
	user = update.effective_user
	to_match = message.sticker
	if not to_match:
		return

	getmode, value = sql.get_blacklist_setting(chat.id)

	chat_filters = sql.get_chat_stickers(chat.id)
	for trigger in chat_filters:
		if to_match.set_name.lower() == trigger.lower():
			try:
				if getmode == 0:
					return
				elif getmode == 1:
					message.delete()
				elif getmode == 2:
					message.delete()
					warn(update.effective_user, chat, tl(update.effective_message, "Menggunakan stiker '{}' yang ada di daftar hitam stiker").format(trigger), message, update.effective_user, conn=False)
					return
				elif getmode == 3:
					message.delete()
					bot.restrict_chat_member(chat.id, update.effective_user.id, can_send_messages=False)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} di bisukan karena menggunakan stiker '{}' yang ada di daftar hitam stiker").format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 4:
					message.delete()
					res = chat.unban_member(update.effective_user.id)
					if res:
						bot.sendMessage(chat.id, tl(update.effective_message, "{} di tendang karena menggunakan stiker '{}' yang ada di daftar hitam stiker").format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 5:
					message.delete()
					chat.kick_member(user.id)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} di blokir karena menggunakan stiker '{}' yang ada di daftar hitam stiker").format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 6:
					message.delete()
					bantime = extract_time(message, value)
					chat.kick_member(user.id, until_date=bantime)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} di blokir selama {} karena menggunakan stiker '{}' yang ada di daftar hitam stiker").format(mention_markdown(user.id, user.first_name), value, trigger), parse_mode="markdown")
					return
				elif getmode == 7:
					message.delete()
					mutetime = extract_time(message, value)
					bot.restrict_chat_member(chat.id, user.id, until_date=mutetime, can_send_messages=False)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} di bisukan selama {} karena menggunakan stiker '{}' yang ada di daftar hitam stiker").format(mention_markdown(user.id, user.first_name), value, trigger), parse_mode="markdown")
					return
			except BadRequest as excp:
				if excp.message == "Message to delete not found":
					pass
				else:
					LOGGER.exception("Error while deleting blacklist message.")
				break


def __import_data__(chat_id, data):
	# set chat blacklist
	blacklist = data.get('sticker_blacklist', {})
	for trigger in blacklist:
		sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
	sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
	blacklisted = sql.num_stickers_chat_filters(chat_id)
	return (tld(chat.id, "Ada `{}` daftar hitam stiker.").format(blacklisted))

def __stats__():
	return (tld(chat.id, "{} pemicu daftar hitam stiker, di seluruh {} obrolan.").format(sql.num_stickers_filters(),
															sql.num_stickers_filter_chats()))

__help__ = "blstickers_help"

__mod_name__ = "Sticker Blacklist"

BLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler("blsticker", blackliststicker, pass_args=True, admin_ok=True)
ADDBLACKLIST_STICKER_HANDLER = DisableAbleCommandHandler("addblsticker", add_blackliststicker)
UNBLACKLIST_STICKER_HANDLER = CommandHandler(["unblsticker", "rmblsticker"], unblackliststicker)
BLACKLISTMODE_HANDLER = CommandHandler("blstickermode", blacklist_mode, pass_args=True)
BLACKLIST_STICKER_DEL_HANDLER = MessageHandler(Filters.sticker & Filters.group, del_blackliststicker)

dispatcher.add_handler(BLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(ADDBLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(UNBLACKLIST_STICKER_HANDLER)
dispatcher.add_handler(BLACKLISTMODE_HANDLER)
dispatcher.add_handler(BLACKLIST_STICKER_DEL_HANDLER)