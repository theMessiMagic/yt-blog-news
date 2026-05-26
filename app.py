from flask import Flask, render_template, abort
import os
import json

app = Flask(__name__)

ARTICLES_DIR = "articles"


def load_articles():

    articles = []

    if not os.path.exists(ARTICLES_DIR):
        return []

    for file in os.listdir(ARTICLES_DIR):

        if file.endswith(".json"):

            path = os.path.join(
                ARTICLES_DIR,
                file
            )

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                article = json.load(f)

                article["id"] = file.replace(
                    ".json",
                    ""
                )

                articles.append(article)

    articles.sort(
        key=lambda x: x["created_at"],
        reverse=True
    )

    return articles


@app.route("/")
def home():

    articles = load_articles()

    return render_template(
        "index.html",
        articles=articles
    )


@app.route("/article/<article_id>")
def article(article_id):

    file_path = os.path.join(
        ARTICLES_DIR,
        f"{article_id}.json"
    )

    if not os.path.exists(file_path):
        abort(404)

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        article = json.load(f)

    return render_template(
        "article.html",
        article=article
    )


if __name__ == "__main__":
    app.run(debug=True)