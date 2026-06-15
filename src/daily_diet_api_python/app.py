import os
from time import time

from dotenv import load_dotenv
from flask import Flask

from src.daily_diet_api_python.database import db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

db.init_app(app)


@app.route("/health", methods=["GET"])
def health_check() -> dict[str, int | str]:
  return {"project": "python-api", "time": int(time())}


def run() -> None:
  app.run(debug=True, port=3333)  # noqa: S201


if __name__ == "__main__":
  run()
