import csv
import datetime
import os
import random
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
api_key = os.getenv("NEWSAPI_KEY")

command_list = [
    "/start - start the bot",
    "/top_headlines - get the latest news headlines about a category, country or source",
    "/demo_top_headlines - get an example of how to use the /top_headlines command",
    "/country_codes - get the country codes you can use as parameters for the /top_headlines command",
    "/categories - get the categories you can use as parameters for the /top_headlines command",
    "/everything - get all the news articles related to a keyword",
    "/demo_everything - get an example of how to use the /everything command",
    "/search - search for the latest news articles related to a keyword",
    "/random_headline - get a random news headline",
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The news bot is at your service!")


async def handle_invalid_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This command does not exist.")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "".join([f"{command}\n" for command in command_list])
    await update.message.reply_text("Here are the commands you can use:\n" + "\n" + msg)


async def demo_top_headlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parameters = ["category", "country", "sources", "n"]
    msg = (
        "To use the /top_headlines command, you can specify the following parameters:\n"
    )

    for parameter in parameters:
        msg += f"{parameter}\n"

    demo_msg = (
        "\nHere is an example of how you can use the /top_headlines command:\n"
        + "\n/top_headlines category=technology country=us n=3\n"
    )
    explanation = (
        "\nThis should return (up to) 3 latest top headlines about technology in the US from "
        + "the BBC.\n\nDo take note that the sources parameter cannot be used with the "
        + "country and category parameters. Feel free to use the /country_codes command to find out" 
        + " what code to use for the country parameter."
    )

    msg += demo_msg + explanation
    await update.message.reply_text(msg)


async def demo_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parameters = ["keyword", "domains", "from", "to", "sortBy", "n"]
    msg = "To use the /everything command, you can specify the following parameters:\n"
    now = datetime.datetime.now()
    today_date_str = now.strftime("%Y-%m-%d")
    month_before_today_date_str = (now - datetime.timedelta(days=30)).strftime(
        "%Y-%m-%d"
    )

    for parameter in parameters:
        msg += f"{parameter}\n"

    demo_msg = (
        "\nHere is an example of how you can use the /everything command:\n"
        + f"\n/everything keyword=bitcoin domains=wsj.com from={month_before_today_date_str} "
        + f"to={today_date_str} sortBy=popularity n=3\n"
    )
    explanation = (
        "\nThis should return (up to) 3 most popular news articles about Bitcoin from "
        + f"the Wall Street Journal from {month_before_today_date_str} to {today_date_str}."
    )

    msg += demo_msg + explanation
    await update.message.reply_text(msg)


async def get_country_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = "countries.csv"
    countries = {}

    with open(file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        rows = list(csvreader)
        for row in rows[1:]:
            countries[row[1]] = row[0]

    msg = "".join([f"{key}: {value}\n" for key, value in countries.items()])
    await update.message.reply_text(
        "Here are the country codes you can use as parameters for the /top_headlines command: \n"
        + "\n"
        + msg
    )


async def get_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = [
        "business",
        "entertainment",
        "general",
        "health",
        "science",
        "sports",
        "technology",
    ]
    msg = "".join([f"{category}\n" for category in categories])
    await update.message.reply_text(
        "Here are the categories you can use as parameters for the /top_headlines command: \n"
        + msg
    )


def split_arg(arg):
    return arg.split("=")


def get_key(arg):
    return split_arg(arg)[0]


def get_value(arg):
    return split_arg(arg)[1]


def update_news_parameters(news_parameters, args):
    if args:
        for arg in args:
            key = get_key(arg)
            value = get_value(arg)
            if key != "n":
                news_parameters[key] = value
            else:
                news_parameters[key] = int(value)


def check_parameters(news_parameters, correct_parameters, incorrect_parameters):
    for parameter in news_parameters:
        if parameter in incorrect_parameters or parameter not in correct_parameters:
            return [False, parameter]
    return [True, ""]


def is_parameters_correct(result):
    return result[0]


def construct_api_endpoint(
    endpoint, keyword, category, country, domains, sources, from_date, to_date, sortBy
):
    api_endpoint_without_query = f"https://newsapi.org/v2/{endpoint}?"
    api_endpoint = api_endpoint_without_query

    if keyword:
        api_endpoint += f"q={keyword}&"
    if category:
        api_endpoint += f"category={category}&"
    if country:
        api_endpoint += f"country={country}&"
    if domains:
        api_endpoint += f"domains={domains}&"
    if sources:
        api_endpoint += f"sources={sources}&"
    if from_date:
        api_endpoint += f"from={from_date}&"
    if to_date:
        api_endpoint += f"to={to_date}&"
    if sortBy:
        api_endpoint += f"sortBy={sortBy}&"

    api_endpoint += f"apiKey={api_key}&language=en"
    return api_endpoint


async def handle_data(update: Update, news_parameters, data):
    if data.get("status") == "ok":
        articles = data.get("articles")
        if articles:
            for i in range(news_parameters["n"]):
                if i >= len(articles):
                    break
                title = articles[i]["title"]
                url = articles[i]["url"]
                await update.message.reply_text(f"{title}\n\n{url}")
        else:
            await update.message.reply_text(
                "Sorry, I could not find any news articles that match your query."
            )

    else:
        too_far_back_error_msg = (
            "You are trying to request results too far in the past."
        )
        if too_far_back_error_msg in data.get("message"):
            await update.message.reply_text(
                "Unfortunately, I do not have access to news from so far back. Please use dates"
                + " within the past month."
            )
            return

        await update.message.reply_text(
            "Sorry, something went wrong when fetching the latest news. Please try again later."
        )


async def get_top_headlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    endpoint = "top-headlines"
    news_parameters = {"category": "", "country": "", "sources": "", "n": 1}

    correct_parameters = list(news_parameters.keys())

    incorrect_parameters = {
        "keyword": "",
        "domains": "",
        "from": "",
        "to": "",
        "sortBy": "",
    }

    args = context.args
    update_news_parameters(news_parameters, args)
    check = check_parameters(news_parameters, correct_parameters, incorrect_parameters)
    status = is_parameters_correct(check)

    if not status:
        await update.message.reply_text(
            "Sorry, the /top_headlines command does not have a "
            + f"{check[1]} parameter. Please try again."
            ""
        )
        return

    api_endpoint = construct_api_endpoint(
        endpoint,
        "",
        news_parameters["category"],
        news_parameters["country"],
        "",
        news_parameters["sources"],
        "",
        "",
        "",
    )

    res = requests.get(api_endpoint)
    data = res.json()
    await handle_data(update, news_parameters, data)


async def get_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    endpoint = "everything"
    news_parameters = {
        "keyword": "",
        "domains": "",
        "from": "",
        "to": "",
        "sortBy": "",
        "n": 1,
    }

    correct_parameters = list(news_parameters.keys())

    incorrect_parameters = {"category": "", "country": "", "sources": ""}

    args = context.args
    update_news_parameters(news_parameters, args)
    check = check_parameters(news_parameters, correct_parameters, incorrect_parameters)
    status = is_parameters_correct(check)

    if not status:
        await update.message.reply_text(
            "Sorry, the /everything command does not have a "
            + f"{check[1]} parameter. Please try again."
        )
        return

    api_endpoint = construct_api_endpoint(
        endpoint,
        news_parameters["keyword"],
        "",
        "",
        news_parameters["domains"],
        "",
        news_parameters["from"],
        news_parameters["to"],
        news_parameters["sortBy"],
    )

    res = requests.get(api_endpoint)
    data = res.json()
    await handle_data(update, news_parameters, data)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    endpoint = "everything"
    news_parameters = {
        "keyword": "",
        "domains": "",
        "from": "",
        "to": "",
        "sortBy": "",
        "n": 3,
    }

    keyword = context.args[0]
    news_parameters["keyword"] = keyword
    news_parameters["sortBy"] = "publishedAt"

    api_endpoint = construct_api_endpoint(
        endpoint,
        news_parameters["keyword"],
        "",
        "",
        "",
        "",
        "",
        "",
        news_parameters["sortBy"],
    )

    res = requests.get(api_endpoint)
    data = res.json()
    await handle_data(update, news_parameters, data)


async def get_random_headline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    endpoint = "top-headlines"
    api_endpoint_without_query = (
        f"https://newsapi.org/v2/{endpoint}?apiKey={api_key}&language=en"
    )

    res = requests.get(api_endpoint_without_query)
    data = res.json()

    if data.get("status") == "ok":
        articles = data.get("articles")
        if articles:
            random_article = random.choice(articles)
            title = random_article["title"]
            url = random_article["url"]
            await update.message.reply_text(f"{title}\n\n{url}")
    else:
        await update.message.reply_text(
            "Sorry, something went wrong when fetching a random headline. Please try again later."
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("top_headlines", get_top_headlines))
    app.add_handler(CommandHandler("everything", get_everything))
    app.add_handler(CommandHandler("country_codes", get_country_codes))
    app.add_handler(CommandHandler("categories", get_categories))
    app.add_handler(CommandHandler("demo_top_headlines", demo_top_headlines))
    app.add_handler(CommandHandler("demo_everything", demo_everything))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("random_headline", get_random_headline))

    app.add_handler(MessageHandler(filters.TEXT, handle_invalid_commands))
    app.add_handler(MessageHandler(~filters.COMMAND, handle_invalid_commands))
    app.run_polling(poll_interval=0.5)
