import datetime
import textwrap
import random
import math

import bs4
import requests
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler

RATING_LIST = {
    "s" : "Safe",
    "e" : "Explicit",
    "q" : "Questionable"
}


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    log = int(math.floor(math.log(size_bytes, 1024)))
    power = math.pow(1024, log)
    size = round(size_bytes / power, 2)
    return f"{size} {size_name[log]}"


@run_async
def search_e621(bot: Bot, update: Update):

    message = update.effective_message
    args = message.text.strip().split(" ", 1)

    try:
        search_query = args[1]
    except IndexError:
        update.effective_message.reply_text("Format : /e621 <tags>")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")
    search_query_args = search_query.split(",")
    e621_base_request_url = "https://e621.net/posts.json?tags="
    headers = {'User-Agent': 'Furry Saitama'}

    for each_search_query in search_query_args:
        each_search_query = each_search_query.strip().replace(" ", "_")
        e621_base_request_url += f"{each_search_query} "

    result = requests.get(e621_base_request_url, headers=headers).json()['posts']
    if result:
        item = random.choice(result)
        image = item['file']['url']

        artist_list = []
        for artist in item['tags']['artist']:
            artist_list.append(f'<a href="https://e621.net/posts?tags={artist}">{artist}</a>')

        artists = ', '.join([artist for artist in artist_list])
        species_list = ' #'.join([species for species in item['tags']['species']])

        species_list = "#" + species_list

        description = item['description'] or "Empty"
        post_id = item['id']

        source_list = []
        for index in range(len(item['sources'])):
            source_link = item['sources'][index]
            source_list.append(f'<a href="{source_link}">{index+1}</a>')

        sources = ', '.join([source for source in source_list])
        rating = RATING_LIST[item['rating']]
        score = item['score']['total']

        posted_time = item['created_at'].split(".", 1)[0]
        date_format = "%Y-%m-%dT%H:%M:%S"
        then = datetime.datetime.strptime(posted_time, date_format)
        now = datetime.datetime.now()
        duration = now - then
        duration_in_s = duration.total_seconds()
        days = duration.days

        if not days:
            hours = divmod(duration_in_s, 3600)[0]
            if hours:
                time_past = f"{hours} hours ago"
        else:
            if days > 365:
                years = divmod(days, 365)[0]
                time_past = f"{years} years ago"
            elif days > 30:
                months = divmod(days, 30)[0]
                time_past = f"{months} months ago"
            else:
                time_past = f"{days} days ago"

        if not days and not hours:
            minutes = divmod(duration_in_s, 60)[0]
            time_past = f"{minutes} minutes ago"

        approver_id = item["approver_id"]
        approver_page = requests.get(f"https://e621.net/users/{approver_id}", headers=headers).text
        soup = bs4.BeautifulSoup(approver_page, "html.parser")
        approver = soup.find("title").text.split("-")[1].strip()

        file_size = convert_size(item['file']['size'])
        size = f"{item['file']['width']}x{item['file']['height']} ({file_size})"

        flags = item['flags']
        if flags['pending']:
            status = "Pending"
            approver = "None"
        elif flags['flagged']:
            status = "Flagged"
        elif flags['note_locked']:
            status = "Note Locked"
        elif flags['status_locked']:
            status = "Status Locked"
        elif flags['rating_locked']:
            status = "Rating Locked"
        elif flags['deleted']:
            status = "Deleted"
        else:
            status = "Active"
        fav = item['fav_count']

        caption = textwrap.dedent(f"""
<b>Artists</b>: {artists}
<b>Species</b>: {species_list}
<b>Description</b>: <code>{description}</code>

<b>Information</b>
<b>ID</b>: <code>{post_id}</code>
<b>Source</b>: {sources}
<b>Rating</b>: {rating}
<b>Score</b>: {score}
<b>Posted</b>: {time_past}
<b>Approver</b>: {approver}
<b>Size</b>: <code>{size}</code>
<b>Status</b>: {status}
<b>Favorites</b>: {fav}
        """)

        buttons = [
            [
                InlineKeyboardButton("Download", url=image),
                InlineKeyboardButton("Visit Post on e621", url=f"https://e621.net/posts/{post_id}")
            ],
            [InlineKeyboardButton("Sets with this post", url=f"https://e621.net/post_sets?post_id={post_id}")],
            [InlineKeyboardButton("Visually similar on E6", url=f"https://e621.net/iqdb_queries?post_id={post_id}")],
        ]

        try:
            update.effective_message.reply_photo(photo=image, caption=caption, parse_mode=ParseMode.HTML,
                                                    reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
        except:
            update.effective_message.reply_text(image)
            update.effective_message.reply_text(caption, parse_mode=ParseMode.HTML,
                                                reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    else:
        update.effective_message.reply_text("No results found.")

    progress_message.delete()


__help__ = """
*Available commands:*

 - /e621 <tags> - finds random pic containing the given tags

 """

E621_HANDLER = DisableAbleCommandHandler("e621", search_e621)

dispatcher.add_handler(E621_HANDLER)

__mod_name__ = "E621"
__command_list__ = ["e621"]
__handlers__ = [E621_HANDLER]
