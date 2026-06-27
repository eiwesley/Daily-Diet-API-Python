from datetime import datetime

from database import db


class Meal(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
  name = db.Column(db.String(120), nullable=False)
  description = db.Column(db.Text, nullable=False)
  date_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  is_on_diet = db.Column(db.Boolean, nullable=False)

  user = db.relationship("User", backref=db.backref("meals", lazy="dynamic"))

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "user_id": self.user_id,
      "name": self.name,
      "description": self.description,
      "date_time": self.date_time.isoformat(),
      "is_on_diet": self.is_on_diet,
    }
