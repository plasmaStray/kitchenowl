from sqlalchemy import event

from app import db
from app.models import Category, Household, Item


def test_get_all_items_loads_categories_without_n_plus_one_queries(
    user_client_with_household, household_id
):
    category = Category.create_by_name(household_id, "Vegetables")
    items = [
        Item(name=f"Catalog item {index}", household_id=household_id, category=category)
        for index in range(10)
    ]
    db.session.add_all(items)
    db.session.commit()

    category_queries = []

    def capture_category_query(
        connection, cursor, statement, parameters, context, executemany
    ):
        if "from category " in statement.lower():
            category_queries.append(statement)

    event.listen(db.engine, "before_cursor_execute", capture_category_query)
    try:
        response = user_client_with_household.get(f"/api/household/{household_id}/item")
    finally:
        event.remove(db.engine, "before_cursor_execute", capture_category_query)

    assert response.status_code == 200
    response_items = response.get_json()
    assert len(response_items) == len(items)
    response_by_id = {item["id"]: item for item in response_items}
    assert set(response_by_id) == {item.id for item in items}

    response_item = response_by_id[items[0].id]
    assert set(response_item) == set(Item.__table__.columns.keys()) | {"category"}
    assert set(response_item["category"]) == set(Category.__table__.columns.keys())
    assert response_item["category"]["id"] == category.id
    assert response_item["category"]["name"] == category.name
    assert len(category_queries) <= 1


def test_update_item_sets_and_removes_category_and_icon(
    user_client_with_household, household_id, item_id
):
    category = user_client_with_household.post(
        f'/api/household/{household_id}/category', json={'name': 'Vegetables'}
    ).get_json()

    res = user_client_with_household.post(
        f'/api/item/{item_id}',
        json={'icon': 'mushroom', 'category': {'id': category['id'], 'name': 'Vegetables'}},
    )
    assert res.status_code == 200
    assert res.get_json()['icon'] == 'mushroom'
    assert res.get_json()['category_id'] == category['id']

    res = user_client_with_household.post(
        f'/api/item/{item_id}', json={'icon': None, 'category': None}
    )
    assert res.status_code == 200
    assert res.get_json()['icon'] is None
    assert res.get_json()['category_id'] is None


def test_update_item_rejects_category_of_other_household(
    user_client_with_household, item_id
):
    other = Household(name='Other household').save()
    foreign = Category.create_by_name(other.id, 'Foreign')

    res = user_client_with_household.post(
        f'/api/item/{item_id}', json={'category': {'id': foreign.id}}
    )
    assert res.status_code == 400


def test_update_item_keeps_name_used_by_other_item(
    user_client_with_household, shoppinglist_id, item_id, item_name
):
    user_client_with_household.post(
        f'/api/shoppinglist/{shoppinglist_id}/add-item-by-name', json={'name': 'Bread'}
    )

    res = user_client_with_household.post(f'/api/item/{item_id}', json={'name': 'Bread'})
    assert res.status_code == 200
    assert res.get_json()['name'] == item_name
