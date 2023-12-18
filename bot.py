import csv
import datetime
import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
apiKey = os.getenv("NEWSAPI_KEY")

command_list = [
    "/start - start the bot",
    "/top_headlines - get the latest news headlines about a category, country or source",
    "/demo_top_headlines - get an example of how to use the /top_headlines command",
    "/country_codes - get the country codes you can use as parameters for the /top_headlines command",
    "/categories - get the categories you can use as parameters for the /top_headlines command",
    "/everything - get all the news articles related to a keyword",
    "/demo_everything - get an example of how to use the /everything command",
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The news bot is at your service!")


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
        "\nThis should return the 3 latest news articles about technology in the US from"
        + "BBC News. \nDo take note that the sources parameter cannot be used with the "
        + "country and category parameters."
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
        + f"to={today_date_str} sortBy=popularity n=3"
    )
    msg += demo_msg
    await update.message.reply_text(msg)


async def getCountryCodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = "countries.csv"
    countries = {}

    with open(file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        rows = list(csvreader)
        for row in rows[1:]:
            countries[row[1]] = row[0]

    msg = "".join([f"{key}: {value}\n" for key, value in countries.items()])
    await update.message.reply_text(
        "Here are the country codes you can use as parameters for the "
        + "/top_headlines command: \n"
        + msg
    )


async def getCategories(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "Here are the categories you can use as parameters for the "
        + "/top_headlines command: \n"
        + msg
    )


def splitArg(arg):
    return arg.split("=")


def getKey(arg):
    return splitArg(arg)[0]


def getValue(arg):
    return splitArg(arg)[1]


def updateNewsParameters(news_parameters, args):
    print(args)
    if args:
        for arg in args:
            key = getKey(arg)
            value = getValue(arg)
            if key != "n":
                news_parameters[key] = value
            else:
                news_parameters[key] = int(value)


def parametersCheck(news_parameters, correct_parameters, incorrect_parameters):
    for parameter in news_parameters:
        if parameter in incorrect_parameters or parameter not in correct_parameters:
            return [False, parameter]
    return [True, ""]


def isParametersCorrect(result):
    return result[0]


def constructApiEndpoint(
    endpoint, keyword, category, country, domains, sources, from_date, to_date, sortBy
):
    apiEndpointWithoutQuery = f"https://newsapi.org/v2/{endpoint}?"

    if keyword:
        apiEndpointWithoutQuery += f"q={keyword}&"
    if category:
        apiEndpointWithoutQuery += f"category={category}&"
    if country:
        apiEndpointWithoutQuery += f"country={country}&"
    if domains:
        apiEndpointWithoutQuery += f"domains={domains}&"
    if sources:
        apiEndpointWithoutQuery += f"sources={sources}&"
    if from_date:
        apiEndpointWithoutQuery += f"from={from_date}&"
    if to_date:
        apiEndpointWithoutQuery += f"to={to_date}&"
    if sortBy:
        apiEndpointWithoutQuery += f"sortBy={sortBy}&"

    apiEndpointWithoutQuery += f"apiKey={apiKey}"
    return apiEndpointWithoutQuery


async def handleData(update: Update, news_parameters, data):
    if data.get("status") == "ok":
        articles = data.get("articles")
        if articles:
            print(news_parameters["n"])
            for i in range(news_parameters["n"]):
                title = articles[i]["title"]
                url = articles[i]["url"]
                await update.message.reply_text(f"{title}\n\n{url}")

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
            "Sorry, something went wrong when trying to fetch the "
            + "latest news. Please try again later."
        )


async def getTopHeadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    updateNewsParameters(news_parameters, args)
    check = parametersCheck(news_parameters, correct_parameters, incorrect_parameters)
    isCorrectParameters = isParametersCorrect(check)

    if not isCorrectParameters:
        await update.message.reply_text(
            "Sorry, the /top_headlines command does not have a "
            + f"{check[1]} parameter. Please try again."
            ""
        )
        return

    apiEndpoint = constructApiEndpoint(
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

    res = requests.get(apiEndpoint)
    data = res.json()

    await handleData(update, news_parameters, data)


async def getEverything(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    updateNewsParameters(news_parameters, args)
    check = parametersCheck(news_parameters, correct_parameters, incorrect_parameters)
    isCorrectParameters = isParametersCorrect(check)

    if not isCorrectParameters:
        await update.message.reply_text(
            "Sorry, the /everything command does not have a "
            + f"{check[1]} parameter. Please try again."
        )
        return

    apiEndpoint = constructApiEndpoint(
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
    print(apiEndpoint)

    res = requests.get(apiEndpoint)
    data = res.json()
    print(data)

    await handleData(update, news_parameters, data)


if __name__ == "__main__":
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("top_headlines", getTopHeadlines))
    app.add_handler(CommandHandler("everything", getEverything))
    app.add_handler(CommandHandler("country_codes", getCountryCodes))
    app.add_handler(CommandHandler("categories", getCategories))
    app.add_handler(CommandHandler("demo_top_headlines", demo_top_headlines))
    app.add_handler(CommandHandler("demo_everything", demo_everything))
    app.run_polling(poll_interval=0.5)
