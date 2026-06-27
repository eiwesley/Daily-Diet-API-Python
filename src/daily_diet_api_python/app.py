import os
from datetime import datetime
from time import time

import bcrypt
from database import db
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_login import (
  LoginManager,
  current_user,
  login_required,
  login_user,
  logout_user,
)
from models.meal import Meal
from models.user import User

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)

with app.app_context():
  db.create_all()

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id: int):
  return User.query.get(user_id)


@app.route("/user", methods=["POST"])
def create_user():
  data = request.json
  username = data.get("username")
  password = data.get("password")

  if username and password:
    hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
    user = User(username=username, password=hashed_password, role="user")
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Usuário cadastrado com sucesso"}), 201

  return jsonify({"message": "Credenciais inválidas"}), 400


@app.route("/login", methods=["POST"])
def login():
  data = request.json
  username = data.get("username")
  password = data.get("password")

  if username and password:
    user = User.query.filter_by(username=username).first()

    if user and bcrypt.checkpw(str.encode(password), str.encode(user.password)):
      login_user(user)
      return jsonify({"message": "Autenticação realizada com sucesso"})

  return jsonify({"message": "Credenciais inválidas"}), 400


@app.route("/logout", methods=["POST"])
@login_required
def logout():
  logout_user()
  return jsonify({"message": "Logout realizado com sucesso!"})


@app.route("/user/<int:id_user>", methods=["GET"])
@login_required
def read_user(id_user: int):
  user = User.query.get(id_user)

  if user:
    return {"username": user.username}

  return jsonify({"message": "Usuário não encontrado"}), 404


@app.route("/user/<int:id_user>", methods=["PUT"])
@login_required
def update_user(id_user: int):
  user = User.query.get(id_user)
  data = request.json

  if id_user != current_user.id and current_user.role == "user":
    return jsonify({"message": "Operação não permitida"}), 403

  if user and data.get("password"):
    user.password = data.get("password")
    db.session.commit()

    return jsonify({"message": f"Usuário {id_user} alterado com sucesso"})

  return jsonify({"message": "Usuário não encontrado"}), 404


@app.route("/user/<int:id_user>", methods=["DELETE"])
@login_required
def delete_user(id_user: int):
  user = User.query.get(id_user)

  if current_user.role != "admin":
    return jsonify({"message": "Operação não permitida"}), 403

  if id_user == current_user.id:
    return jsonify({"message": "Deleção não permitida"}), 403

  if user:
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": f"Usuário {id_user} deletado com sucesso"})

  return jsonify({"message": "Usuário não encontrado"}), 404


@app.route("/meals", methods=["POST"])
@login_required
def create_meal():
  data = request.json or {}
  name = data.get("name")
  description = data.get("description")
  date_time = data.get("date_time")
  is_on_diet = data.get("is_on_diet")

  if not name or not description or is_on_diet is None:
    return jsonify(
      {
        "message": "Dados incompletos: name, description e is_on_diet são obrigatórios"
      }
    ), 400

  try:
    parsed_date_time = (
      datetime.fromisoformat(date_time) if date_time else datetime.utcnow()
    )
  except ValueError:
    return jsonify({"message": "date_time deve estar no formato ISO 8601"}), 400

  meal = Meal(
    user_id=current_user.id,
    name=name,
    description=description,
    date_time=parsed_date_time,
    is_on_diet=bool(is_on_diet),
  )

  db.session.add(meal)
  db.session.commit()

  return jsonify(meal.to_dict()), 201


@app.route("/users/<int:user_id>/meals", methods=["GET"])
@login_required
def list_user_meals(user_id: int):
  if current_user.role == "user" and current_user.id != user_id:
    return jsonify({"message": "Operação não permitida"}), 403

  user = User.query.get(user_id)

  if not user:
    return jsonify({"message": "Usuário não encontrado"}), 404

  meals = [meal.to_dict() for meal in user.meals.order_by(Meal.date_time).all()]

  return jsonify(meals)


@app.route("/meals/<int:meal_id>", methods=["GET"])
def read_meal(meal_id: int):
  meal = Meal.query.get(meal_id)

  if meal:
    return jsonify(meal.to_dict())

  return jsonify({"message": "Refeição não encontrada"}), 404


@app.route("/meals/<int:meal_id>", methods=["PUT"])
def update_meal(meal_id: int):
  meal = Meal.query.get(meal_id)
  data = request.json or {}

  if not meal:
    return jsonify({"message": "Refeição não encontrada"}), 404

  if current_user.role == "user" and meal.user_id != current_user.id:
    return jsonify({"message": "Operação não permitida"}), 403

  name = data.get("name")
  description = data.get("description")
  date_time = data.get("date_time")
  is_on_diet = data.get("is_on_diet")

  if not name or not description or is_on_diet is None:
    return jsonify(
      {
        "message": "Dados incompletos: name, description e is_on_diet são obrigatórios"
      }
    ), 400

  try:
    parsed_date_time = (
      datetime.fromisoformat(date_time) if date_time else meal.date_time
    )
  except ValueError:
    return jsonify({"message": "date_time deve estar no formato ISO 8601"}), 400

  meal.name = name
  meal.description = description
  meal.date_time = parsed_date_time
  meal.is_on_diet = bool(is_on_diet)

  db.session.commit()

  return jsonify(meal.to_dict())


@app.route("/meals/<int:meal_id>", methods=["DELETE"])
@login_required
def delete_meal(meal_id: int):
  meal = Meal.query.get(meal_id)

  if not meal:
    return jsonify({"message": "Refeição não encontrada"}), 404

  db.session.delete(meal)
  db.session.commit()

  return jsonify({"message": f"Refeição {meal_id} deletada com sucesso"})


@app.route("/health", methods=["GET"])
def health_check() -> dict[str, int | str]:
  return {"project": "python-api", "time": int(time())}


def run() -> None:
  app.run(debug=True, port=3333)  # noqa: S201


if __name__ == "__main__":
  run()
