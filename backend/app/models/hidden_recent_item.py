from typing import TYPE_CHECKING, Self

from app import db

Model = db.Model
if TYPE_CHECKING:
    from app.helpers.db_model_base import DbModelBase

    Model = DbModelBase


class HiddenRecentItem(Model):
    __tablename__ = "shoppinglist_recent_item_hidden"

    shoppinglist_id = db.Column(
        db.Integer,
        db.ForeignKey("shoppinglist.id", ondelete="CASCADE"),
        primary_key=True,
    )
    item_id = db.Column(
        db.Integer,
        db.ForeignKey("item.id", ondelete="CASCADE"),
        primary_key=True,
    )

    shoppinglist = db.relationship(
        "Shoppinglist", back_populates="hidden_recent_items"
    )
    item = db.relationship("Item", back_populates="hidden_recent_items")

    @classmethod
    def find_by_ids(cls, shoppinglist_id: int, item_id: int) -> Self | None:
        return cls.query.filter_by(
            shoppinglist_id=shoppinglist_id, item_id=item_id
        ).first()
