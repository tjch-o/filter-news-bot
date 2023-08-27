import os
import requests
import csv
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
apiKey = os.getenv("NEWSAPI_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The news bot is at your service!")
    
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_list = [
        "/start - start the bot",
        "/top_headlines - get the latest news headlines about a category, country or source",
        "/country_codes - get the country codes you can use as parameters for the /top_headlines command",
        "/categories - get the categories you can use as parameters for the /top_headlines command",
        "/everything - get all the news articles related to a keyword"
    ]
    
    msg = "".join([f"{command}\n" for command in command_list])
    await update.message.reply_text("Here are the commands you can use:\n" + "\n" + msg)
    
    
async def getCountryCodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = "countries.csv"
    countries = {}
    
    with open(file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        rows = list(csvreader)
        for row in rows[1:]:
            countries[row[1]] = row[0]
    
    msg = "".join(
        [f"{key}: {value}\n" for key, value in countries.items()]
    )
    await update.message.reply_text("Here are the country codes you can use as parameters for the " + 
                                    "/top_headline command: \n" + msg)
    
async def getCategories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    msg = "".join([f"{category}\n" for category in categories])
    await update.message.reply_text("Here are the categories you can use as parameters for the " + 
                                    "/top_headline command: \n" + msg)
     
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

def constructApiEndpoint(endpoint, keyword, category, country, domains, sources, from_date, to_date, sortBy):
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
        tooFarBack = "You are trying to request results too far in the past."
        if tooFarBack in data.get("message"):
            await update.message.reply_text("Sorry, we do not have access to news from so far back. " 
                                        + "Please try again.")
            return 
        
        await update.message.reply_text("Sorry, something went wrong when trying to fetch the " +
        "latest news. Please try again later.")

async def getTopHeadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    endpoint = "top-headlines"
    news_parameters = {
        "category": "",
        "country": "",
        "sources": "",
        "n": 1
    }
    
    correct_parameters = list(news_parameters.keys())
    
    incorrect_parameters = {
        "keyword": "",
        "domains": "",
        "from": "",
        "to": "",
        "sortBy": ""
    }
    
    args = context.args
    updateNewsParameters(news_parameters, args)
    check = parametersCheck(news_parameters, correct_parameters, incorrect_parameters)
    isCorrectParameters = isParametersCorrect(check)
    
    if not isCorrectParameters:
        await update.message.reply_text("Sorry, the top_headlines command does not have a " + 
                                        f"{check[1]} parameter. Please try again.""")
        return
    
    apiEndpoint = constructApiEndpoint(endpoint, "", news_parameters["category"], 
                news_parameters["country"], "", news_parameters["sources"], "", "", "")
    print(apiEndpoint)
    
    res = requests.get(apiEndpoint)
    data = res.json()
    print(data)
    
    await handleData(update, news_parameters, data)
    
async def getEverything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    endpoint = "everything"
    news_parameters = {
        "keyword": "",
        "domains": "", 
        "from": "",
        "to": "",
        "sortBy": "",
        "n": 1
    }
    
    correct_parameters = list(news_parameters.keys())
    
    incorrect_parameters = {
        "category": "",
        "country": "",
        "sources": ""
    }
    
    args = context.args
    updateNewsParameters(news_parameters, args)
    check = parametersCheck(news_parameters, correct_parameters, incorrect_parameters)
    isCorrectParameters = isParametersCorrect(check)
    
    if not isCorrectParameters:
        await update.message.reply_text("Sorry, the everything command does not have a " + 
        f"{check[1]} parameter. Please try again.")
        return
    
    apiEndpoint = constructApiEndpoint(endpoint, news_parameters["keyword"], "", 
                "", news_parameters["domains"], "", news_parameters["from"], news_parameters["to"], 
                news_parameters["sortBy"])
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
    app.run_polling(poll_interval=0.5)